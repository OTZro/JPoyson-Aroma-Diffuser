import logging

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN

logger = logging.getLogger(__package__)


async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry, async_add_entities):
    device_manager = hass.data[DOMAIN].pop(config_entry.entry_id)
    logger.warning("Adding JPoyson Aroma Diffuser switch...")

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
        if not self._device_manager.connected:
            logger.warning("Device is not connected.")
            is_success = await self._device_manager.try_reconnect()
            logger.warning("is_success: %s", is_success)
            if not is_success:
                logger.warning("Failed to reconnect to the device.")
                return

        await self._device_manager.turn_on_device()
        self._is_on = True
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs):
        if not self._device_manager.connected:
            logger.warning("Device is not connected.")
            is_success = await self._device_manager.try_reconnect()
            if not is_success:
                logger.warning("Failed to reconnect to the device.")
                return

        await self._device_manager.turn_off_device()
        self._is_on = False
        self.async_write_ha_state()
