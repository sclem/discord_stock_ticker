from logging import error

from requests import get

COINCAP = 'api.coincap.io/v2/assets/'
HEADERS = {
    'User-Agent': 'Mozilla/5.0',
    'accept': 'application/json',
    'Host': '123'
}


def get_crypto_price(ticker: str) -> dict:
    '''
    Get a live stock price from COIN CAP API
    '''
    print('Calling crypto api: {}'.format(ticker))

    resp = get(
        COINCAP + f'{ticker}',
        headers=HEADERS
    )

    try:
        resp.raise_for_status()
    except:
        return {}

    print('Response data: {}'.format(resp.json()))
    return resp.json()
