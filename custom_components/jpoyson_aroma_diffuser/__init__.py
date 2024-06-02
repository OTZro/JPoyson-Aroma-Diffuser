from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType

from .const import DOMAIN, WORKING_TIME, PAUSE_TIME
from .device_manager import DeviceManager


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the JPoyson Aroma Diffuser component."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up JPoyson Aroma Diffuser from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    device_id = entry.data["device_id"]
    manager = DeviceManager(hass=hass, config_entry=entry)

    await manager.connect_device(device_id)
    hass.data[DOMAIN][entry.entry_id] = manager

    hass.async_create_task(
        hass.config_entries.async_forward_entry_setup(entry, "switch")
    )
    hass.async_create_task(
        hass.config_entries.async_forward_entry_setup(entry, "sensor")
    )

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a JPoyson Aroma Diffuser config entry."""
    await hass.config_entries.async_forward_entry_unload(entry, "switch")
    await hass.config_entries.async_forward_entry_unload(entry, "sensor")

    # Remove the manager from hass.data and handle disconnection
    manager = hass.data[DOMAIN].pop(entry.entry_id, None)
    if manager and manager.client:
        await manager.client.disconnect()

    return True
