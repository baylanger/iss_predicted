"""Config flow for ISS Predicted Tracker integration."""
from __future__ import annotations

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult

from .const import DOMAIN

class ISSConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for ISS Predicted Tracker."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, any] | None = None
    ) -> FlowResult:
        """Handle the initial step when user adds the integration from the UI."""
        if user_input is not None:
            # Prevent duplicate entries (only allow tracking the ISS once)
            await self.async_set_unique_id("iss_predicted_tracker_global")
            self._abort_if_unique_id_configured()

            return self.async_create_entry(
                title="ISS Predicted Tracker",
                data=user_input
            )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({}),
        )
