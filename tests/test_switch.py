import asyncio
import json
from unittest.mock import MagicMock

import pytest

from homepilot.switch import HomePilotSwitch


class TestHomePilotSwitch:
    @pytest.fixture
    def mocked_api(self, event_loop):
        f = open("tests/test_files/device_switch.json")
        j = json.load(f)
        api = MagicMock()
        func_get_device = asyncio.Future(loop=event_loop)
        func_get_device.set_result(j["payload"]["device"])
        api.get_device.return_value = func_get_device
        func_turn_on = asyncio.Future(loop=event_loop)
        func_turn_on.set_result(None)
        api.async_turn_on.return_value = func_turn_on
        func_turn_off = asyncio.Future(loop=event_loop)
        func_turn_off.set_result(None)
        api.async_turn_off.return_value = func_turn_off
        func_ping = asyncio.Future(loop=event_loop)
        func_ping.set_result(None)
        api.async_ping.return_value = func_ping
        yield api

    @pytest.mark.asyncio
    async def test_build_from_api(self, mocked_api):
        switch = await HomePilotSwitch.async_build_from_api(mocked_api, 1)
        assert switch.did == "1010018"
        assert switch.uid == "43d488_1"
        assert switch.name == "Hütte"
        assert switch.device_number == "35000262"
        assert switch.device_group == "1"
        assert switch.fw_version == "4.7-1"
        assert switch.model == "DuoFern Universal actuator 2-channel"
        assert switch.has_ping_cmd is True

    @pytest.mark.asyncio
    async def test_update_state(self, mocked_api):
        switch = await HomePilotSwitch.async_build_from_api(mocked_api, 1)
        switch.update_state({
            "statusesMap": {
                "Position": 100
            },
            "statusValid": True
        })
        assert switch.is_on is True
        assert switch.available is True

        switch.update_state({
            "statusesMap": {
                "Position": 0
            },
            "statusValid": False
        })
        assert switch.is_on is False
        assert switch.available is False

    @pytest.mark.asyncio
    async def test_async_turn_on(self, mocked_api):
        switch = await HomePilotSwitch.async_build_from_api(mocked_api, 1)
        await switch.async_turn_on()
        mocked_api.async_turn_on.assert_called_with('1010018')

    @pytest.mark.asyncio
    async def test_async_turn_off(self, mocked_api):
        switch = await HomePilotSwitch.async_build_from_api(mocked_api, 1)
        await switch.async_turn_off()
        mocked_api.async_turn_off.assert_called_with('1010018')

    @pytest.mark.asyncio
    async def test_async_toggle(self, mocked_api):
        switch = await HomePilotSwitch.async_build_from_api(mocked_api, 1)
        switch.update_state({
            "statusesMap": {
                "Position": 100
            },
            "statusValid": True
        })
        await switch.async_toggle()
        mocked_api.async_turn_off.assert_called_with('1010018')
        switch.update_state({
            "statusesMap": {
                "Position": 0
            },
            "statusValid": True
        })
        await switch.async_toggle()
        mocked_api.async_turn_on.assert_called_with('1010018')
