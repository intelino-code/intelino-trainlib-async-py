#!/usr/bin/env python3
"""BLE scanning utility to find nearby intelino trains."""

import asyncio
from typing import List
from bleak import BleakScanner
from bleak.backends.device import BLEDevice


def list_devices(title: str, devices: List[BLEDevice]) -> None:
    print(f"{title} ({len(devices)}):")
    for d in devices:
        print(f"{d.address} : {d.name} (RSSI {d.rssi})")


async def scan(timeout: float) -> None:
    devices = await BleakScanner.discover(timeout)

    trains = list(filter(lambda d: str(d.name).startswith("intelino"), devices))
    others = list(filter(lambda d: not str(d.name).startswith("intelino"), devices))

    list_devices("Trains", trains)
    print()
    list_devices("Others", others)


def main():
    asyncio.run(scan(2))


if __name__ == "__main__":
    main()
