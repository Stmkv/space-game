import asyncio


async def sleep(tics=1):
    for _ in range(tics):
        await asyncio.sleep(0)
