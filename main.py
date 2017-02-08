import asyncio as aio, aiohttp
import json

import wiki, table


async def main(loop):
    async with aiohttp.ClientSession(loop=loop,
                                     connector=aiohttp.TCPConnector(limit=20)) as session:
        #print(await wiki._get_item(session,'/Heart_Wreath'))
        tables = {
            'food': aio.ensure_future(table.process_categories(session, wiki.food_categories)),
            'crafts': aio.ensure_future(table.process_categories(session, wiki.crafts_categories)),
        }
        for n, t in tables.items():
            simple, compound, components = await t
            #with open(n + '.json', 'w') as fd:
            #    json.dump({'simple': simple, 'compound': compound}, fd)
            table.components_csv(n + '.csv', simple, compound, components)


if __name__ == '__main__':
    loop = aio.get_event_loop()
    loop.run_until_complete(main(loop))
