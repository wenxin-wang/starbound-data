# Starbound Data

Generate Starbound game data, collected from [wiki](http://starbounder.org).

## Product Information

I want to know which product is best for selling in terms of unit selling price, production rate, etc.

Currently only food and drinks are considered, since I'm still in an early stage of game play.

## Running the script

The csv files are the resuling data, so you probably don't have to run the script yourself.

Requirements:

- Python 3.5
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
