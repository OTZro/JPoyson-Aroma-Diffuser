import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback

from .const import DOMAIN, DEVICE_ID

# Define the configuration schema
DATA_SCHEMA = vol.Schema({
    vol.Required("device_id"): str,
})


class JPoysonAromaDiffuserConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            device_id = user_input.get("device_id")

            # Validate the device ID (you can add more validation if needed)
            if not device_id:
                errors["base"] = "invalid_device_id"
            else:
                await self.async_set_unique_id(device_id)
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title=f"JPoyson Aroma Diffuser ({device_id})",
                    data={DEVICE_ID: device_id}
                )

        return self.async_show_form(
            step_id="user",
            data_schema=DATA_SCHEMA,
            errors=errors
        )
