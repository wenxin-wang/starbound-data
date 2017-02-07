import re
import gzip
import asyncio as aio
from yarl import URL
# yarl seems to have bug in quoting, so use urllib's quote instead
from urllib.parse import quote
from bs4 import BeautifulSoup, SoupStrainer

base = 'http://starbounder.org'
api = base + '/mediawiki/api.php'

crops = '/Crops'
category = '/Category:'
category_food = category + 'Food'
food_categories = ['Food', 'Prepared_Food', 'Drink']


async def url_soup(session, url, parse_only=None):
    async with session.get(URL(base + quote(url), encoded=True)) as res:
        content = await res.text()
        print("GET %s" % url)
        soup = BeautifulSoup(content, 'html.parser',
                             parse_only=parse_only)
        return soup


async def get_item(session, name, url):
    parse_only = SoupStrainer('div', class_='infoboxwrapper')
    soup = await url_soup(session, url, parse_only)
    item = {'name': name}
    pixel_a = soup.find('a', href='/Pixel')
    item['price'] = int(pixel_a.next_sibling.string)
    ing_text_div = soup.find('div', text='INGREDIENTS')
    if ing_text_div:
        ingredients = {}
        for div in ing_text_div.next_siblings:
            if not div.name:
                continue
            a = div.a
            n = a.parent.next_sibling.div.string
            ingredients[a['href']] = int(n)
        item['ingredients'] = ingredients
    return item


async def get_category_members(session, category):
    params = {'action': 'query', 'list': 'categorymembers', 'continue': '',
              'format': 'json', 'cmprop': 'title', 'cmlimit': '500', 'cmtitle':
              'Category:' + category}
    async with session.get(api, params=params) as res:
        data = await res.json()
        print("LIST %s" % category)
        for member in data['query']['categorymembers']:
            title = member['title']
            yield title, '/' + title.replace(' ', '_')


async def get_crops_time(session, url=crops):
    harvest_re = re.compile(r"^\s*Harvest:\s*([0-9]+)\s*minutes\s*", re.I)
    parse_only = SoupStrainer(id='mw-content-text')
    soup = await url_soup(session, url, parse_only)
    tag = soup.find(id='Crop_Images_and_Average_Growth_Times')
    while tag.name != 'table':
        tag = tag.next_element
    for table in tag.find_all('table', class_='gametable'):
        a = table.find('a')
        p = table.find('p')
        yield a['href'], harvest_re.match(p.string).group(1)


async def get_food_in_category(session, category):
    urls = []
    pending = []
    async for name, url in get_category_members(session, category):
        urls.append(url)
        pending.append(aio.ensure_future(get_item(session, name, url)))
    done, _ = await aio.wait(pending, loop=session.loop)
    foods = {u:await f for u, f in zip(urls, done)}
    return foods


async def get_food_all_categories(session, categories=food_categories):
    done, _ = await aio.wait([(get_food_in_category(session, c)) for c in
                              categories], loop=session.loop)
    res = {}
    for d in done:
        res.update(await d)
    return res


async def get_foods(session, url=category_food):
    '''
    Get a list of all kind of foods
    Get harvest time for crops
    Try to get simple ingredients since ingredients may be compound
    Return a dictionary from food url to food dictionary
    '''
    urls = []
    pending = []
    for div in soup.children:
        for li in div.ul.find_all('li', recursive=False):
            a = li.a
            u = a['href']
            urls.append(u)
            pending.append(get_item(session, a.string, u))
    done, _ = await aio.wait(pending, loop=session.loop)
    foods = {u:await f for u, f in zip(urls, done)}
    return foods
