import hashlib
from typing import Any

import aiohttp
from aiohttp import ClientConnectorError
from aiohttp.abc import AbstractCookieJar
from .const import (
    APICAP_AUTO_MODE_CFG,
    APICAP_GOTO_POS_CMD,
    APICAP_PING_CMD,
    APICAP_POS_DOWN_CMD,
    APICAP_POS_UP_CMD,
    APICAP_STOP_CMD,
    APICAP_TARGET_TEMPERATURE_CFG,
    APICAP_TURN_OFF_CMD,
    APICAP_TURN_ON_CMD,
    APICAP_SET_SLAT_POS_CMD,
    APICAP_STOP_SLAT_CMD
)


class HomePilotApi:
    _host: str
    _password: str
    _authenticated: bool = False
    _cookie_jar: Any = None

    def __init__(self, host, password) -> None:
        self._host = host
        self._password = password

    @staticmethod
    async def test_connection(host: str) -> str:
        async with aiohttp.ClientSession() as session:
            try:
                response = await session.get(f"http://{host}/")
                if response.status != 200:
                    return "error"
                response = await session.post(
                    f"http://{host}/authentication/password_salt"
                )
                if response.status == 500:
                    return "ok"
                else:
                    return "auth_required"
            except ClientConnectorError:
                return "error"

    @staticmethod
    async def test_auth(host: str, password: str) -> AbstractCookieJar:
        cookie_jar = aiohttp.CookieJar(unsafe=True)
        async with aiohttp.ClientSession(cookie_jar=cookie_jar) as session:
            response = await session.post(f"http://{host}/authentication/password_salt")
            response_data = await response.json()
            if response.status == 500 and response_data["error_code"] == 5007:
                raise AuthError()
            if response.status != 200 or response_data["error_code"] != 0:
                raise CannotConnect()
            salt = response_data["password_salt"]
            hashed_password = hashlib.sha256(password.encode("utf-8")).hexdigest()
            salted_password = hashlib.sha256(
                f"{salt}{hashed_password}".encode("utf-8")
            ).hexdigest()
            response = await session.post(
                f"http://{host}/authentication/login",
                json={"password": salted_password, "password_salt": salt},
            )
            if response.status != 200:
                raise AuthError()
            return session.cookie_jar

    async def authenticate(self):
        if not self.authenticated and self.password != "":
            self.cookie_jar = await HomePilotApi.test_auth(self.host, self.password)
            self._authenticated = True

    async def get_devices(self):
        await self.authenticate()
        async with aiohttp.ClientSession(cookie_jar=self.cookie_jar) as session:
            async with session.get(f"http://{self.host}/devices") as response:
                response = await response.json()
                if response["error_code"] != 0:
                    return []
                if "payload" in response and "devices" in response["payload"]:
                    devices = response["payload"]["devices"]
                    return devices
                return []

    async def get_device(self, did):
        await self.authenticate()
        async with aiohttp.ClientSession(cookie_jar=self.cookie_jar) as session:
            async with session.get(f"http://{self.host}/devices/{did}") as response:
                response = await response.json()
                if response["error_code"] != 0:
                    return []
                if "payload" in response and "device" in response["payload"]:
                    device = response["payload"]["device"]
                    return device
                return None

    async def async_get_fw_status(self):
        await self.authenticate()
        async with aiohttp.ClientSession(cookie_jar=self.cookie_jar) as session:
            async with session.get(
                f"http://{self.host}/service/system-update-image/status"
            ) as response:
                response = await response.json()
                return response

    async def async_get_fw_version(self):
        await self.authenticate()
        async with aiohttp.ClientSession(cookie_jar=self.cookie_jar) as session:
            async with session.get(
                f"http://{self.host}/service/system-update-image/version"
            ) as response:
                response = await response.json()
                return response

    async def async_get_nodename(self):
        await self.authenticate()
        async with aiohttp.ClientSession(cookie_jar=self.cookie_jar) as session:
            async with session.get(
                f"http://{self.host}/service/system/networkmgr/v1/nodename"
            ) as response:
                response = await response.json()
                return response

    async def async_get_led_status(self):
        await self.authenticate()
        async with aiohttp.ClientSession(cookie_jar=self.cookie_jar) as session:
            async with session.get(
                f"http://{self.host}/service/system/leds/status"
            ) as response:
                response = await response.json()
                return response

    async def async_get_device_state(self, did):
        await self.authenticate()
        async with aiohttp.ClientSession(cookie_jar=self.cookie_jar) as session:
            async with session.get(
                f"http://{self.host}/v4/devices/{did}"
            ) as response:
                response = await response.json()
                if response["response"] != "get_device":
                    device = {}
                else:
                    if "device" in response:
                        device = response["device"]
                    else:
                        device = {}
                return device

    async def async_get_devices_state(self):
        await self.authenticate()
        async with aiohttp.ClientSession(cookie_jar=self.cookie_jar) as session:
            async with session.get(
                f"http://{self.host}/v4/devices?devtype=Actuator"
            ) as response:
                response = await response.json()
                if response["response"] != "get_visible_devices":
                    actuators = {}
                else:
                    if response["devices"]:
                        devices = response["devices"]
                        actuators = {str(device["did"]): device for device in devices}
                    else:
                        actuators = {}
            async with session.get(
                f"http://{self.host}/v4/devices?devtype=Sensor"
            ) as response:
                response = await response.json()
                if response["response"] != "get_meters":
                    sensors = {}
                else:
                    if response["meters"]:
                        devices = response["meters"]
                        sensors = {str(device["did"]): device for device in devices}
                    else:
                        sensors = {}
            return {**actuators, **sensors}

    async def async_ping(self, did):
        await self.authenticate()
        async with aiohttp.ClientSession(cookie_jar=self.cookie_jar) as session:
            async with session.put(
                f"http://{self.host}/devices/{did}", json={"name": APICAP_PING_CMD}
            ) as response:
                return await response.json()

    async def async_open_cover(self, did):
        await self.authenticate()
        async with aiohttp.ClientSession(cookie_jar=self.cookie_jar) as session:
            async with session.put(
                f"http://{self.host}/devices/{did}", json={"name": APICAP_POS_UP_CMD}
            ) as response:
                return await response.json()

    async def async_close_cover(self, did):
        await self.authenticate()
        async with aiohttp.ClientSession(cookie_jar=self.cookie_jar) as session:
            async with session.put(
                f"http://{self.host}/devices/{did}", json={"name": APICAP_POS_DOWN_CMD}
            ) as response:
                return await response.json()

    async def async_stop_cover(self, did):
        await self.authenticate()
        async with aiohttp.ClientSession(cookie_jar=self.cookie_jar) as session:
            async with session.put(
                f"http://{self.host}/devices/{did}", json={"name": APICAP_STOP_CMD}
            ) as response:
                return await response.json()

    async def async_set_cover_position(self, did, position):
        await self.authenticate()
        async with aiohttp.ClientSession(cookie_jar=self.cookie_jar) as session:
            async with session.put(
                f"http://{self.host}/devices/{did}",
                json={"name": APICAP_GOTO_POS_CMD, "value": position},
            ) as response:
                return await response.json()

    async def async_open_cover_tilt(self, did) -> None:
        await self.authenticate()
        async with aiohttp.ClientSession(cookie_jar=self.cookie_jar) as session:
            async with session.put(
                f"http://{self.host}/devices/{did}",
                json={"name": APICAP_SET_SLAT_POS_CMD, "value": 0},
            ) as response:
                return await response.json()

    async def async_close_cover_tilt(self, did) -> None:
        await self.authenticate()
        async with aiohttp.ClientSession(cookie_jar=self.cookie_jar) as session:
            async with session.put(
                f"http://{self.host}/devices/{did}",
                json={"name": APICAP_SET_SLAT_POS_CMD, "value": 100},
            ) as response:
                return await response.json()

    async def async_set_cover_tilt_position(self, did, position) -> None:
        await self.authenticate()
        async with aiohttp.ClientSession(cookie_jar=self.cookie_jar) as session:
            async with session.put(
                f"http://{self.host}/devices/{did}",
                json={"name": APICAP_SET_SLAT_POS_CMD, "value": position},
            ) as response:
                return await response.json()

    async def async_stop_cover_tilt(self, did) -> None:
        await self.authenticate()
        async with aiohttp.ClientSession(cookie_jar=self.cookie_jar) as session:
            async with session.put(
                f"http://{self.host}/devices/{did}",
                json={"name": APICAP_STOP_SLAT_CMD},
            ) as response:
                return await response.json()

    async def async_turn_on(self, did):
        await self.authenticate()
        async with aiohttp.ClientSession(cookie_jar=self.cookie_jar) as session:
            async with session.put(
                f"http://{self.host}/devices/{did}", json={"name": APICAP_TURN_ON_CMD}
            ) as response:
                return await response.json()

    async def async_turn_off(self, did):
        await self.authenticate()
        async with aiohttp.ClientSession(cookie_jar=self.cookie_jar) as session:
            async with session.put(
                f"http://{self.host}/devices/{did}", json={"name": APICAP_TURN_OFF_CMD}
            ) as response:
                return await response.json()

    async def async_set_target_temperature(self, did, temperature):
        await self.authenticate()
        async with aiohttp.ClientSession(cookie_jar=self.cookie_jar) as session:
            async with session.put(
                f"http://{self.host}/devices/{did}",
                json={"name": APICAP_TARGET_TEMPERATURE_CFG, "value": temperature},
            ) as response:
                return await response.json()

    async def async_set_auto_mode(self, did, auto_mode):
        await self.authenticate()
        async with aiohttp.ClientSession(cookie_jar=self.cookie_jar) as session:
            async with session.put(
                f"http://{self.host}/devices/{did}",
                json={"name": APICAP_AUTO_MODE_CFG, "value": auto_mode},
            ) as response:
                return await response.json()

    async def async_turn_led_on(self):
        await self.authenticate()
        async with aiohttp.ClientSession(cookie_jar=self.cookie_jar) as session:
            async with session.post(
                f"http://{self.host}/service/system/leds/enable"
            ) as response:
                return await response.json()

    async def async_turn_led_off(self):
        await self.authenticate()
        async with aiohttp.ClientSession(cookie_jar=self.cookie_jar) as session:
            async with session.post(
                f"http://{self.host}/service/system/leds/disable"
            ) as response:
                return await response.json()

    async def async_update_firmware(self):
        await self.authenticate()
        async with aiohttp.ClientSession(cookie_jar=self.cookie_jar) as session:
            async with session.post(
                f"http://{self.host}/service/system-update-image/startupdate"
            ) as response:
                return await response.json()

    @property
    def host(self):
        return self._host

    @property
    def password(self):
        return self._password

    @property
    def authenticated(self):
        return self._authenticated

    @property
    def cookie_jar(self):
        return self._cookie_jar

    @cookie_jar.setter
    def cookie_jar(self, cookie_jar):
        self._cookie_jar = cookie_jar


class CannotConnect(BaseException):
    """Error to indicate we cannot connect."""


class AuthError(BaseException):
    """Error to indicate an authentication error."""
