import asyncio as aio
import aiohttp
import wiki


async def main(loop):
    async with aiohttp.ClientSession(loop=loop) as session:
        return await wiki.get_foods(session)


if __name__ == '__main__':
    loop = aio.get_event_loop()
    print(loop.run_until_complete(main(loop)))
