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


class HomePilotCover(HomePilotDevice):
    _can_set_position: bool
    _cover_type: int
    _has_tilt: bool
    _can_set_tilt_position: bool
    _cover_position: int = None
    _cover_tilt_position: int = None
    _is_closed: bool
    _is_closing: bool
    _is_opening: bool

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
        cover_type: int = 2,
        has_tilt: bool = False,
        can_set_tilt_position: bool = False,
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
        self._cover_type = cover_type
        self._has_tilt = has_tilt
        self._can_set_tilt_position = can_set_tilt_position

    @staticmethod
    def build_from_api(api: HomePilotApi, did: str):
        return asyncio.run(HomePilotCover.async_build_from_api(api, did))

    @staticmethod
    async def async_build_from_api(api: HomePilotApi, did):
        """Build a new HomePilotDevice from the response of API"""
        device = await api.get_device(did)
        device_map = HomePilotDevice.get_capabilities_map(device)
        return HomePilotCover(
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
            cover_type=int(device_map[APICAP_DEVICE_TYPE_LOC]["value"]),
            has_tilt=APICAP_SET_SLAT_POS_CMD in device_map,
            can_set_tilt_position=APICAP_SET_SLAT_POS_CMD in device_map,
        )

    def update_state(self, state):
        super().update_state(state)
        self.cover_position = 100 - state["statusesMap"]["Position"]
        if self.has_tilt:
            if "slatposition" not in state["statusesMap"]:
                self.has_tilt = False
                self.can_set_tilt_position = False
            else:
                self.cover_tilt_position = 100 - state["statusesMap"][
                    "slatposition"]
        self.is_closed = self.cover_position == 0
        self.is_closing = False
        self.is_opening = False

    async def async_open_cover(self) -> None:
        await self.api.async_open_cover(self.did)

    async def async_close_cover(self) -> None:
        await self.api.async_close_cover(self.did)

    async def async_set_cover_position(self, new_position) -> None:
        if self.can_set_position:
            await self.api.async_set_cover_position(self.did,
                                                    100 - new_position)

    async def async_stop_cover(self) -> None:
        await self.api.async_stop_cover(self.did)

    async def async_open_cover_tilt(self) -> None:
        if self.has_tilt:
            await self.api.async_open_cover_tilt(self.did)

    async def async_close_cover_tilt(self) -> None:
        if self.has_tilt:
            await self.api.async_close_cover_tilt(self.did)

    async def async_set_cover_tilt_position(self, new_position) -> None:
        if self.has_tilt and self.can_set_tilt_position:
            await self.api.async_set_cover_tilt_position(self.did,
                                                         100 - new_position)

    async def async_stop_cover_tilt(self) -> None:
        if self.has_tilt:
            await self.api.async_stop_cover_tilt(self.did)

    @property
    def cover_position(self) -> int:
        return self._cover_position

    @property
    def cover_tilt_position(self) -> int:
        return self._cover_tilt_position

    @cover_tilt_position.setter
    def cover_tilt_position(self, cover_tilt_position):
        self._cover_tilt_position = cover_tilt_position

    @cover_position.setter
    def cover_position(self, cover_position):
        self._cover_position = cover_position

    @property
    def is_closed(self) -> bool:
        return self._is_closed

    @is_closed.setter
    def is_closed(self, is_closed):
        self._is_closed = is_closed

    @property
    def is_closing(self) -> bool:
        return self._is_closing

    @is_closing.setter
    def is_closing(self, is_closing):
        self._is_closing = is_closing

    @property
    def is_opening(self) -> bool:
        return self._is_opening

    @is_opening.setter
    def is_opening(self, is_opening):
        self._is_opening = is_opening

    @property
    def can_set_position(self) -> bool:
        return self._can_set_position

    @property
    def cover_type(self) -> int:
        return self._cover_type

    @property
    def has_tilt(self) -> bool:
        return self._has_tilt

    @has_tilt.setter
    def has_tilt(self, has_tilt):
        self._has_tilt = has_tilt

    @property
    def can_set_tilt_position(self) -> bool:
        return self._can_set_tilt_position

    @can_set_tilt_position.setter
    def can_set_tilt_position(self, can_set_tilt_position):
        self._can_set_tilt_position = can_set_tilt_position
