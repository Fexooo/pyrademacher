import asyncio
import logging
from typing import Dict

from .dimmer import HomePilotDimmer
from .hub import HomePilotHub
from .sensor import HomePilotSensor
from .switch import HomePilotSwitch
from .cover import HomePilotCover
from .thermostat import HomePilotThermostat
from .api import HomePilotApi

from .device import HomePilotDevice

_LOGGER = logging.getLogger(__name__)


class HomePilotManager:
    _api: HomePilotApi
    _devices: Dict[str, HomePilotDevice]

    def __init__(self, api: HomePilotApi) -> None:
        self._api = api

    @staticmethod
    def build_manager(api: HomePilotApi):
        return asyncio.run(HomePilotManager.async_build_manager(api))

    @staticmethod
    async def async_build_manager(api: HomePilotApi):
        manager = HomePilotManager(api)
        manager.devices = {
            id_type["did"]: await HomePilotManager.async_build_device(manager.api, id_type)
            for id_type in await manager.get_device_ids_types()
            if id_type["type"] in ["-1", "1", "2", "3", "4", "5", "8"]
        }
        return manager

    @staticmethod
    async def async_build_device(api, id_type):
        if id_type["type"] == "-1":
            return await HomePilotHub.async_build_from_api(api, id_type["did"])
        if id_type["type"] == "1":
            return await HomePilotSwitch.async_build_from_api(api, id_type["did"])
        if id_type["type"] == "2":
            return await HomePilotCover.async_build_from_api(api, id_type["did"])
        if id_type["type"] == "3":
            return await HomePilotSensor.async_build_from_api(api, id_type["did"])
        if id_type["type"] == "4":
            return await HomePilotDimmer.async_build_from_api(api, id_type["did"])
        if id_type["type"] == "5":
            return await HomePilotThermostat.async_build_from_api(api, id_type["did"])
        if id_type["type"] == "8":
            return await HomePilotCover.async_build_from_api(api, id_type["did"])
        return None

    async def get_hub_state(self):
        return {
            "status": await self.api.async_get_fw_status(),
            "version": await self.api.async_get_fw_version(),
            "led": await self.api.async_get_led_status(),
        }

    async def update_state(self, did):
        try:
            if did == "-1":
                state = await self.get_hub_state()
            else:
                state = await self.api.async_get_device_state(did)
        except Exception:
            device: HomePilotDevice = self.devices[did]
            device.available = False

        device: HomePilotDevice = self.devices[did]
        device.update_state(state)
        return device

    async def update_states(self):
        try:
            states = await self.api.async_get_devices_state()
            states["-1"] = await self.get_hub_state()
        except Exception:
            for did in self.devices:
                device: HomePilotDevice = self.devices[did]
                device.available = False
            raise

        for did in self.devices:
            device: HomePilotDevice = self.devices[did]
            if device.did in states:
                device.update_state(states[did])
            else:
                device.available = False

        return self.devices

    async def get_device_ids_types(self):
        devices = await self.api.get_devices()
        devices.append(HomePilotHub.get_capabilities())
        test = [HomePilotDevice.get_did_type_from_json(device) for device in devices]
        print(test)
        return test

    @property
    def api(self) -> HomePilotApi:
        return self._api

    @property
    def devices(self) -> Dict[str, HomePilotDevice]:
        return self._devices

    @devices.setter
    def devices(self, devices: Dict[str, HomePilotDevice]):
        self._devices = devices
