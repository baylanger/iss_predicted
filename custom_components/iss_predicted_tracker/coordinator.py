"""Coordinator for ISS Predicted Tracker with local SGP4 tracking and overhead pass detection."""
from datetime import datetime, timezone, timedelta
import logging
import aiohttp

from skyfield.api import EarthSatellite, load, wgs84
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.core import HomeAssistant

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

CELESTRAK_TLE_URL = "https://celestrak.org/NORAD/elements/gp.php?CATNR=25544&FORMAT=tle"

class ISSDataUpdateCoordinator(DataUpdateCoordinator):
    """Data update coordinator for the ISS Predicted Tracker."""

    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=60),
        )
        self.ts = load.timescale()
        self.satellite = None
        self.last_tle_fetch = None

        # Grab Home Assistant's configured home location automatically
        self.home_observer = wgs84.latlon(
            latitude_degrees=self.hass.config.latitude,
            longitude_degrees=self.hass.config.longitude,
            elevation_m=self.hass.config.elevation
        )

    async def _async_update_data(self):
        """Fetch fresh TLE if needed, calculate position, and find next overhead pass."""
        try:
            now = datetime.now(timezone.utc)

            if self.satellite is None or self.last_tle_fetch is None or (now - self.last_tle_fetch).total_seconds() > 43200:
                success = await self._async_fetch_and_parse_tle()
                if not success and self.satellite is None:
                    if self.data:
                        _LOGGER.warning("CelesTrak fetch failed during startup, falling back to cached telemetry data.")
                        return self.data
                    raise UpdateFailed("Failed to download initial TLE data from CelesTrak.")

            # 1. Calculate current live position
            t = self.ts.from_datetime(now)
            geocentric = self.satellite.at(t)
            subpoint = wgs84.subpoint(geocentric)

            lat = float(subpoint.latitude.degrees)
            lon = float(subpoint.longitude.degrees)
            elevation = float(subpoint.elevation.km)

            # 2. Calculate next overhead pass relative to HA Home coordinates
            next_pass = self._calculate_next_pass(now)

            # 3. Determine a clean, intuitive state for the entity
            # e.g., if next pass is within the next 15 minutes, state = "Approaching", otherwise "In Orbit"
            state_val = "In Orbit"
            if next_pass.get("time"):
                pass_dt = datetime.fromisoformat(next_pass["time"])
                time_to_pass = (pass_dt - now).total_seconds()
                if 0 <= time_to_pass <= 900:  # Within 15 minutes
                    state_val = f"Approaching ({next_pass.get('event', 'Pass')})"
                elif -300 <= time_to_pass < 0:  # During the pass (5 min window)
                    state_val = "Overhead Now!"

            return {
                "latitude": lat,
                "longitude": lon,
                "altitude_km": elevation,
                "timestamp": now,
                "status": state_val, # Used for entity state
                "next_pass_time": next_pass.get("time"),
                "next_pass_event": next_pass.get("event"),
                "next_pass_max_degrees": next_pass.get("max_alt")  # Clean and explicit mapping
            }

        except Exception as err:
            _LOGGER.warning("Orbital calculation warning (%s).", err)

            # If CelesTrak gives a 500 error or network drops, but we already have data in memory,
            # keep using the last known good telemetry instead of dropping sensors to unavailable.
            if self.data:
                _LOGGER.info("Using last known good ISS telemetry data due to temporary network/CelesTrak issue.")
                return self.data

            raise UpdateFailed(f"Orbital calculation failed: {err}")

    def _calculate_next_pass(self, now: datetime):
        """Find the next upcoming pass over HA Home location using Skyfield events."""
        try:
            t0 = self.ts.from_datetime(now)
            # Search ahead 48 hours to ensure we catch a full sequence
            t1 = self.ts.from_datetime(now + timedelta(hours=48))

            times, events = self.satellite.find_events(self.home_observer, t0, t1, altitude_degrees=10.0)

            event_names = ["Rise (Above 10°)", "Culmination (Highest Point)", "Set"]

            for i, (ti, event) in enumerate(zip(times, events)):
                event_time = ti.utc_datetime()

                # We want the next upcoming event to be a Rise, OR if we are currently mid-pass,
                # catch the upcoming Culmination/Set. But to keep it clean, let's find the next Rise
                # or fallback to the absolute next chronological future event.
                if event_time > now:
                    # If the next event is a Culmination or Set, let's find its max altitude directly
                    max_alt = None

                    # If this event is already a Culmination, compute its alt directly
                    if event == 1:
                        difference = self.satellite - self.home_observer
                        topocentric = difference.at(ti)
                        alt, _, _ = topocentric.altaz()
                        max_alt = round(alt.degrees, 1)
                    else:
                        # Otherwise look ahead in this sequence for the Culmination (1)
                        for future_ti, future_event in zip(times[i:], events[i:]):
                            if future_event == 1:  # Culmination
                                difference = self.satellite - self.home_observer
                                topocentric = difference.at(future_ti)
                                alt, _, _ = topocentric.altaz()
                                max_alt = round(alt.degrees, 1)
                                break
                            elif future_event == 2:  # Set
                                break

                    return {
                        "time": event_time.isoformat(),
                        "event": event_names[event],
                        "max_alt": max_alt
                    }
        except Exception as err:
            _LOGGER.debug("Could not compute next pass: %s", err)

        return {"time": None, "event": "Unknown", "max_alt": None}

    async def _async_fetch_and_parse_tle(self) -> bool:
        """Download and validate latest TLE lines from CelesTrak."""
        try:
            headers = {"User-Agent": "HomeAssistant-ISSPredictedTracker/1.0"}

            async with aiohttp.ClientSession() as session:
                async with session.get(CELESTRAK_TLE_URL, headers=headers, timeout=15) as response:
                    if response.status != 200:
                        _LOGGER.error("Failed to fetch TLE, HTTP status: %s", response.status)
                        return False

                    text = await response.text()
                    lines = [line.strip() for line in text.splitlines() if line.strip()]

                    line1 = None
                    line2 = None
                    name = "ISS (ZARYA)"

                    for line in lines:
                        if line.startswith("1 25544"):
                            line1 = line
                        elif line.startswith("2 25544"):
                            line2 = line
                        elif not line.startswith("1 ") and not line.startswith("2 ") and len(line) > 3 and "---" not in line:
                            name = line

                    if not line1 or not line2:
                        _LOGGER.error("Invalid TLE response from CelesTrak.")
                        return False

                    self.satellite = EarthSatellite(line1, line2, name, self.ts)
                    self.last_tle_fetch = datetime.now(timezone.utc)
                    return True

        except Exception as err:
            _LOGGER.error("Exception occurred while fetching TLE: %s", err)
            return False
