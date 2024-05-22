import asyncio
import logging
from datetime import datetime

from bleak import BleakClient

NOTIFICATION_CHARACTERISTIC_UUID = "0783B03E-8535-B5A0-7140-A304D2495CB8"
SERVICE_CHARACTERISTIC_UUID = "0783B03E-8535-B5A0-7140-A304D2495CBA"


class DeviceManager:
    def __init__(self):
        self.client = None
        self.device_id = None
        self.sendDateTimeCount = 0
        self.sendClockInterval = None
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 10  # Maximum reconnect attempts
        self.logger = logging.getLogger(__package__)
        self.state_object_array = [None] * 4  # Assuming 4 timer slots as per the JS code
        self.power_status = False
        self.power_status_callback = None

    def get_control_code(self, timer_mode, power_status, current_time_type):
        control_code = [165, 250, power_status, timer_mode['week'], current_time_type]
        start_hour = int(timer_mode['startTimeHour'])
        stop_hour = int(timer_mode['stopTimeHour'])
        start_min = int(timer_mode['startTimeMin'])
        stop_min = int(timer_mode['stopTimeMin'])
        working_time = timer_mode['workingTime']
        pause_time = timer_mode['pauseTime']
        working_time_int = int(working_time)
        pause_time_int = int(pause_time)

        control_code.extend(
            [start_hour, start_min, stop_hour, stop_min, (working_time_int & 65280) >> 8, working_time_int & 255,
             (pause_time_int & 65280) >> 8, pause_time_int & 255])

        checksum = sum(control_code)
        control_code.append(checksum & 255)

        control_code_bytes = bytearray(control_code)

        return control_code_bytes

    def get_clock_code(self):
        current_time = datetime.now()
        hour = current_time.hour
        minute = current_time.minute
        second = current_time.second
        weekday = current_time.weekday() + 1  # Python's weekday starts from 0 (Monday) to 6 (Sunday)

        clock_code = []
        clock_code.extend([165, 253, weekday, hour, minute, second, 0, 0, 0, 0, 0, 0])

        checksum = sum(clock_code)
        clock_code.append(checksum & 255)

        clock_code_bytes = bytearray(clock_code)

        return clock_code_bytes

    async def turn_off_device(self):
        control_code = self.get_control_code({
            "week": 255,  # 255 represents all days of the week 11111111
            "startTimeHour": "00",
            "startTimeMin": "00",
            "stopTimeHour": "23",
            "stopTimeMin": "59",
            "workingTime": 15,
            "pauseTime": 175,
        }, 0, 1)
        await self.send_control_code(control_code)
        self.logger.info("Device turned off")

    async def turn_on_device(self):
        control_code = self.get_control_code({
            "week": 255,  # 255 represents all days of the week 11111111
            "startTimeHour": "00",
            "startTimeMin": "00",
            "stopTimeHour": "23",
            "stopTimeMin": "59",
            "workingTime": 15,
            "pauseTime": 180,
        }, 1, 1)
        await self.send_control_code(control_code)
        self.logger.info("Device turned on")

    async def connect_device(self, device_id):
        self.device_id = device_id

        async def handle_disconnect(client: BleakClient):
            self.logger.warning(f"Device {self.device_id} disconnected")
            await self.try_reconnect()

        client = BleakClient(device_id, disconnected_callback=handle_disconnect)
        return await self.try_connect(client)

    async def try_connect(self, client):
        try:
            await client.connect()
            self.logger.info(f"Connected to {self.device_id}")
            self.client = client
            self.reconnect_attempts = 0  # Reset reconnect attempts after successful connection

            await self.enable_notifications(NOTIFICATION_CHARACTERISTIC_UUID)

            await self.send_control_code(self.get_clock_code())
            self.sendDateTimeCount += 1
            self.sendClockInterval = asyncio.get_event_loop().call_later(0.1, self.send_clock_code_repeatedly)
            return True
        except Exception as e:
            self.logger.error(f"Failed to connect: {e}")
            return await self.try_reconnect()

    async def try_reconnect(self):
        if self.reconnect_attempts < self.max_reconnect_attempts:
            self.reconnect_attempts += 1
            self.logger.info(f"Reconnecting attempt {self.reconnect_attempts}/{self.max_reconnect_attempts}...")
            await asyncio.sleep(5)  # Wait before trying to reconnect
            return await self.connect_device(self.device_id)
        else:
            self.logger.error("Max reconnect attempts reached. Giving up.")
            self.reconnect_attempts = 0

        return False

    async def enable_notifications(self, characteristic_uuid):
        def notification_handler(sender, data):
            # 將 bytearray 轉換為十六進制字串
            hex_data = data.hex().upper()
            self.logger.info(f"Notification from {sender}: {hex_data}")

            if hex_data.startswith("A5FB"):
                self.set_device_state(hex_data)

            if self.power_status_callback:
                self.power_status_callback(self.power_status)
                self.logger.info(f"Callback called with power status: {self.power_status}")

        await self.client.start_notify(characteristic_uuid, notification_handler)
        self.logger.info('Notifications enabled')

    def set_device_state(self, hex_data):
        # 解析資料
        power_status = int(hex_data[4:6], 16)
        week = int(hex_data[6:8], 16)
        timer_slot = int(hex_data[8:10], 16) - 1
        start_time_hour = int(hex_data[10:12], 16)
        start_time_min = int(hex_data[12:14], 16)
        stop_time_hour = int(hex_data[14:16], 16)
        stop_time_min = int(hex_data[16:18], 16)
        working_time = int(hex_data[18:22], 16)
        pause_time = int(hex_data[22:26], 16)

        self.power_status = (power_status != 0)

        timer_object = {
            # convert to binary, this is a bitmask. 1 = Monday, 2 = Tuesday, 4 = Wednesday, 8 = Thursday, 16 = Friday, 32 = Saturday, 64 = Sunday
            "week": week,
            "startTimeHour": start_time_hour,
            "startTimeMin": start_time_min,
            "stopTimeHour": stop_time_hour,
            "stopTimeMin": stop_time_min,
            "workingTime": working_time,
            "pauseTime": pause_time,
        }
        try:
            self.state_object_array[timer_slot] = timer_object
            self.logger.info(f"Timer slot {timer_slot + 1} state updated: {timer_object}")
        except IndexError:
            self.logger.error(f"Invalid timer slot {timer_slot}")

    @property
    def connected(self):
        if not self.client:
            return False
        return self.client.is_connected

    def send_clock_code_repeatedly(self):
        if self.sendDateTimeCount < 5:
            asyncio.create_task(self.send_control_code(self.get_clock_code()))
            self.sendDateTimeCount += 1
            self.sendClockInterval = asyncio.get_event_loop().call_later(0.1, self.send_clock_code_repeatedly)
        else:
            self.sendClockInterval = None

    async def send_control_code(self, code):
        self.logger.info(f'Sending control code: {code}')
        await self.client.write_gatt_char(SERVICE_CHARACTERISTIC_UUID, code, response=True)

    def set_power_status_callback(self, callback):
        self.power_status_callback = callback
