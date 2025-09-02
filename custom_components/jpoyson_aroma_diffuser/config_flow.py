import logging

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.components import bluetooth
from homeassistant.core import callback
from homeassistant.helpers import selector
from homeassistant.helpers.selector import SelectOptionDict

from .const import DOMAIN, DEVICE_ID, WORKING_TIME, PAUSE_TIME

logger = logging.getLogger(__package__)


class JPoysonAromaDiffuserConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            device_id = user_input.get("device_id")
            manual_device_id = user_input.get("manual_device_id")

            # Validate the device ID (you can add more validation if needed)
            if not device_id and not manual_device_id:
                errors["base"] = "invalid_device_id"
            else:
                await self.async_set_unique_id(device_id or manual_device_id)
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title=f"JPoyson Aroma Diffuser ({device_id or manual_device_id})",
                    data={
                        DEVICE_ID: device_id or manual_device_id,
                        WORKING_TIME: user_input.get(WORKING_TIME, 15),
                        PAUSE_TIME: user_input.get(PAUSE_TIME, 180),
                    }
                )

        # Discover available devices
        logger.debug("Calling async_step_user...")
        devices = await self._async_discover_devices()
        logger.debug("Discovered devices: %s", devices)

        if not devices:
            logger.debug("No BLE devices found.")
            return self.async_abort(reason="no_devices_found")

        # Extract device IDs and names from the list of devices
        device_options: list[SelectOptionDict] = [
            SelectOptionDict(label=device["name"], value=device["address"]) for device in devices
        ]
        logger.debug("Device options: %s", device_options)

        # Show form with device selection dropdown and initial working/pause time settings
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Optional("manual_device_id"): str,
                vol.Optional("device_id"): selector.SelectSelector(
                    selector.SelectSelectorConfig(options=device_options),
                ),
                vol.Optional(WORKING_TIME, default=15): int,
                vol.Optional(PAUSE_TIME, default=180): int,
            }),
            errors=errors
        )

    async def _async_discover_devices(self):
        """Discover BLE devices using Home Assistant's bluetooth integration."""
        logger.debug("Discovering BLE devices...")
        try:
            # Use Home Assistant's bluetooth scanner for better reliability
            scanner = bluetooth.async_get_scanner(self.hass)
            discovered_devices = await scanner.discover(timeout=10.0)
            logger.debug("Discovered %d BLE devices", len(discovered_devices))
            
            # Filter and format devices
            devices = []
            for device in discovered_devices:
                if device.name:  # Only include devices with names
                    devices.append({
                        "name": device.name,
                        "address": device.address
                    })
            
            return devices
        except Exception as e:
            logger.error("Error discovering BLE devices: %s", e)
            return []

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return JPoysonAromaDiffuserOptionsFlowHandler()


class JPoysonAromaDiffuserOptionsFlowHandler(config_entries.OptionsFlow):
    async def async_step_init(self, user_input=None):
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(
                title="",
                data={
                    WORKING_TIME: user_input.get(WORKING_TIME, 15),
                    PAUSE_TIME: user_input.get(PAUSE_TIME, 180),
                }
            )

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({
                vol.Optional(WORKING_TIME, default=self.config_entry.options.get(WORKING_TIME, 15)): int,
                vol.Optional(PAUSE_TIME, default=self.config_entry.options.get(PAUSE_TIME, 180)): int,
            })
        )
