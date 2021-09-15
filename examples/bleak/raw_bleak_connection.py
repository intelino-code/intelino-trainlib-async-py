import sys
import asyncio
import logging
import time
from bleak import BleakClient, BleakScanner
from bleak.exc import BleakError


COMMAND_CHARACTERISTIC = "40c540d0-344c-4d0d-a1da-9cc260b82d43"
RESPONSE_CHARACTERISTIC = "a4b80869-a84c-4160-a3e0-72fa58ff480e"


async def run(address: str, debug=False):
    log = logging.getLogger(__name__)
    log.setLevel(logging.DEBUG if debug else logging.INFO)
    h = logging.StreamHandler(sys.stdout)
    h.setLevel(logging.DEBUG)
    log.addHandler(h)

    device = await BleakScanner.find_device_by_address(address, timeout=5.0)
    if not device:
        raise BleakError(f"A device with address {address} could not be found.")

    async with BleakClient(device) as client:
        log.info(f"{time.time():.3f} Connected: {client.is_connected}")

        def callback_handler(_: int, data: bytearray):
            content = ":".join(["{:02x}".format(x) for x in data])
            log.debug(f"{time.time():.3f} Received {content}")

        await client.start_notify(RESPONSE_CHARACTERISTIC, callback_handler)

        log.info(f"{time.time():.3f} Drive medium speed forward")
        cmd = bytearray([0xB8, 0x03, 0x01, 0x02, 0x01])
        await client.write_gatt_char(COMMAND_CHARACTERISTIC, cmd, True)

        log.info(f"{time.time():.3f} Setting color to RED...")
        color = [0xFF, 0, 0]
        cmd = bytearray([0xB4, 0x07, 0x06, *color, *color])
        await client.write_gatt_char(COMMAND_CHARACTERISTIC, cmd, True)
        log.debug(f"{time.time():.3f} Setting color to RED DONE")

        await asyncio.sleep(3.0)

        log.info(f"{time.time():.3f} Setting color to GREEN...")
        color = [0, 0xFF, 0]
        cmd = bytearray([0xB4, 0x07, 0x06, *color, *color])
        await client.write_gatt_char(COMMAND_CHARACTERISTIC, cmd, True)
        log.debug(f"{time.time():.3f} Setting color to GREEN DONE")

        await asyncio.sleep(3.0)

        log.info(f"{time.time():.3f} Setting color to BLUE...")
        color = [0, 0, 0xFF]
        cmd = bytearray([0xB4, 0x07, 0x06, *color, *color])
        await client.write_gatt_char(COMMAND_CHARACTERISTIC, cmd, True)
        log.debug(f"{time.time():.3f} Setting color to BLUE DONE")

        await asyncio.sleep(3.0)

        log.info(f"{time.time():.3f} Stopping the train")
        cmd = bytearray([0xB9, 0x01, 0x01])
        await client.write_gatt_char(COMMAND_CHARACTERISTIC, cmd, True)

        log.info(f"{time.time():.3f} Stopping notifications")
        await client.stop_notify(RESPONSE_CHARACTERISTIC)
        log.info(f"{time.time():.3f} Disconnecting")
        await client.disconnect()
        log.info(f"{time.time():.3f} Done")


if __name__ == "__main__":
    address = "33AA542E-1452-4525-8DB8-7BC941A7FE49"
    loop = asyncio.get_event_loop()
    loop.set_debug(True)
    loop.run_until_complete(run(address, True))
    loop.close()
