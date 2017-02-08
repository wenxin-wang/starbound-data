import asyncio as aio
import aiohttp
import json
import wiki
import table


async def main(loop):
    async with aiohttp.ClientSession(loop=loop,
                                     connector=aiohttp.TCPConnector(limit=20)) as session:
        food = await wiki.get_items_all_categories(session, wiki.food_categories)
    with open('food.json', 'w') as fd:
        json.dump(food, fd)
    table.components_csv('food.csv', food)


if __name__ == '__main__':
    loop = aio.get_event_loop()
    loop.run_until_complete(main(loop))
