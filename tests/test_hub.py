import asyncio
from unittest.mock import MagicMock
import pytest
from homepilot.hub import HomePilotHub

TEST_HOST = "test_host"


class TestHomePilotHub:
    @pytest.fixture
    def mocked_api(self, event_loop):
        api = MagicMock()
        api.host = TEST_HOST
        api.password = ""
        func_get_fw_version = asyncio.Future(loop=event_loop)
        func_get_fw_version.set_result({
            "hw_platform": "ampere",
            "sw_platform": "bridge",
            "version": "5.4.3",
            "df_stick_version": "2.0"
        })
        api.async_get_fw_version.return_value = func_get_fw_version
        func_get_nodename = asyncio.Future(loop=event_loop)
        func_get_nodename.set_result({"nodename": "testnodename"})
        api.async_get_nodename.return_value = func_get_nodename
        func_turn_led_on = asyncio.Future(loop=event_loop)
        func_turn_led_on.set_result(None)
        api.async_turn_led_on.return_value = func_turn_led_on
        func_turn_led_off = asyncio.Future(loop=event_loop)
        func_turn_led_off.set_result(None)
        api.async_turn_led_off.return_value = func_turn_led_off
        func_ping = asyncio.Future(loop=event_loop)
        func_ping.set_result(None)
        api.async_ping.return_value = func_ping
        yield api

    @pytest.mark.asyncio
    async def test_build_from_api(self, mocked_api):
        hub = await HomePilotHub.async_build_from_api(mocked_api, "-1")
        assert hub.api == mocked_api
        assert hub.did == "-1"
        assert hub.uid == TEST_HOST
        assert hub.device_number == "-1"
        assert hub.device_group == "-1"
        assert hub.duofern_stick_version == "2.0"
        assert hub.fw_version == "5.4.3"
        assert hub.name == "Testnodename"
        assert hub.hub_type == "Start2Smart"
        assert hub.model == "Start2Smart"
        assert hub.hw_platform == "ampere"
        assert hub.sw_platform == "bridge"
        assert hub.has_ping_cmd is False

    @pytest.mark.asyncio
    async def test_update_state(self, mocked_api):
        hub = await HomePilotHub.async_build_from_api(mocked_api, "-1")
        hub.update_state(
            {
                "status": {
                    "update_status": "UPDATE_AVAILABLE",
                    "version": "6.0.0"
                },
                "led": {
                    "status": "enabled"
                }
            }
        )
        assert hub.fw_update_available is True
        assert hub.fw_update_version == "6.0.0"
        assert hub.led_status is True

    @pytest.mark.asyncio
    async def test_async_turn_led_on(self, mocked_api):
        cover = await HomePilotHub.async_build_from_api(mocked_api, 1)
        await cover.async_turn_led_on()
        mocked_api.async_turn_led_on.assert_called()

    @pytest.mark.asyncio
    async def test_async_turn_led_off(self, mocked_api):
        cover = await HomePilotHub.async_build_from_api(mocked_api, 1)
        await cover.async_turn_led_off()
        mocked_api.async_turn_led_off.assert_called()

    @pytest.mark.asyncio
    async def test_async_ping(self, mocked_api):
        cover = await HomePilotHub.async_build_from_api(mocked_api, 1)
        await cover.async_ping()
        mocked_api.async_ping.assert_not_called()
