from bleak import BleakClient
import asyncio
import random


COMMAND_CHARACTERISTIC = "40c540d0-344c-4d0d-a1da-9cc260b82d43"
RESPONSE_CHARACTERISTIC = "a4b80869-a84c-4160-a3e0-72fa58ff480e"


async def train_program(address: str):
    print(f"starting train program {address}")
    async with BleakClient(address, timeout=5.0) as client:

        def callback(sender: int, data: bytearray):
            print(address, data)

        try:
            await client.start_notify(RESPONSE_CHARACTERISTIC, callback)

            print(f"drive medium speed forward")
            cmd = bytearray([0xB8, 0x03, 0x01, 0x02, 0x01])
            await client.write_gatt_char(COMMAND_CHARACTERISTIC, cmd, True)

            for i in range(10):
                print(f"setting color...")
                color = [random.randint(0, 1) * 0xFF for i in range(3)]
                cmd = bytearray([0xB4, 0x07, 0x06, *color, *color])
                await client.write_gatt_char(COMMAND_CHARACTERISTIC, cmd, True)
                await asyncio.sleep(1.0)

            await client.stop_notify(RESPONSE_CHARACTERISTIC)

            print(f"stop movement")
            cmd = bytearray([0xB9, 0x01, 0x01])
            await client.write_gatt_char(COMMAND_CHARACTERISTIC, cmd, True)

            print(f"disconnecting from {address}")

        except Exception as e:
            print(e)


async def main():
    addresses = [
        "33AA542E-1452-4525-8DB8-7BC941A7FE49",
        "CD3C3305-36E2-4DE7-94F3-EC7FFF59E1F8",
    ]
    await asyncio.gather(*(train_program(address) for address in addresses))


if __name__ == "__main__":
    asyncio.run(main())
