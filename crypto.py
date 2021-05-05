from logging import error
from requests import get

CRYPTO_URL = 'https://data.messari.io/api/v1/assets/'
HEADERS = {
    'User-Agent': 'Mozilla/5.0',
    'Content-Type': 'application/json; charset=utf-8'
}


def get_crypto_price(ticker: str) -> dict:
    '''
    Get a live stock price from COIN CAP API
    '''

    resp = get(
        CRYPTO_URL + f'{ticker}/metrics',
        headers=HEADERS,
    )

    try:
        resp.raise_for_status()
    except e:
        print(e)
        return {}

    return resp.json()
