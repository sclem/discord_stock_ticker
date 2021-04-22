import os
import re

import discord
from yahoo import get_stock_price

client = discord.Client()

TARGET_CHANNEL = os.getenv('DISCORD_CHANNEL_ID')

STOCK_REGEX = "\\b([A-Z]{3,5})\\b"
prog = re.compile(STOCK_REGEX)

whitelist_users = os.getenv('DISCORD_USER_IDS').split(',')


def get_price(ticker):
    try:
        market_data = get_stock_price(ticker)
        result = market_data['quoteSummary']['result'][0]
        price = result['price']['regularMarketPrice']['fmt']
        return price
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
    if str(message.author.id) not in whitelist_users:
        print('{} is not whitelisted'.format(message.author.name))
        return

    tickers = prog.findall(message.content)
    data = []
    for t in tickers:
        price = get_price(t)
        if price:
            data.append({
                'ticker': t,
                'price': price
            })
    if len(data) == 0:
        return
    out_msg = '<@{}>\n'.format(message.author.id)
    for d in data:
        out_msg += '{} is ${}\n'.format(d['ticker'], d['price'])
    print('sending: \n{}'.format(out_msg))
    await message.channel.send(out_msg)


TOKEN = os.getenv('DISCORD_TOKEN')
client.run(TOKEN)
