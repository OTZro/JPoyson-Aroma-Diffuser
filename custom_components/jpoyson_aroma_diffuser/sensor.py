import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import Entity

from .const import DOMAIN

logger = logging.getLogger(__package__)


async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry, async_add_entities):
    device_manager = hass.data[DOMAIN].get(config_entry.entry_id)
    logger.info("Adding JPoyson Aroma Diffuser sensors...")

    sensors = []
    for i in range(4):
        sensors.append(TimerSlotSensor(hass, device_manager, i))

    async_add_entities(sensors, True)


class TimerSlotSensor(Entity):
    def __init__(self, hass, device_manager, slot):
        self.hass = hass
        self._device_manager = device_manager
        self.slot = slot
        self._state = None

    @property
    def name(self):
        return f"Timer Slot {self.slot + 1}"

    @property
    def state(self):
        return self._state

    @property
    def device_state_attributes(self):
        return self._state

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self._device_manager.device_id)},
            "name": "JPoyson Aroma Diffuser",
            "manufacturer": "J Poyson",
        }

    @property
    def unique_id(self):
        return f"{self._device_manager.device_id}_slot_{self.slot}"

    async def async_update(self):
        self._state = self._device_manager.state_object_array[self.slot]
