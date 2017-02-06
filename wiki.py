import re
import gzip
import asyncio as aio
from bs4 import BeautifulSoup, SoupStrainer

SELL_RATIO = 0.2
wiki_url = 'http://starbounder.org'
crops_url = '/Crops'
category_url = '/Category:'
category_food = category_url + 'Food'
food_categories = ['Food', 'Prepared_Food', 'Drink']


async def url_soup(session, url, parse_only=None):
    async with session.get(url) as res:
        content = await res.text()
        soup = BeautifulSoup(content, 'html.parser',
                             parse_only=parse_only)
        return soup


async def get_food(session, name, rel_url, wiki=wiki_url):
    parse_only = SoupStrainer('div', class_='infoboxwrapper')
    soup = await url_soup(session, wiki + rel_url, parse_only)
    food = {'name': name}
    price_text_div = soup.find('div', text='Common')
    food['sell'] = int(price_text_div.next_sibling.text) * SELL_RATIO
    ing_text_div = soup.find('div', text='INGREDIENTS')
    print("GET %s" % rel_url)
    if ing_text_div:
        ingredients = {}
        for div in ing_text_div.next_siblings:
            if not div.name:
                continue
            ingredients[div.a['href']] = 1
            food['ingredients'] = ingredients
    return food


async def get_crops_time(rel_url=crops_url, wiki=wiki_url):
    harvest_re = re.compile(r"^\s*Harvest:\s*([0-9]+)\s*minutes\s*", re.I)
    parse_only = SoupStrainer(id='mw-content-text')
    soup = await url_soup(wiki + rel_url, parse_only)
    tag = soup.find(id='Crop_Images_and_Average_Growth_Times')
    while tag.name != 'table':
        tag = tag.next_element
        crops_time = {}
    for table in tag.find_all('table', class_='gametable'):
        a = table.find('a')
        p = table.find('p')
        crops_time[a['href']] = harvest_re.match(p.text).group(1)
    return crops_time


async def get_foods(session, rel_url=category_food, wiki=wiki_url):
    parse_only = SoupStrainer('div', class_='mw-category-group')
    soup = await url_soup(session, wiki + rel_url, parse_only)
    print('GET %s' % rel_url)
    urls = []
    pending = []
    for div in soup.children:
        for li in div.ul.find_all('li', recursive=False):
            a = li.a
            u = a['href']
            urls.append(u)
            pending.append(get_food(session, a.string, u))
    done, _ = await aio.wait(pending)
    foods = {u:await f for u, f in zip(urls, done)}
    return foods
