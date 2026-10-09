"""Sensor platform for ISS Predicted Tracker."""
from __future__ import annotations

from homeassistant.components.sensor import (
    SensorEntity,
    SensorStateClass,
)
from homeassistant.const import DEGREE, UnitOfLength
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN

async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up ISS sensor entities via direct platform loading."""
    coordinator = hass.data[DOMAIN]["coordinator"]

    sensors = [
        ISSStatusSensor(coordinator),
        ISSAltitudeSensor(coordinator),
        ISSMaxPassDegreesSensor(coordinator),
    ]
    async_add_entities(sensors)

class ISSBaseSensor(CoordinatorEntity, SensorEntity):
    """Base class for ISS sensors."""

    def __init__(self, coordinator):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_has_entity_name = True
        self._attr_icon = "mdi:satellite-variant"

class ISSStatusSensor(ISSBaseSensor):
    """Representation of the main ISS mission status."""

    def __init__(self, coordinator):
        super().__init__(coordinator)
        self._attr_name = "ISS Status"
        self._attr_unique_id = "iss_predicted_status"

    @property
    def native_value(self):
        """Return the intuitive status state."""
        if self.coordinator.data:
            return self.coordinator.data.get("status", "In Orbit")
        return "Initializing"

    @property
    def extra_state_attributes(self):
        """Keep raw coordinates and telemetry in attributes."""
        data = self.coordinator.data
        if not data:
            return {}
        return {
            "latitude": data.get("latitude"),
            "longitude": data.get("longitude"),
            "next_pass_time": data.get("next_pass_time"),
            "next_pass_event": data.get("next_pass_event"),
            "source": "Local SGP4 Engine",
        }

class ISSAltitudeSensor(ISSBaseSensor):
    """Representation of the physical orbital altitude of the ISS."""

    def __init__(self, coordinator):
        super().__init__(coordinator)
        self._attr_name = "ISS Orbital Altitude"
        self._attr_unique_id = "iss_predicted_altitude"
        self._attr_native_unit_of_measurement = UnitOfLength.KILOMETERS
        self._attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def native_value(self):
        """Return physical altitude in km."""
        if self.coordinator.data:
            return self.coordinator.data.get("altitude_km")
        return None

class ISSMaxPassDegreesSensor(ISSBaseSensor):
    """Representation of the next pass peak sky elevation angle."""

    def __init__(self, coordinator):
        super().__init__(coordinator)
        self._attr_name = "ISS Next Pass Max Elevation"
        self._attr_unique_id = "iss_predicted_max_degrees"
        self._attr_native_unit_of_measurement = DEGREE
        self._attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def native_value(self):
        """Return max degrees above horizon."""
        if self.coordinator.data:
            # Must match the key returned by the coordinator dictionary!
            return self.coordinator.data.get("next_pass_max_degrees")
        return None
