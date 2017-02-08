import asyncio as aio
import aiohttp
import json
import wiki


async def main(loop):
    async with aiohttp.ClientSession(loop=loop) as session:
        #return await wiki.get_crops_time(session)
        #return await wiki.get_item(session, '/Cotton')
        #return await wiki.get_item(session, '/Bolt_O\'s')
        #return await wiki.get_items_in_category(session, 'Food')

        #return await wiki.get_redirect(session, '/Cotton')
        #return await wiki.gen_food_data(session)
        return await wiki.get_items_all_categories(session, wiki.food_categories)


if __name__ == '__main__':
    loop = aio.get_event_loop()
    food = loop.run_until_complete(main(loop))
    with open('food.json', 'w') as fd:
        json.dump(food, fd)
    print(food)
