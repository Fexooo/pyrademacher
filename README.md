# pyrademacher

Python Library to read/control devices connected to your Rademacher HomePilot (or Start2Smart) hub.

This library uses the latest REST API, so you must update your hub to the latest firmware if you want to use this library.

## Installation

Use pip to install pyrademacher lib:
```bash
pip install pyrademacher
```

## Usage

### API Class

With the HomePilotApi class you can acess the REST API directly:

```python
from customHomepilot.api import HomePilotApi

api = HomePilotApi("hostname", "password")  # password can be empty if not defined ("")

print(asyncio.run(asyncio.run(api.get_devices())))  # get all devices

asyncio.run(api.async_open_cover(did=1))  # open cover for device id 1 (assuming it's a cover device)
```

### Manager Class

You can use the HomePilotManager helper class to more easily manage the devices:

```python
import asyncio
from customHomepilot.manager import HomePilotManager
from customHomepilot.api import HomePilotApi

api = HomePilotApi("hostname", "password")  # password can be empty if not defined ("")

manager = asyncio.run(HomePilotManager.async_build_manager(api))
asyncio.run(manager.update_states())

print(manager.devices["1"].is_closed)
print(manager.devices["1"].cover_position)

print(manager.devices["-1"].fw_version)  # ID -1 is reserved for the hub itself
```
Each device in manager.devices is an instance of the specific device class.
