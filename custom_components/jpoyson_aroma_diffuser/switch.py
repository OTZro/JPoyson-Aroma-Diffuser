from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DEVICE_ID
from .device_manager import DeviceManager


async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry, async_add_entities):
    device_id = config_entry.data[DEVICE_ID]
    device_manager = DeviceManager()
    await device_manager.connect_device(device_id)

    async_add_entities([JPoysonAromaDiffuserDeviceSwitch(device_manager)])


class JPoysonAromaDiffuserDeviceSwitch(SwitchEntity):
    def __init__(self, device_manager):
        self._device_manager = device_manager
        self._is_on = False

    @property
    def name(self):
        return "JPoyson Aroma Diffuser"

    @property
    def is_on(self):
        return self._is_on

    async def async_turn_on(self, **kwargs):
        await self._device_manager.turn_on_device()
        self._is_on = True
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs):
        await self._device_manager.turn_off_device()
        self._is_on = False
        self.async_write_ha_state()
