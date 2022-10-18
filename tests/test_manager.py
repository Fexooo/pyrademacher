import asyncio
import json
from unittest.mock import MagicMock
import pytest
from homepilot.api import HomePilotApi
from homepilot.cover import HomePilotCover
from homepilot.hub import HomePilotHub

from homepilot.manager import HomePilotManager
from homepilot.sensor import ContactState, HomePilotSensor
from homepilot.switch import HomePilotSwitch


TEST_HOST = "test_host"


class TestHomePilotManager:
    @pytest.fixture
    def mocked_api(self, event_loop):
        api = MagicMock(HomePilotApi)

        f = open("tests/test_files/devices.json")
        devices = json.load(f)
        func_get_devices = asyncio.Future(loop=event_loop)
        func_get_devices.set_result(devices["payload"]["devices"])
        api.get_devices.return_value = yield from func_get_devices

        f1 = open("tests/test_files/device_cover.json")
        device1 = json.load(f1)
        func_get_device1 = asyncio.Future(loop=event_loop)
        func_get_device1.set_result(device1["payload"]["device"])

        f2 = open("tests/test_files/device_env_sensor.json")
        device2 = json.load(f2)
        func_get_device2 = asyncio.Future(loop=event_loop)
        func_get_device2.set_result(device2["payload"]["device"])

        f3 = open("tests/test_files/device_switch.json")
        device3 = json.load(f3)
        func_get_device3 = asyncio.Future(loop=event_loop)
        func_get_device3.set_result(device3["payload"]["device"])

        f4 = open("tests/test_files/device_contact_sensor.json")
        device4 = json.load(f4)
        func_get_device4 = asyncio.Future(loop=event_loop)
        func_get_device4.set_result(device4["payload"]["device"])

        api.get_device.side_effect = [
            (yield from func_get_device1),
            (yield from func_get_device2),
            (yield from func_get_device3),
            (yield from func_get_device4)
        ]

        f_actuators = open("tests/test_files/actuators.json")
        actuators_response = json.load(f_actuators)
        actuators = {str(device["did"]): device for device in
                     actuators_response["devices"]}
        f_actuators = open("tests/test_files/sensors.json")
        sensors_response = json.load(f_actuators)
        sensors = {str(device["did"]): device for device in sensors_response[
            "meters"]}
        func_get_devices_state = asyncio.Future(loop=event_loop)
        func_get_devices_state.set_result({**actuators, **sensors})
        api.async_get_devices_state.return_value = \
            yield from func_get_devices_state

        func_get_fw_version = asyncio.Future(loop=event_loop)
        func_get_fw_version.set_result({
            "hw_platform": "ampere",
            "sw_platform": "bridge",
            "version": "5.4.3",
            "df_stick_version": "2.0"
        })
        api.async_get_fw_version.return_value = yield from func_get_fw_version
        func_get_fw_status = asyncio.Future(loop=event_loop)
        func_get_fw_status.set_result({
            "version": "5.4.9",
            "update_channel": "manifest-ampere-5.4.0",
            "is_default": True,
            "update_status": "UPDATE_AVAILABLE"
        })
        api.async_get_fw_status.return_value = yield from func_get_fw_status
        func_get_led_status = asyncio.Future(loop=event_loop)
        func_get_led_status.set_result({"status": "disabled"})
        api.async_get_led_status.return_value = yield from func_get_led_status

        yield api

    @pytest.mark.asyncio
    async def test_build_manager(self, mocked_api):
        manager = await HomePilotManager.async_build_manager(mocked_api)
        assert list(manager.devices.keys()) == \
            ['1', '1010012', '1010018', '1010072', '-1']
        assert isinstance(manager.devices['1'], HomePilotCover)
        assert isinstance(manager.devices['1010012'], HomePilotSensor)
        assert isinstance(manager.devices['1010018'], HomePilotSwitch)
        assert isinstance(manager.devices['1010072'], HomePilotSensor)
        assert isinstance(manager.devices['-1'], HomePilotHub)

    @pytest.mark.asyncio
    async def test_update_state(self, mocked_api):
        manager = await HomePilotManager.async_build_manager(mocked_api)
        await manager.update_states()
        assert manager.devices["1"].cover_position == 35
        assert manager.devices["1"].cover_tilt_position == 11
        assert manager.devices["1010012"].temperature_value == 2.5
        assert manager.devices["1010012"].sun_height_value == -7
        assert manager.devices["1010018"].is_on
        assert manager.devices["1010072"].contact_state_value == \
            ContactState.OPEN
        assert manager.devices["1010072"].battery_level_value == 99
        assert not manager.devices["-1"].led_status
        assert manager.devices["-1"].fw_update_version == "5.4.9"
