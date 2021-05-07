from logging import error
from requests import get

CRYPTO_URL = 'https://data.messari.io/api/v1/assets/'
HEADERS = {
    'User-Agent': 'Mozilla/5.0',
    'Content-Type': 'application/json; charset=utf-8'
}
CRYPTO_LIST_URL = 'https://data.messari.io/api/v2/assets?fields=symbol'


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
    except Exception as e:
        print(e)
        return {}

    return resp.json()

def list_all_crypto():
    limit = 200
    page = 0
    crypto_map = {}
    done = False
    while not done:
        page += 1
        resp = get(CRYPTO_LIST_URL + f'&page={page}&limit={limit}')

        try:
            resp.raise_for_status()
        except Exception as e:
            print(e)
            done = True
            break

        data_list = resp.json().get('data', [])
        for ticker in data_list:
            symbol = ticker.get('symbol')
            if symbol:
                crypto_map[symbol] = True
        # end loop when we get back less than limit
        done = len(data_list) < limit
    
    return crypto_map
