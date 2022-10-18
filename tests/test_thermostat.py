import asyncio
import json
from unittest.mock import MagicMock

import pytest

from homepilot.thermostat import HomePilotThermostat


class TestHomePilotCover:
    @pytest.fixture
    def mocked_api(self, event_loop):
        f = open("tests/test_files/device_thermostat.json")
        j = json.load(f)
        api = MagicMock()
        func_get_device = asyncio.Future(loop=event_loop)
        func_get_device.set_result(j["payload"]["device"])
        api.get_device.return_value = func_get_device
        func_set_target_temperature = asyncio.Future(loop=event_loop)
        func_set_target_temperature.set_result(None)
        api.async_set_target_temperature.return_value = func_set_target_temperature
        func_set_auto_mode = asyncio.Future(loop=event_loop)
        func_set_auto_mode.set_result(None)
        api.async_set_auto_mode.return_value = func_set_auto_mode
        yield api

    @pytest.mark.asyncio
    async def test_build_from_api(self, mocked_api):
        thermostat: HomePilotThermostat = await HomePilotThermostat.async_build_from_api(mocked_api, 1)
        assert thermostat.did == "1010014"
        assert thermostat.uid == "733e25_A_1"
        assert thermostat.name == "Wohnzimmer-Raumthermostat"
        assert thermostat.device_number == "32501812_A"
        assert thermostat.device_group == "5"
        assert thermostat.fw_version == "1.4-1"
        assert thermostat.model == "DuoFern Room Thermostat"
        assert thermostat.has_ping_cmd is True
        assert thermostat.min_temperature == -40.0
        assert thermostat.max_temperature == 80.0
        assert thermostat.has_temperature is True
        assert thermostat.has_target_temperature is True
        assert thermostat.can_set_target_temperature is True
        assert thermostat.min_target_temperature == 4.0
        assert thermostat.max_target_temperature == 40.0
        assert thermostat.step_target_temperature == 0.5

    @pytest.mark.asyncio
    async def test_update_state(self, mocked_api):
        thermostat: HomePilotThermostat = await HomePilotThermostat.async_build_from_api(mocked_api, 1)
        thermostat.update_state({
            "statusesMap": {
                "Manuellbetrieb": 100,
                "Position": 240,
                "acttemperatur": 212,
                "relaisstatus": 1,
                "automaticvalue": 215,
                "manualoverride": 0
            },
            "statusValid": True
        })
        assert thermostat.temperature_value == 21.2
        assert thermostat.target_temperature_value == 24.0

    @pytest.mark.asyncio
    async def test_async_set_target_temperature(self, mocked_api):
        thermostat = await HomePilotThermostat.async_build_from_api(mocked_api, 1)
        await thermostat.async_set_target_temperature(10)
        mocked_api.async_set_target_temperature.assert_called_with('1010014', 10)

    @pytest.mark.asyncio
    async def test_async_set_auto_mode(self, mocked_api):
        thermostat = await HomePilotThermostat.async_build_from_api(mocked_api, 1)
        await thermostat.async_set_auto_mode(True)
        mocked_api.async_set_auto_mode.assert_called_with('1010014', True)
