from csv import DictWriter


SELL_RATIO = 0.4


def _traverse(s, price, p, cur):
    used_by = p.get('used_by')
    if not used_by:
        return
    for it in used_by:
        n = cur * it['ingredients'][p['url']]
        it['components'][s] = n
        if price:
            it['ncomp'] += n
            it['raw'] += n * price
        _traverse(s, price, it, n)


def get_components(items):
    simple = []
    compound = []
    unknown = set()
    for it in items.values():
        ingredients = it.get('ingredients')
        if not ingredients:
            simple.append(it)
        else:
            it['components'] = {}
            it['ncomp'] = 0
            it['raw'] = 0
            try:
                for ing in ingredients.keys():
                    items[ing]['used_by'].append(it)
                compound.append(it)
            except KeyError:
                print('Unknown Ingredient %s for %s' % (ing, it['name']))
                unknown.add(ing)
    simple.sort(key=lambda s: s['price'])
    for s in simple:
        _traverse(s['name'], s['price'], s, 1)
    return simple, compound


def components_csv(name, items):
    simple, compound = get_components(items)
    with open(name, 'w') as fd:
        fieldnames = ['Item', 'Total', 'Raw', 'Unit'] + [s['name'] for s in simple]
        writer = DictWriter(fd, fieldnames=fieldnames)
        writer.writeheader()
        for s in simple:
            name = s['name']
            price = s['price'] * SELL_RATIO
            writer.writerow({'Item': name, 'Total': price, 'Unit': price,
                             'Raw': price, name: 1})
        for c in compound:
            components = c.get('components')
            price = c['price'] * SELL_RATIO
            raw = c['raw'] * SELL_RATIO
            unit = price / c['ncomp']
            row = dict(Item=c['name'], Total=price, Unit=unit, Raw=raw, **components)
            writer.writerow(row)
