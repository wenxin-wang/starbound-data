import asyncio
import re
import gzip
from urllib.request import urlopen
from bs4 import BeautifulSoup, SoupStrainer

SELL_RATIO = 0.2
site = mwclient.Site(('http', 'starbounder.org'), path = '/mediawiki/')
wiki_url = 'http://starbounder.org'
crops_url = '/Crops'
category_url = wiki_url + '/Category:'
food_categories = ['Food', 'Prepared_Food', 'Drink']


def url_soup(url, parse_only=None):
    with urlopen(url) as res:
        content = res.read()
        if res.info().get('Content-Encoding') == 'gzip':
            content = gzip.decompress(content)
        soup = BeautifulSoup(content.decode('utf-8'), 'html.parser',
                             parse_only=parse_only)
    return soup


def get_food(name, rel_url, wiki=wiki_url):
    soup = url_soup(wiki + rel_url, SoupStrainer('div', class_='infoboxwrapper'))
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


def get_crops_time(rel_url=crops_url, wiki=wiki_url):
    harvest_re = re.compile(r"^\s*Harvest:\s*([0-9]+)\s*minutes\s*", re.I)
    soup = url_soup(wiki + rel_url, SoupStrainer(id='mw-content-text'))
    tag = soup.find(id='Crop_Images_and_Average_Growth_Times')
    while tag.name != 'table':
        tag = tag.next_element
    crops_time = {}
    for table in tag.find_all('table', class_='gametable'):
        a = table.find('a')
        p = table.find('p')
        crops_time[a['href']] = harvest_re.match(p.text).group(1)
    return crops_time


def get_food_from_category(name):
    site.Pages[]


def get_foods(rel_url=category_food, wiki=wiki_url):
    soup = url_soup(wiki + rel_url, SoupStrainer('div', class_='mw-category-group'))
    print('GET %s' % rel_url)
    threads = {}
    for div in soup.children:
        for li in div.ul.find_all('li', recursive=False):
            a = li.a
            threads[a['href']] = gevent.spawn(get_food, a.string, a['href'])
    gevent.joinall(threads.values())
    foods = {u:t.value for u,t in threads.items()}
    return foods


import mwclient
site = mwclient.Site(('http', 'starbounder.org'), path = '/mediawiki/')
