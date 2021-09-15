import sys
import asyncio
import logging
import time
from bleak import BleakScanner
from bleak.exc import BleakError
from intelino.trainlib_async import Train, TrainMsg
from intelino.trainlib_async.train_ble_device import TrainBleDevice
from intelino.trainlib_async.drivers.bleak_driver import BleakDriver


async def run(address: str, debug=False):
    log = logging.getLogger(__name__)
    log.setLevel(logging.DEBUG if debug else logging.INFO)
    h = logging.StreamHandler(sys.stdout)
    h.setLevel(logging.DEBUG)
    log.addHandler(h)

    device = await BleakScanner.find_device_by_address(address, timeout=5.0)
    if not device:
        raise BleakError(f"A device with address {address} could not be found.")

    driver = BleakDriver(device)
    train_device = TrainBleDevice(driver)
    train = Train(train_device)

    await train.connect()

    log.info(f"{time.time():.3f} Connected: {train.is_connected}")

    def callback_handler(msg: TrainMsg):
        log.debug(f"{time.time():.3f} Received {msg.raw_packet}")

    train.notifications.subscribe(callback_handler)

    log.info(f"{time.time():.3f} Drive medium speed forward")
    await train.send_command(0xB8, [0x01, 0x02, 0x01])

    log.info(f"{time.time():.3f} Setting color to RED...")
    color = [0xFF, 0, 0]
    await train.send_command(0xB4, [0x06, *color, *color])
    log.debug(f"{time.time():.3f} Setting color to RED DONE")

    await asyncio.sleep(3.0)

    log.info(f"{time.time():.3f} Setting color to GREEN...")
    color = [0, 0xFF, 0]
    await train.send_command(0xB4, [0x06, *color, *color])
    log.debug(f"{time.time():.3f} Setting color to GREEN DONE")

    await asyncio.sleep(3.0)

    log.info(f"{time.time():.3f} Setting color to BLUE...")
    color = [0, 0, 0xFF]
    await train.send_command(0xB4, [0x06, *color, *color])
    log.debug(f"{time.time():.3f} Setting color to BLUE DONE")

    await asyncio.sleep(3.0)

    log.info(f"{time.time():.3f} Stopping the train")
    await train.send_command(0xB9, [0x01])

    log.info(f"{time.time():.3f} Stopping notifications and disconnecting")
    await train.disconnect()
    log.info(f"{time.time():.3f} Done")


if __name__ == "__main__":
    address = "33AA542E-1452-4525-8DB8-7BC941A7FE49"
    loop = asyncio.get_event_loop()
    loop.set_debug(True)
    loop.run_until_complete(run(address, True))
    loop.close()
