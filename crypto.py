from logging import error
from requests import get

COINCAP = 'https://api.coincap.io/v2/assets/'
HEADERS = {
    'User-Agent': 'Mozilla/5.0',
    'Content-Type': 'application/json; charset=utf-8'
}


def get_crypto_price(ticker: str) -> dict:
    '''
    Get a live stock price from COIN CAP API
    '''

    resp = get(
        COINCAP + f'{ticker}',
        headers=HEADERS,
    )

    try:
        resp.raise_for_status()
    except e:
        print(e)
        return {}

    return resp.json()
