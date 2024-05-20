import asyncio
from datetime import datetime
from bleak import BleakClient, BleakScanner

NOTIFICATION_CHARACTERISTIC_UUID = "0783B03E-8535-B5A0-7140-A304D2495CB8"
SERVICE_CHARACTERISTIC_UUID = "0783B03E-8535-B5A0-7140-A304D2495CBA"


class DeviceManager:
    def __init__(self):
        self.client = None
        self.device_id = None
        self.connected = False
        self.sendDateTimeCount = 0
        self.sendClockInterval = None

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
            "week": 255,
            "startTimeHour": "00",
            "startTimeMin": "00",
            "stopTimeHour": "23",
            "stopTimeMin": "59",
            "workingTime": 15,
            "pauseTime": 175,
        }, 0, 1)
        await self.send_control_code(control_code)
        print("Device turned off")

    async def turn_on_device(self):
        control_code = self.get_control_code({
            "week": 255,
            "startTimeHour": "00",
            "startTimeMin": "00",
            "stopTimeHour": "23",
            "stopTimeMin": "59",
            "workingTime": 15,
            "pauseTime": 180,
        }, 1, 1)
        await self.send_control_code(control_code)
        print("Device turned on")

    async def connect_device(self, device_id):
        self.device_id = device_id
        self.connected = False

        async def handle_disconnect(client):
            print(f"Device {self.device_id} disconnected")
            self.connected = False

        client = BleakClient(device_id, disconnected_callback=handle_disconnect)
        await client.connect()
        print(f"Connected to {device_id}")
        self.client = client
        self.connected = True

        services = await self.client.get_services()
        for service in services:
            print(f"Service: {service.uuid}")
            for characteristic in service.characteristics:
                print(f"  Characteristic: {characteristic.uuid}")

        await self.enable_notifications(NOTIFICATION_CHARACTERISTIC_UUID)

        await self.send_control_code(self.get_clock_code())
        self.sendDateTimeCount += 1
        self.sendClockInterval = asyncio.get_event_loop().call_later(0.1, self.send_clock_code_repeatedly)

    async def enable_notifications(self, characteristic_uuid):
        def notification_handler(sender, data):
            print(f"Notification from {sender}: {data}")

        await self.client.start_notify(characteristic_uuid, notification_handler)
        print('Notifications enabled')

    def send_clock_code_repeatedly(self):
        if self.sendDateTimeCount < 5:
            asyncio.create_task(self.send_control_code(self.get_clock_code()))
            self.sendDateTimeCount += 1
            self.sendClockInterval = asyncio.get_event_loop().call_later(0.1, self.send_clock_code_repeatedly)
        else:
            self.sendClockInterval = None

    async def send_control_code(self, code):
        print(f'Sending control code: {code}')
        await self.client.write_gatt_char(SERVICE_CHARACTERISTIC_UUID, code, response=True)
