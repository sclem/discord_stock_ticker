import os
import re

import discord
from yahoo import get_stock_price

client = discord.Client()

TARGET_CHANNEL = os.getenv('DISCORD_CHANNEL_ID')

STOCK_REGEX = "\\b([A-Z]{3,5})\\b"
prog = re.compile(STOCK_REGEX)

TARGET_ROLE = os.getenv('DISCORD_ROLE_ID')

print('checking for role {}'.format(TARGET_ROLE))


def get_price(ticker):
    try:
        market_data = get_stock_price(ticker)
        result = market_data['quoteSummary']['result'][0]
        price = result['price']['regularMarketPrice']['fmt']
        percent = result['price']['regularMarketChangePercent']['fmt']
        return [price, percent]
    except:
        return None


@client.event
async def on_ready():
    print('we have logged in as {0.user}'.format(client))


@client.event
async def on_message(message):
    if message.author == client.user:
        return
    if str(message.channel.id) != TARGET_CHANNEL:
        return
    has_role = False
    for role in message.author.roles:
        if str(role.id) == TARGET_ROLE:
            has_role = True
            break
    if not has_role:
        print('{} does not have role'.format(message.author.name))
        return

    tickers = prog.findall(message.content)
    # dedup
    tickers = list(dict.fromkeys(tickers))
    data = []
    for t in tickers:
        ticker_data = get_price(t)
        if ticker_data:
            [price, percent] = ticker_data
            data.append({
                'ticker': t,
                'price': price,
                'percent': percent
            })
    if len(data) == 0:
        return
    out_msg = '<@{}>\n'.format(message.author.id)
    for d in data:
        out_msg += '{} is ${} ({})\n'.format(d['ticker'], d['price'], d['percent'])
    print('sending: \n{}'.format(out_msg))
    await message.channel.send(out_msg)


TOKEN = os.getenv('DISCORD_TOKEN')
client.run(TOKEN)
