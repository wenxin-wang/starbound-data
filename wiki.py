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
crafts_categories = ['Crafting materials', 'Craftables']
ignore_categories = ['Removed', 'Disabled']

headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:51.0) Gecko/20100101 Firefox/51.0'}

redirected = {}
cache = {}


def get_real_url(soup, u):
    _u = unquote(soup.find(id='ca-nstab-main').find('a')['href'])
    redirected[u] = _u
    return _u


def should_ignore(soup):
    ul = soup.find(id='mw-normal-catlinks').ul
    for li in ul.find_all('li', recursive=False):
        if li.a.string.strip() in ignore_categories:
            return True
    return False


async def get_soup(session, url, parse_only=None):
    await aio.sleep(0.1)
    async with session.get(URL(base + quote(url), encoded=True), headers=headers) as res:
        content = await res.text()
    return BeautifulSoup(content, 'html.parser',
                         parse_only=parse_only)


async def url_soup(session, url, parse_only=None):
    soup = await get_soup(session, url, parse_only)
    print("GET %s" % url)
    return soup, get_real_url(soup, url)


def get_price(infobox):
    pixel_a = infobox.find('a', href='/File:Pixels-Sell.png')
    if pixel_a:
        return int(pixel_a.parent.get_text())
    pixel_img = infobox.find('img', alt='Pixels-Sell.png')
    if pixel_img:
        return int(pixel_img.parent.get_text())
    pixel_a = infobox.find('a', href='/Pixel')
    return int(pixel_a.next_sibling.string)


async def _get_item(session, url):
    soup, url = await url_soup(session, url)
    if should_ignore(soup):
        return None, url
    item = {'name': url[1:], 'url': url}
    pixel_a = None
    infobox = soup.find('div', class_='infoboxwrapper')
    item['price'] = get_price(infobox)
    ing_text_div = infobox.find('div', text='INGREDIENTS')
    if ing_text_div:
        ingredients = {}
        for div in ing_text_div.next_siblings:
            if not div.name:
                continue
            a = div.a
            n = a.parent.next_sibling.div.string
            ingredients[a['href']] = int(n)
        item['ingredients'] = ingredients
    return item, url


async def get_item(session, url):
    # Since async is single threaded,
    # only await statements are interrupted
    url = unquote(url)
    url = redirected.get(url, url) # this could be redirected url
    f = cache.get(url)
    if not f:
        f = aio.ensure_future(_get_item(session, url))
        cache[url] = f
    it, url = await f

    _f = cache.get(url) # Direct entry
    # If direct entry doesn't exist, use redirected.
    # Redirected is never used when direct entry exists.
    # Else cache[url] already points to the direct one
    if not _f:
        cache[url] = f # Direct url must haven't been queried yet
    elif _f != f:
        it, _ = await _f
    return it


async def get_category_urls(session, category, limit=50):
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
    soup, _ = await url_soup(session, url)
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
