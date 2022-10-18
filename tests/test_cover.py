import asyncio
import json
from unittest.mock import MagicMock

import pytest

from homepilot.cover import HomePilotCover


class TestHomePilotCover:
    @pytest.fixture
    def mocked_api(self, event_loop):
        f = open("tests/test_files/device_cover.json")
        j = json.load(f)
        api = MagicMock()
        func_get_device = asyncio.Future(loop=event_loop)
        func_get_device.set_result(j["payload"]["device"])
        api.get_device.return_value = func_get_device
        func_open_cover = asyncio.Future(loop=event_loop)
        func_open_cover.set_result(None)
        api.async_open_cover.return_value = func_open_cover
        func_close_cover = asyncio.Future(loop=event_loop)
        func_close_cover.set_result(None)
        api.async_close_cover.return_value = func_close_cover
        func_stop_cover = asyncio.Future(loop=event_loop)
        func_stop_cover.set_result(None)
        api.async_stop_cover.return_value = func_stop_cover
        func_set_cover_position = asyncio.Future(loop=event_loop)
        func_set_cover_position.set_result(None)
        api.async_set_cover_position.return_value = func_set_cover_position
        func_ping = asyncio.Future(loop=event_loop)
        func_ping.set_result(None)
        api.async_ping.return_value = func_ping
        yield api

    @pytest.mark.asyncio
    async def test_build_from_api(self, mocked_api):
        cover = await HomePilotCover.async_build_from_api(mocked_api, 1)
        assert cover.did == "1"
        assert cover.uid == "407903_1"
        assert cover.name == "Living Room Blinds"
        assert cover.device_number == "14234511"
        assert cover.device_group == "2"
        assert cover.fw_version == "1.2-1"
        assert cover.model == "RolloTron radio beltwinder"
        assert cover.has_ping_cmd is True
        assert cover.can_set_position is True

    @pytest.mark.asyncio
    async def test_update_state(self, mocked_api):
        cover = await HomePilotCover.async_build_from_api(mocked_api, 1)
        cover.update_state({
            "statusesMap": {
                "Position": 100,
                "slatposition": 34
            },
            "statusValid": True
        })
        assert cover.is_closed is True
        assert cover.cover_position == 0
        assert cover.cover_tilt_position == 66
        assert cover.is_closing is False
        assert cover.is_opening is False
        assert cover.available is True

        cover.update_state({
            "statusesMap": {
                "Position": 40,
                "slatposition": 55
            },
            "statusValid": False
        })
        assert cover.is_closed is False
        assert cover.cover_position == 60
        assert cover.cover_tilt_position == 45
        assert cover.is_closing is False
        assert cover.is_opening is False
        assert cover.available is False

    @pytest.mark.asyncio
    async def test_async_open_cover(self, mocked_api):
        cover = await HomePilotCover.async_build_from_api(mocked_api, 1)
        await cover.async_open_cover()
        mocked_api.async_open_cover.assert_called_with('1')

    @pytest.mark.asyncio
    async def test_async_close_cover(self, mocked_api):
        cover = await HomePilotCover.async_build_from_api(mocked_api, 1)
        await cover.async_close_cover()
        mocked_api.async_close_cover.assert_called_with('1')

    @pytest.mark.asyncio
    async def test_async_stop_cover(self, mocked_api):
        cover = await HomePilotCover.async_build_from_api(mocked_api, 1)
        await cover.async_stop_cover()
        mocked_api.async_stop_cover.assert_called_with('1')

    @pytest.mark.asyncio
    async def test_async_set_cover_position(self, mocked_api):
        cover = await HomePilotCover.async_build_from_api(mocked_api, 1)
        await cover.async_set_cover_position(40)
        mocked_api.async_set_cover_position.assert_called_with('1', 60)

    @pytest.mark.asyncio
    async def test_async_ping(self, mocked_api):
        cover = await HomePilotCover.async_build_from_api(mocked_api, 1)
        await cover.async_ping()
        mocked_api.async_ping.assert_called_with('1')
