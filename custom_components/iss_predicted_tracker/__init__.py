"""The ISS Predicted Tracker integration."""
from __future__ import annotations

import voluptuous as vol

from homeassistant.core import HomeAssistant
from homeassistant.helpers import discovery
from homeassistant.helpers.typing import ConfigType

from .const import DOMAIN
from .coordinator import ISSDataUpdateCoordinator

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema({})
    },
    extra=vol.ALLOW_EXTRA,
)

async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the ISS Predicted Tracker component directly from YAML."""
    hass.data.setdefault(DOMAIN, {})

    # Initialize the coordinator using async_refresh for direct YAML setup
    coordinator = ISSDataUpdateCoordinator(hass)
    await coordinator.async_refresh()
    hass.data[DOMAIN]["coordinator"] = coordinator

    # Forward/load the sensor platform via discovery helper
    hass.async_create_task(
        discovery.async_load_platform(hass, "sensor", DOMAIN, {}, config)
    )

    return True
