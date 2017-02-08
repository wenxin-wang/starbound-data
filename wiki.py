import re
import gzip
import asyncio as aio
from yarl import URL
# yarl seems to have bug in quoting, so use urllib's quote instead
from urllib.parse import quote, unquote
from bs4 import BeautifulSoup, SoupStrainer

base = 'http://starbounder.org'
api = base + '/mediawiki/api.php'

crops_page = '/Crops'
category = '/Category:'
category_food = category + 'Food'
food_categories = ['Food', 'Prepared_Food', 'Drink', 'Cooking Ingredient']

redirected = {}


def get_real_url(content, u):
    parse_only = SoupStrainer(id='ca-nstab-main')
    soup = BeautifulSoup(content, 'html.parser',
                         parse_only=parse_only)
    _u = unquote(soup.find('a')['href'])
    if u != _u:
        redirected[u] = _u
        return _u


async def get_content(session, url):
    async with session.get(URL(base + quote(url), encoded=True)) as res:
        return await res.text()


async def get_redirect(session, url):
    url = unquote(url)
    u = redirected.get(url)
    if u:
        return u
    content = await get_content(session, url)
    print("CHECK REDIRECT %s" % url)
    return get_real_url(content, url)


async def url_soup(session, url, parse_only=None):
    url = unquote(url)
    content = await get_content(session, url)
    print("GET %s" % url)
    soup = BeautifulSoup(content, 'html.parser',
                         parse_only=parse_only)
    return soup, get_real_url(content, url) or url


async def get_item(session, url):
    parse_only = SoupStrainer('div', class_='infoboxwrapper')
    soup, url = await url_soup(session, url, parse_only)
    item = {'url': url}
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


async def get_category_items(session, category, limit=50):
    params = {'action': 'query', 'list': 'categorymembers', 'continue': '',
              'format': 'json', 'cmprop': 'title', 'cmlimit': str(limit), 'cmtitle':
              'Category:' + category}
    while True:
        async with session.get(api, params=params) as res:
            data = await res.json()
            print("LIST %s" % category)
            for member in data['query']['categorymembers']:
                title = member['title']
                yield '/' + title.replace(' ', '_')
            cont = data.get('continue')
            if not cont:
                break
            params['cmcontinue'] = cont['cmcontinue']


async def get_items_in_category(session, category):
    pending = []
    async for url in get_category_items(session, category):
        pending.append(aio.ensure_future(get_item(session, url)))
    done, _ = await aio.wait(pending, loop=session.loop)
    items = {}
    for d in done:
        it = await d
        items[it['url']] = it
    return items


async def get_items_all_categories(session, categories):
    done, _ = await aio.wait([(get_items_in_category(session, c)) for c in
                              categories], loop=session.loop)
    res = {}
    for d in done:
        res.update(await d)
    return res


async def get_crops_time(session, url=crops_page):
    '''
    This is currently unused
    '''
    harvest_re = re.compile(r"^\s*Harvest:\s*([0-9]+)\s*minutes\s*", re.I)
    parse_only = SoupStrainer(id='mw-content-text')
    soup, _ = await url_soup(session, url, parse_only)
    tag = soup.find(id='Crop_Images_and_Average_Growth_Times')
    while tag.name != 'table':
        tag = tag.next_element
    times = {}
    for table in tag.find_all('table', class_='gametable'):
        a = table.find('a')
        p = table.find('p')
        times[a['href']] = harvest_re.match(p.string).group(1)
    return times


async def gen_food_data(session):
    '''
    This is currently unused
    Get a list of all kind of food
    Try to get simple ingredients since ingredients may be compound
    Return a dictionary from food url to food dictionary
    '''
    food, time = await aio.gather(get_food_all_categories(session),
                                  get_crops_time(session), loop=session.loop)
    for u, t in time.items():
        try:
            f = food[u]
        except KeyError as e:
            u = await get_redirect(session, u)
            if not u:
                raise e
            f = food[u]
        f['time'] = t
    return food
