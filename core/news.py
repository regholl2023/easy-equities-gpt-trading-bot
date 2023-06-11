import http.client, urllib.parse
import json
from collections import defaultdict
import sys
sys.path.append('..')
from env import MARKETAUX_API_KEY


def get_news_limited(symbol):
    """gets the raw news from marketaux in its raw form

    Args:
        symbol: the symbol you want to get the news from

    Returns:
        a list of processed news items
    """

    conn = http.client.HTTPSConnection('api.marketaux.com')

    params = urllib.parse.urlencode({
            'api_token': MARKETAUX_API_KEY,
            'symbols': symbol,
            'limit': 100,
        })

    conn.request('GET', '/v1/news/all?{}'.format(params))

    res = conn.getresponse()
    data = res.read()

    news_items = json.loads(data.decode('utf-8'))['data']

    processed_news_items = []

    # proccess the items
    for news_item in news_items:
        processed_news_items.append(
                process_news(news_item, symbol)
            )
    
    return processed_news_items

def condense_output(output):
    """Takes multiple news items in the fromat of what process_news returns
    and condenses them into single stock and higlights pares.
    additionaly it limits the ammount of highlist to 10 otherwise
    gpt will throw an error because the input is too long

    Args:
        output: takes in the output of the process_news items

    Returns:
        array: an array of dicts
    """
    highlights = defaultdict(list)
    return_array = []

    for item in output:
        stock = item['stock']
        for highlight in item['highlights']:
            if highlight not in highlights[stock]:
                highlights[stock].append(highlight)

    for key, value in highlights.items():
        return_array.append(
            {
                'stock': key,
                # only get the first 10 items
                'highlights': value[:10],
            }
        )

    return return_array
    

def get_news(symbols):
    """A warpper for get_news_limited, simply calls get_news_limited
    for each symbol in symbols

    Args:
        symbols: list of symbols you want news for

    Returns:
        list: list of dictionaries with symbols and news highlights
    """

    processed_news_items = []

    for symbol in symbols:
        print(symbol)
        processed_news_items.extend(
                get_news_limited(symbol)
            )
    
    condensed_output = condense_output(processed_news_items)
    # pruged_output = list(filter( lambda item: item['stock'] in symbols, condensed_output ))
    return condensed_output

def process_news(news_item, symbol = None):
    """Processes the news items into something gpt can use

    Args:
        news_item (dict): comes from the news api
        symbol (string): sometimes a difrent symbol Is used in the news item
            so setting symbol replaces the symbol to be the correct one
    
    Returns:
        dict: returns a dict of news items
    """

    highlights = []
    for entry in news_item['entities']:
        highlights.extend(
                list(map(lambda news: {"highlight": news["highlight"], "sentiment": news["sentiment"]}, entry['highlights']))
            )
    return{
        "stock": news_item['entities'][0]['symbol'] if symbol == None else symbol,
        "highlights": highlights,
    }