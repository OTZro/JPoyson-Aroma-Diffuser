import logging

import voluptuous as vol
from bleak import BleakScanner
from homeassistant import config_entries
from homeassistant.helpers import selector
from homeassistant.helpers.selector import SelectOptionDict

from .const import DOMAIN, DEVICE_ID

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
                await self.async_set_unique_id(device_id)
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title=f"JPoyson Aroma Diffuser ({device_id or manual_device_id})",
                    data={DEVICE_ID: device_id or manual_device_id}
                )

        # Discover available devices
        logger.warning("Calling async_step_user...")
        devices = await self._async_discover_devices()
        logger.warning("Discovered devices: %s", devices)

        if not devices:
            logger.warning("No BLE devices found.")
            return self.async_abort(reason="no_devices_found")

        # Extract device IDs and names from the list of devices
        device_options: list[SelectOptionDict] = [
            SelectOptionDict(label=device["name"], value=device["address"]) for device in devices
        ]
        logger.warning("Device options: %s", device_options)

        # Show form with device selection dropdown
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Optional("manual_device_id"): str,
                vol.Optional("device_id"): selector.SelectSelector(
                    selector.SelectSelectorConfig(options=device_options),
                ),
            }),
            errors=errors
        )

    async def _async_discover_devices(self):
        """Discover BLE devices."""
        logger.warning("Discovering BLE devices...")
        try:
            # Use BleakScanner to discover BLE devices
            devices = await BleakScanner.discover()
            logger.warning("Discovered %d BLE devices", len(devices))
            return [{"name": device.name, "address": device.address} for device in devices]
        except Exception as e:
            logger.error("Error discovering BLE devices: %s", e)
            return []
