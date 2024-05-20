from homeassistant.core import HomeAssistant

from .const import DOMAIN


async def async_setup_entry(hass: HomeAssistant, entry) -> bool:
    hass.data.setdefault(DOMAIN, {})

    hass.async_create_task(
        hass.config_entries.async_forward_entry_setup(entry, "switch")
    )

    return True


async def async_unload_entry(hass: HomeAssistant, entry) -> bool:
    await hass.config_entries.async_forward_entry_unload(entry, "switch")
    return True
