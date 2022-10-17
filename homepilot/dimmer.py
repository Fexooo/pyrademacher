import asyncio
from enum import Enum
from .const import (
    APICAP_CURR_SLAT_POS_CFG,
    APICAP_DEVICE_TYPE_LOC,
    APICAP_GOTO_POS_CMD,
    APICAP_ID_DEVICE_LOC,
    APICAP_NAME_DEVICE_LOC,
    APICAP_PING_CMD,
    APICAP_PROD_CODE_DEVICE_LOC,
    APICAP_PROT_ID_DEVICE_LOC,
    APICAP_SET_SLAT_POS_CMD,
    APICAP_VERSION_CFG,
    SUPPORTED_DEVICES,
)
from .api import HomePilotApi
from .device import HomePilotDevice


class CoverType(Enum):
    SHUTTER = 2
    GARAGE = 8


class HomePilotDimmer(HomePilotDevice):
    _can_set_position: bool
    _cover_position: int = None
    _is_on: bool

    def __init__(
        self,
        api: HomePilotApi,
        did: int,
        uid: str,
        name: str,
        device_number: str,
        model: str,
        fw_version: str,
        device_group: int,
        has_ping_cmd: bool = False,
        can_set_position: bool = True,
    ) -> None:
        super().__init__(
            api=api,
            did=did,
            uid=uid,
            name=name,
            device_number=device_number,
            model=model,
            fw_version=fw_version,
            device_group=device_group,
            has_ping_cmd=has_ping_cmd,
        )
        self._can_set_position = can_set_position

    @staticmethod
    def build_from_api(api: HomePilotApi, did: str):
        return asyncio.run(HomePilotDimmer.async_build_from_api(api, did))

    @staticmethod
    async def async_build_from_api(api: HomePilotApi, did):
        """Build a new HomePilotDevice from the response of API"""
        device = await api.get_device(did)
        device_map = HomePilotDevice.get_capabilities_map(device)
        return HomePilotDimmer(
            api=api,
            did=device_map[APICAP_ID_DEVICE_LOC]["value"],
            uid=device_map[APICAP_PROT_ID_DEVICE_LOC]["value"],
            name=device_map[APICAP_NAME_DEVICE_LOC]["value"],
            device_number=device_map[APICAP_PROD_CODE_DEVICE_LOC]["value"],
            model=SUPPORTED_DEVICES[device_map[APICAP_PROD_CODE_DEVICE_LOC][
                "value"]]["name"]
            if device_map[APICAP_PROD_CODE_DEVICE_LOC]["value"] in
            SUPPORTED_DEVICES
            else "Generic Device",
            fw_version=device_map[APICAP_VERSION_CFG]["value"]
            if APICAP_VERSION_CFG in device_map else "",
            device_group=device_map[APICAP_DEVICE_TYPE_LOC]["value"],
            has_ping_cmd=APICAP_PING_CMD in device_map,
            can_set_position=APICAP_GOTO_POS_CMD in device_map,
        )

    def update_state(self, state):
        super().update_state(state)
        self.cover_position = 100 - state["statusesMap"]["Position"]

    async def async_set_cover_position(self, new_position) -> None:
        if self.can_set_position:
            await self.api.async_set_cover_position(self.did,
                                                    100 - new_position)

    @property
    def cover_position(self) -> int:
        return self._cover_position

    @cover_position.setter
    def cover_position(self, cover_position):
        self._cover_position = cover_position

    @property
    def can_set_position(self) -> bool:
        return self._can_set_position

    @property
    def is_on(self) -> bool:
        return self._is_on

    @is_on.setter
    def is_on(self, is_on):
        self._is_on = is_on

    async def async_turn_on(self) -> None:
        await self.api.async_turn_on(self.did)

    async def async_turn_off(self) -> None:
        await self.api.async_turn_off(self.did)

    async def async_toggle(self) -> None:
        if self.is_on:
            await self.async_turn_off()
        else:
            await self.async_turn_on()
