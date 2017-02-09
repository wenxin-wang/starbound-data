# Starbound Data

Generate Starbound game data, collected from [wiki](http://starbounder.org).

## Product Information

I want to know which product is best for selling in terms of unit selling price, production rate, etc.

The `.csv` and `.xls` files are the resuling data, as of 2017-02-09. `crafts.xls` are data for all craftables, while `food.xls` only contains data for food and drinks. That is because I'm especially concerned with food and drinks.

## Running the script

Requirements:

- Python 3.6
- aiohttp
- BeautifulSoup4

Use `venv` if needed. Install the requirements first with:

```bash
pip install -r requirements
```

Then run the script with

```bash
python main.py
```
