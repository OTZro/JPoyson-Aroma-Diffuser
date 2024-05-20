from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import config_validation as cv
import voluptuous as vol
from bleak import BleakScanner

from .const import DOMAIN, DEVICE_ID


class MyBluetoothDeviceConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title="My Bluetooth Device", data=user_input)

        devices = await BleakScanner.discover()
        device_options = {device.address: f"{device.name} ({device.address})" for device in devices}

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(DEVICE_ID): vol.In(device_options),
            })
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return OptionsFlowHandler(config_entry)


class OptionsFlowHandler(config_entries.OptionsFlow):
    def __init__(self, config_entry):
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({}),
        )
