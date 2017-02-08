import asyncio as aio
import aiohttp
import json
import wiki
import table


async def main(loop):
    async with aiohttp.ClientSession(loop=loop,
                                     connector=aiohttp.TCPConnector(limit=100)) as session:
        food, crafts = await aio.gather(
            wiki.get_items_all_categories(session, wiki.food_categories),
            wiki.get_items_all_categories(session, wiki.crafts_categories)
        )
    with open('food.json', 'w') as fd:
        json.dump(food, fd)
    with open('crafts.json', 'w') as fd:
        json.dump(crafts, fd)
    table.components_csv('food.csv', food)
    table.components_csv('crafts.csv', crafts)


if __name__ == '__main__':
    loop = aio.get_event_loop()
    loop.run_until_complete(main(loop))
