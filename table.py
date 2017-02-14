import asyncio as aio
from csv import DictWriter
from collections import defaultdict
import wiki

SELL_RATIO = 1


async def process_item(session, url):
    item = await wiki.get_item(session, url)
    if not item or 'components' in item:
        return item

    ingredients = item.get('ingredients')
    if ingredients:
        ingf = []
        for u, n in ingredients.items():
            f = process_item(session, u)
            ingf.append((aio.ensure_future(f), n))
        comps = defaultdict(int)
        ncomp = 0
        raw = 0
        for f, n in ingf:
            it = await f
            for u, m in it['components'].items():
                comps[u] += n * m
        for u, n in comps.items():
            p = (await wiki.get_item(session, u))['price']
            ncomp += n
            raw += n * p
        item['components'] = comps
        item['ncomp'] = ncomp
        item['raw'] = raw
    else:
        item['components'] = {item['url']: 1}
        item['ncomp'] = 1
        item['raw'] = item['price']
    return item


async def process_category(session, category):
    pending = []
    async for url in wiki.get_category_urls(session, category):
        f = process_item(session, url)
        pending.append(aio.ensure_future(f))
    return pending


async def process_categories(session, categories):
    pending = []
    for c in categories:
        f = process_category(session, c)
        pending.append(aio.ensure_future(f))
    items = [await f for c in pending for f in await c if await f]
    items.sort(key=lambda s: s['price'])
    simple = []
    compound = []
    components = set()
    for item in items:
        components.update(item['components'])
        if 'ingredients' in item:
            compound.append(item)
        else:
            simple.append(item)
    components = list(components)
    components.sort()
    return simple, compound, components


def components_csv(name, simple, compound, components):
    with open(name, 'w') as fd:
        fieldnames = ['Item', 'Total', 'Raw', 'Rise', 'Unit'] + components
        writer = DictWriter(fd, fieldnames=fieldnames)
        writer.writeheader()
        for items in [simple, compound]:
            for it in items:
                price = it['price'] * SELL_RATIO
                raw = it['raw'] * SELL_RATIO
                rise = '{:.2%}'.format(price / raw) if raw > 0 else 'x'
                unit = price / it['ncomp']
                components = it['components']
                row = dict(Item=it['url'], Total=price, Raw=raw, Rise=rise,
                           Unit=unit, **components)
                writer.writerow(row)
