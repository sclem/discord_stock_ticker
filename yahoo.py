from logging import error

from requests import get

import sys
import json

YAHOO_URL = 'https://query1.finance.yahoo.com/v10/finance/'
HEADERS = {
    'User-Agent': 'Mozilla/5.0',
    'accept': 'application/json'
}


def get_stock_price(ticker: str) -> dict:
    '''
    Get a live stock price from YF API
    '''

    resp = get(
        YAHOO_URL + f'quoteSummary/{ticker}?modules=price',
        headers=HEADERS
    )

    try:
        resp.raise_for_status()
    except e:
        print(e)
        return {}

    return resp.json()

if __name__ == "__main__":
    print(json.dumps(get_stock_price(sys.argv[1])))
