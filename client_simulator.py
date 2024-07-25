import asyncio
import json
import math
import os

import numpy as np
import matplotlib.pyplot as plt

def getColorFromSin(idx):
    b = math.sin(0.6 * idx + 0) / 2 + 0.75
    g = math.sin(0.6 * idx + 2) / 2 + 0.75
    r = math.sin(0.6 * idx + 4) / 2 + 0.75
    return r, g, b

async def recvFmt(reader) -> bytes or None:
    try:
        header = await reader.readline()
        msg = await reader.readexactly(int(header.decode("ascii")))
    except Exception as e:
        print(e)
        return None
    return msg


def sendFmt(writer: asyncio.StreamWriter, string) -> None:
    try:
        header = bytes(str(len(string)) + '\n', 'ascii')
        writer.write(header)
        writer.write(bytes(string, 'ascii'))

    except Exception as e:
        print(e)


async def main():
    reader, writer = await asyncio.open_connection('127.0.0.1', 12345)
    sendFmt(writer, "associator_output")
    print("connected")

    path = "/home/wangyize/mocap/data/cad_main6/many_people/output/keypoints3d"
    files = os.listdir(path)
    files.sort()
    while True:
        for file in files:
            with open(os.path.join(path, file), "r") as f:
                s = f.read()
                sendFmt(writer, s)

            await asyncio.sleep(0.04)


if __name__ == "__main__":
    asyncio.run(main())
