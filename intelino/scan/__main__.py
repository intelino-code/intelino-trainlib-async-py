#!/usr/bin/env python3
#
# Copyright 2021 Innokind, Inc. DBA Intelino
#
# Licensed under the Intelino Public License Agreement, Version 1.0 located at
# https://intelino.com/intelino-public-license.
# BY INSTALLING, DOWNLOADING, ACCESSING, USING OR DISTRIBUTING ANY OF
# THE SOFTWARE, YOU AGREE TO THE TERMS OF SUCH LICENSE AGREEMENT.

"""BLE scanning utility to find nearby intelino trains."""

import asyncio
from typing import List
from bleak import BleakScanner
from bleak.backends.device import BLEDevice
from intelino.trainlib_async import TrainScanner, Train


async def print_info_card(train: Train, full: bool = True):
    print(f'{"="*40}')
    print(f'{"Train info":^40s}')
    print(f'{"="*40}')
    print(f'{"Advertised name":<15s}{train.name:>25s}')
    print(f'{"ID":<4s}{train.id:>36s}')
    print(f'{"="*40}')

    if not full:
        return

    # any further information requires the train to be connected
    if not train.is_connected:
        await train.connect()

    msg = await train.get_mac_address()
    print(f'{"MAC address":<15s}{msg.mac_address:>25s}')

    msg = await train.get_uuid()
    print(f'{"UUID":<15s}{msg.uuid:>25s}')

    msg = await train.get_version_info()
    print(f'{"FW version":<15s}{str(msg.fw_version):>25s}')
    print(f'{"BLE API version":<15s}{str(msg.ble_api_version):>25s}')

    msg = await train.get_stats_lifetime_odometer()
    print(f'{"Odometer":<15s}{msg.lifetime_odometer_meters:18.2f} meters')

    print(f'{"="*40}')


async def train_scan(timeout: float):
    # find all trains (search for max 2 seconds)
    trains = await TrainScanner(timeout=timeout).get_trains(
        connect=False,
    )

    # inspect them one by one
    for train in trains:
        await print_info_card(train, full=True)
        await train.disconnect()

    if len(trains) == 0:
        print("No trains found.")


def list_devices(title: str, devices: List[BLEDevice]) -> None:
    print(f"{title} ({len(devices)}):")
    for d in devices:
        print(f"{d.address} : {d.name} (RSSI {d.rssi})")


async def general_scan(timeout: float) -> None:
    devices = await BleakScanner.discover(timeout)

    trains = list(filter(lambda d: d.name.startswith("intelino"), devices))
    others = list(filter(lambda d: not d.name.startswith("intelino"), devices))

    list_devices("Trains", trains)
    print()
    list_devices("Others", others)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Start BLE scanning and discover nearby devices.",
        prog="python3 -m intelino.scan",
    )
    parser.add_argument(
        "-t",
        "--time",
        default=3,
        type=int,
        help="how long to scan in seconds (default: 3 seconds)",
    )
    parser.add_argument(
        "-i",
        "--info",
        action="store_true",
        help="connect to each train and display more info",
    )
    args = parser.parse_args()

    if not args.info:
        asyncio.run(general_scan(args.time))
    else:
        asyncio.run(train_scan(args.time))
