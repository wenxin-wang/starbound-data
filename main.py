import asyncio as aio
import aiohttp
import json
import wiki


async def main(loop):
    async with aiohttp.ClientSession(loop=loop) as session:
        #async for u, t in wiki.get_crops_time(session):
        #    print(u, t)
        #return await wiki.get_item(session, 'B', '/Bolt_O\'s')
        #return await wiki.get_item(session, 'B', '/Tropical_Punch')
        #return await wiki.get_food_in_category(session, 'Prepared Food')

        return await wiki.get_food_all_categories(session)


if __name__ == '__main__':
    loop = aio.get_event_loop()
    foods = loop.run_until_complete(main(loop))
    with open('food.json', 'w') as fd:
        json.dump(foods, fd)
