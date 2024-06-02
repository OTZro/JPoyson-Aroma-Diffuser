import logging

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN

logger = logging.getLogger(__package__)


async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry, async_add_entities):
    device_manager = hass.data[DOMAIN].get(config_entry.entry_id)
    logger.info("Adding JPoyson Aroma Diffuser switch...")

    async_add_entities([JPoysonAromaDiffuserDeviceSwitch(device_manager)])


class JPoysonAromaDiffuserDeviceSwitch(SwitchEntity):
    def __init__(self, device_manager):
        self._device_manager = device_manager
        self._is_on = self._device_manager.power_status
        self._device_manager.set_power_status_callback(self._on_power_status_changed)

    @property
    def name(self):
        return "JPoyson Aroma Diffuser"

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self._device_manager.device_id)},
            "name": "JPoyson Aroma Diffuser",
            "manufacturer": "J Poyson",
        }

    @property
    def unique_id(self):
        return self._device_manager.device_id

    @property
    def is_on(self):
        return self._is_on

    async def async_turn_on(self, **kwargs):
        if not self._device_manager.connected:
            logger.info("Device is not connected.")
            is_success = await self._device_manager.try_reconnect()
            logger.info("is_success: %s", is_success)
            if not is_success:
                logger.info("Failed to reconnect to the device.")
                return

        await self._device_manager.turn_on_device()
        self._is_on = True
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs):
        if not self._device_manager.connected:
            logger.info("Device is not connected.")
            is_success = await self._device_manager.try_reconnect()
            if not is_success:
                logger.info("Failed to reconnect to the device.")
                return

        await self._device_manager.turn_off_device()
        self._is_on = False
        self.async_write_ha_state()

    def _on_power_status_changed(self, is_on):
        logger.info("Power status changed: %s", is_on)
        self._is_on = is_on
        self.async_write_ha_state()
