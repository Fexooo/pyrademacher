import asyncio
from .const import (
    APICAP_AUTO_MODE_CFG,
    APICAP_BATT_VALUE_EVT,
    APICAP_BATTERY_LVL_PCT_MEA,
    APICAP_DEVICE_TYPE_LOC,
    APICAP_ID_DEVICE_LOC,
    APICAP_NAME_DEVICE_LOC,
    APICAP_PING_CMD,
    APICAP_PROD_CODE_DEVICE_LOC,
    APICAP_PROT_ID_DEVICE_LOC,
    APICAP_TARGET_TEMPERATURE_CFG,
    APICAP_TEMPERATURE_INT_CFG,
    APICAP_VERSION_CFG,
    SUPPORTED_DEVICES,
)
from .api import HomePilotApi
from .device import HomePilotDevice


class HomePilotThermostat(HomePilotDevice):
    _has_auto_mode: bool
    _auto_mode_value: bool
    _has_temperature: bool
    _min_temperature: float
    _max_temperature: float
    _has_target_temperature: bool
    _temperature_value: float
    _target_temperature_value: float
    _max_target_temperature: float
    _min_target_temperature: float
    _step_target_temperature: float
    _can_set_target_temperature: bool
    _has_battery_level: bool
    _battery_level_value: float

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
        has_auto_mode: bool = False,
        has_temperature: bool = False,
        min_temperature: float = None,
        max_temperature: float = None,
        has_target_temperature: bool = False,
        can_set_target_temperature: bool = False,
        min_target_temperature: float = None,
        max_target_temperature: float = None,
        step_target_temperature: float = None,
        has_battery_level: bool = False,
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
        self._has_auto_mode = has_auto_mode
        self._has_temperature = has_temperature
        self._min_temperature = min_temperature
        self._max_temperature = max_temperature
        self._has_target_temperature = has_target_temperature
        self._can_set_target_temperature = can_set_target_temperature
        self._min_target_temperature = min_target_temperature
        self._max_target_temperature = max_target_temperature
        self._step_target_temperature = step_target_temperature
        self._has_battery_level = has_battery_level

    @staticmethod
    def build_from_api(api: HomePilotApi, did: str):
        return asyncio.run(HomePilotThermostat.async_build_from_api(api, did))

    @staticmethod
    async def async_build_from_api(api: HomePilotApi, did: str):
        """Build a new HomePilotDevice from the response of API"""
        device = await api.get_device(did)
        device_map = HomePilotDevice.get_capabilities_map(device)
        return HomePilotThermostat(
            api=api,
            did=device_map[APICAP_ID_DEVICE_LOC]["value"],
            uid=device_map[APICAP_PROT_ID_DEVICE_LOC]["value"],
            name=device_map[APICAP_NAME_DEVICE_LOC]["value"],
            device_number=device_map[APICAP_PROD_CODE_DEVICE_LOC]["value"],
            model=SUPPORTED_DEVICES[device_map[APICAP_PROD_CODE_DEVICE_LOC]["value"]][
                "name"
            ]
            if device_map[APICAP_PROD_CODE_DEVICE_LOC]["value"] in SUPPORTED_DEVICES
            else "Generic Device",
            fw_version=device_map[APICAP_VERSION_CFG]["value"]
            if APICAP_VERSION_CFG in device_map else "",
            device_group=device_map[APICAP_DEVICE_TYPE_LOC]["value"],
            has_ping_cmd=APICAP_PING_CMD in device_map,
            has_auto_mode=APICAP_AUTO_MODE_CFG in device_map,
            has_temperature=APICAP_TEMPERATURE_INT_CFG in device_map,
            min_temperature=float(
                device_map[APICAP_TEMPERATURE_INT_CFG]["min_value"]
            ) if APICAP_TEMPERATURE_INT_CFG in device_map
            and device_map[APICAP_TEMPERATURE_INT_CFG]["min_value"] is not None else None,
            max_temperature=float(
                device_map[APICAP_TEMPERATURE_INT_CFG]["max_value"]
            ) if APICAP_TEMPERATURE_INT_CFG in device_map
            and device_map[APICAP_TEMPERATURE_INT_CFG]["max_value"] is not None else None,
            has_target_temperature=APICAP_TARGET_TEMPERATURE_CFG in device_map,
            can_set_target_temperature=APICAP_TARGET_TEMPERATURE_CFG in device_map,
            min_target_temperature=float(
                device_map[APICAP_TARGET_TEMPERATURE_CFG]["min_value"]
            ) if APICAP_TARGET_TEMPERATURE_CFG in device_map
            and device_map[APICAP_TARGET_TEMPERATURE_CFG]["min_value"] is not None else None,
            max_target_temperature=float(
                device_map[APICAP_TARGET_TEMPERATURE_CFG]["max_value"]
            ) if APICAP_TARGET_TEMPERATURE_CFG in device_map
            and device_map[APICAP_TARGET_TEMPERATURE_CFG]["max_value"] is not None else None,
            step_target_temperature=float(
                device_map[APICAP_TARGET_TEMPERATURE_CFG]["step_size"]
            ) if APICAP_TARGET_TEMPERATURE_CFG in device_map
            and device_map[APICAP_TARGET_TEMPERATURE_CFG]["step_size"] is not None else None,
            has_battery_level=APICAP_BATT_VALUE_EVT in device_map,
        )

    def update_state(self, state):
        super().update_state(state)
        if self.has_temperature:
            self.temperature_value = state["statusesMap"]["acttemperatur"] / 10
        if self.has_target_temperature:
            self.target_temperature_value = state["statusesMap"]["Position"] / 10
        if self.has_auto_mode:
            self.auto_mode_value = (
                state["statusesMap"]["Manuellbetrieb"] == 0
                if "Manuellbetrieb" in state["statusesMap"]
                else False
            )
        if self.has_battery_level and "batteryStatus" in state:
            self.battery_level_value = state["batteryStatus"]

    async def async_set_target_temperature(self, temperature) -> None:
        await self.api.async_set_target_temperature(self.did, temperature)

    async def async_set_auto_mode(self, auto_mode) -> None:
        await self.api.async_set_auto_mode(self.did, auto_mode)

    @property
    def has_temperature(self) -> bool:
        return self._has_temperature

    @property
    def has_auto_mode(self) -> bool:
        return self._has_auto_mode

    @property
    def min_temperature(self) -> bool:
        return self._min_temperature

    @property
    def max_temperature(self) -> bool:
        return self._max_temperature

    @property
    def has_target_temperature(self) -> bool:
        return self._has_target_temperature

    @property
    def has_battery_level(self) -> bool:
        return self._has_battery_level

    @property
    def can_set_target_temperature(self) -> bool:
        return self._can_set_target_temperature

    @property
    def min_target_temperature(self) -> bool:
        return self._min_target_temperature

    @property
    def max_target_temperature(self) -> bool:
        return self._max_target_temperature

    @property
    def step_target_temperature(self) -> bool:
        return self._step_target_temperature

    @property
    def auto_mode_value(self) -> bool:
        return self._auto_mode_value

    @auto_mode_value.setter
    def auto_mode_value(self, auto_mode_value):
        self._auto_mode_value = auto_mode_value

    @property
    def temperature_value(self) -> float:
        return self._temperature_value

    @temperature_value.setter
    def temperature_value(self, temperature_value):
        self._temperature_value = temperature_value

    @property
    def target_temperature_value(self) -> float:
        return self._target_temperature_value

    @target_temperature_value.setter
    def target_temperature_value(self, target_temperature_value):
        self._target_temperature_value = target_temperature_value

    @property
    def battery_level_value(self) -> float:
        return self._battery_level_value

    @battery_level_value.setter
    def battery_level_value(self, battery_level_value):
        self._battery_level_value = battery_level_value
