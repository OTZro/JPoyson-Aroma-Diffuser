import logging
from typing import Any

import voluptuous as vol
from bleak import BleakScanner, BleakError
from habluetooth import BluetoothScanningMode
from habluetooth.scanner import create_bleak_scanner
from homeassistant import config_entries
from homeassistant.components.bluetooth import (
    async_get_scanner,
)
from homeassistant.const import CONF_NAME, CONF_MAC
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import device_registry

from .const import DOMAIN, DEVICE_ID, CONF_ENTRY_METHOD, CONF_ENTRY_MANUAL, CONF_ENTRY_SCAN

logger = logging.getLogger(__package__)


async def discover_ble_devices(
        scanner: type[BleakScanner] | None = None,
) -> list[dict[str, Any]]:
    """Scanning feature
    Scan the BLE neighborhood for an Yeelight lamp
    This method requires the script to be launched as root
    Returns the list of nearby lamps
    """
    lamp_list = []
    scanner = scanner if scanner is not None else BleakScanner

    devices = await scanner.discover()

    return devices


class JPoysonAromaDiffuserConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(
            self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle a flow initialized by the user."""

        if user_input is None:
            schema = {
                vol.Required(CONF_ENTRY_METHOD): vol.In(
                    [CONF_ENTRY_SCAN, CONF_ENTRY_MANUAL]
                )
            }
            return self.async_show_form(step_id="user", data_schema=vol.Schema(schema))

        method = user_input[CONF_ENTRY_METHOD]
        logger.debug(f"Method selected: {method}")
        if method == CONF_ENTRY_SCAN:
            return await self.async_step_scan()
        else:
            self.devices = []
            return await self.async_step_device()

    async def async_step_device(
            self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle setting up a device."""
        if not user_input:
            schema_mac = str
            if self.devices:
                schema_mac = vol.In(self.devices)
            schema = vol.Schema(
                {vol.Required(CONF_NAME): str, vol.Required(DEVICE_ID): schema_mac}
            )
            return self.async_show_form(step_id="device", data_schema=schema)

        # user_input[DEVICE_ID] = user_input[DEVICE_ID][:17]
        unique_id = device_registry.format_mac(user_input[DEVICE_ID])
        logger.debug(f"JPoyson UniqueID: {unique_id}")

        await self.async_set_unique_id(unique_id)
        self._abort_if_unique_id_configured()

        # return self.async_create_entry(title=user_input[CONF_NAME], data=user_input)
        return self.async_create_entry(
            title=user_input[CONF_NAME] or f"JPoyson Aroma Diffuser ({user_input[DEVICE_ID]})",
            data={DEVICE_ID: user_input[DEVICE_ID]}
        )

    # https://github.com/hcoohb/hass-yeelightbt/blob/master/custom_components/yeelight_bt/config_flow.py

    async def async_step_scan(
            self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the discovery by scanning."""
        errors = {}
        if user_input is None:
            return self.async_show_form(step_id="scan")
        scanner = async_get_scanner(self.hass)
        logger.debug("Preparing for a scan")
        # first we check if scanner from HA bluetooth is enabled
        try:
            if len(scanner.discovered_devices) >= 1:
                # raises Attribute errors if bluetooth not configured
                logger.debug(f"Using HA scanner {scanner}")
        except AttributeError:
            scanner = create_bleak_scanner(BluetoothScanningMode.ACTIVE, None)
            logger.debug("Using bleak scanner through HA")
        try:
            logger.debug("Starting a scan for JPoyson Aroma Diffuser devices...")
            ble_devices = await discover_ble_devices(scanner)
        except BleakError as err:
            logger.error(f"Bluetooth connection error while trying to scan: {err}")
            errors["base"] = "BleakError"
            return self.async_show_form(step_id="scan", errors=errors)

        if not ble_devices:
            return self.async_abort(reason="no_devices_found")
        self.devices = [
            f"{dev['ble_device'].address} ({dev['model']})" for dev in ble_devices
        ]
        # TODO: filter existing devices ?

        return await self.async_step_device()

    # async def async_step_user(self, user_input=None):
    #     """Handle the initial step."""
    #     errors = {}
    #
    #     if user_input is not None:
    #         device_id = user_input.get("device_id")
    #         manual_device_id = user_input.get("manual_device_id")
    #
    #         if not device_id and not manual_device_id:
    #             errors["base"] = "invalid_device_id"
    #         else:
    #             await self.async_set_unique_id(device_id)
    #             self._abort_if_unique_id_configured()
    #
    #             return self.async_create_entry(
    #                 title=f"JPoyson Aroma Diffuser ({device_id or manual_device_id})",
    #                 data={DEVICE_ID: device_id or manual_device_id}
    #             )
    #
    #     # Discover available devices
    #     logger.warning("Calling async_step_user...")
    #     devices = await self._async_discover_devices()
    #     logger.warning("Discovered devices: %s", devices)
    #
    #     if not devices:
    #         logger.warning("No BLE devices found.")
    #         return self.async_abort(reason="no_devices_found")
    #
    #     # Extract device IDs and names from the list of devices
    #     device_options: list[SelectOptionDict] = [
    #         SelectOptionDict(label=device["name"], value=device["address"]) for device in devices
    #     ]
    #     logger.warning("Device options: %s", device_options)
    #
    #     # Show form with device selection dropdown
    #     return self.async_show_form(
    #         step_id="user",
    #         data_schema=vol.Schema({
    #             vol.Optional("manual_device_id"): str,
    #             vol.Optional("device_id"): selector.SelectSelector(
    #                 selector.SelectSelectorConfig(options=device_options),
    #             ),
    #         }),
    #         errors=errors
    #     )
    #
    # async def _async_discover_devices(self):
    #     """Discover BLE devices."""
    #     logger.warning("Discovering BLE devices...")
    #     try:
    #         # Use BleakScanner to discover BLE devices
    #         devices = await BleakScanner.discover()
    #         logger.warning("Discovered %d BLE devices", len(devices))
    #         return [{"name": device.name, "address": device.address} for device in devices]
    #     except Exception as e:
    #         logger.error("Error discovering BLE devices: %s", e)
    #         return []
