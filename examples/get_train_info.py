import asyncio
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


async def main():
    # collection of our trains
    # find all trains (search for max 2 seconds)
    trains = await TrainScanner(timeout=2.0).get_trains(
        connect=False,
    )

    # inspect them one by one
    for train in trains:
        await print_info_card(train, full=True)
        await train.disconnect()

    if len(trains) == 0:
        print("No trains found.")


if __name__ == "__main__":
    asyncio.run(main())
