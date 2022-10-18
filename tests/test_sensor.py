import asyncio
import json
from unittest.mock import MagicMock

import pytest

from homepilot.sensor import ContactState, HomePilotSensor


class TestHomePilotCover:
    @pytest.fixture
    def mocked_api_env_sensor(self, event_loop):
        f = open("tests/test_files/device_env_sensor.json")
        j = json.load(f)
        api = MagicMock()
        func_get_device = asyncio.Future(loop=event_loop)
        func_get_device.set_result(j["payload"]["device"])
        api.get_device.return_value = func_get_device
        yield api

    @pytest.fixture
    def mocked_api_contact_sensor(self, event_loop):
        f = open("tests/test_files/device_contact_sensor.json")
        j = json.load(f)
        api = MagicMock()
        func_get_device = asyncio.Future(loop=event_loop)
        func_get_device.set_result(j["payload"]["device"])
        api.get_device.return_value = func_get_device
        yield api

    @pytest.mark.asyncio
    async def test_env_sensor_build_from_api(self, mocked_api_env_sensor):
        env_sensor: HomePilotSensor = await HomePilotSensor.async_build_from_api(mocked_api_env_sensor, 1)
        assert env_sensor.did == "1010012"
        assert env_sensor.uid == "692187_S_1"
        assert env_sensor.name == "Umweltsensor"
        assert env_sensor.device_number == "32000064_S"
        assert env_sensor.device_group == "3"
        assert env_sensor.fw_version == "0.3-1"
        assert env_sensor.model == "Sensor DuoFern Environmental sensor"
        assert env_sensor.has_ping_cmd is False
        assert env_sensor.has_battery_level is False
        assert env_sensor.has_brightness is True
        assert env_sensor.has_contact_state is False
        assert env_sensor.has_rain_detection is True
        assert env_sensor.has_sun_detection is True
        assert env_sensor.has_sun_direction is True
        assert env_sensor.has_sun_height is True
        assert env_sensor.has_temperature is True
        assert env_sensor.has_wind_speed is True
        assert env_sensor.has_target_temperature is False

    @pytest.mark.asyncio
    async def test_contact_sensor_build_from_api(self, mocked_api_contact_sensor):
        contact_sensor: HomePilotSensor = await HomePilotSensor.async_build_from_api(mocked_api_contact_sensor, 1)
        assert contact_sensor.did == "1010072"
        assert contact_sensor.uid == "ac0914_1"
        assert contact_sensor.name == "Esszimmer2"
        assert contact_sensor.device_number == "32003164"
        assert contact_sensor.device_group == "3"
        assert contact_sensor.fw_version == ""
        assert contact_sensor.model == "DuoFern Window/Door Contact"
        assert contact_sensor.has_ping_cmd is False
        assert contact_sensor.has_battery_level is True
        assert contact_sensor.has_brightness is False
        assert contact_sensor.has_contact_state is True
        assert contact_sensor.has_rain_detection is False
        assert contact_sensor.has_sun_detection is False
        assert contact_sensor.has_sun_direction is False
        assert contact_sensor.has_sun_height is False
        assert contact_sensor.has_temperature is False
        assert contact_sensor.has_wind_speed is False
        assert contact_sensor.has_target_temperature is False

    @pytest.mark.asyncio
    async def test_env_sensor_update_state(self, mocked_api_env_sensor):
        env_sensor: HomePilotSensor = await HomePilotSensor.async_build_from_api(mocked_api_env_sensor, 1)
        env_sensor.update_state({
            "readings": {
                "sun_detected": False,
                "sun_brightness": 1,
                "sun_direction": 87.0,
                "sun_elevation": -7,
                "wind_speed": 0.0,
                "rain_detected": True,
                "temperature_primary": 2.5
            },
            "statusValid": True
        })
        assert env_sensor.sun_detection_value is False
        assert env_sensor.brightness_value == 1
        assert env_sensor.sun_direction_value == 87.0
        assert env_sensor.sun_height_value == -7
        assert env_sensor.wind_speed_value == 0.0
        assert env_sensor.rain_detection_value is True
        assert env_sensor.temperature_value == 2.5
        assert env_sensor.available is True

    @pytest.mark.asyncio
    async def test_contact_sensor_update_state(self, mocked_api_contact_sensor):
        contact_sensor: HomePilotSensor = await HomePilotSensor.async_build_from_api(mocked_api_contact_sensor, 1)
        contact_sensor.update_state({
            "readings": {
                "contact_state": "open"
            },
            "batteryStatus": 54,
            "statusValid": True
        })
        assert contact_sensor.contact_state_value == ContactState.OPEN
        assert contact_sensor.battery_level_value == 54
        assert contact_sensor.available is True
        contact_sensor.update_state({
            "readings": {
                "contact_state": "closed"
            },
            "batteryStatus": 99,
            "statusValid": False
        })
        assert contact_sensor.contact_state_value == ContactState.CLOSED
        assert contact_sensor.battery_level_value == 99
        assert contact_sensor.available is False
