import os
import re
from datetime import datetime
from pytz import timezone, utc

import discord
from discord.ext import commands
from yahoo import get_stock_price
from crypto import get_crypto_price
from dotenv import load_dotenv
from find_tickers import find_stonks

load_dotenv()

COMMAND_PREFIX = '!'
TARGET_CHANNEL = os.getenv('DISCORD_CHANNEL_ID')
TARGET_ROLE = os.getenv('DISCORD_ROLE_ID')
bot = commands.Bot(command_prefix=COMMAND_PREFIX)
eastern_tz = timezone('America/New_York')

print('checking for role {}'.format(TARGET_ROLE))


def get_price(ticker):
    symbol = ''
    if ticker == 'BTC' or ticker == 'ETH' or ticker == 'DOGE':
        symbol = ticker

    if symbol != '':
        try:
            market_data = get_crypto_price(symbol)
            result = market_data['data']['market_data']
            price = result['price_usd']
            percentChange = result['percent_change_usd_last_24_hours']
            return [price, percentChange], True
        except:
            return None, False
    else:
        try:
            market_data = get_stock_price(ticker)
            result = market_data['quoteSummary']['result'][0].get('price', {})
            price = result.get('regularMarketPrice', {}).get('raw', 0)
            percent = result.get('regularMarketChangePercent', {}).get('raw', 0) * 100.0
            premarketPrice = result.get('preMarketPrice', {}).get('raw', 0)
            premarketPercent = result.get('preMarketChangePercent', {}).get('raw', 0) * 100.0
            postmarketPrice = result.get('postMarketPrice', {}).get('raw', 0)
            postmarketPercent = result.get('postMarketChangePercent', {}).get('raw', 0) * 100.0
            marketOpen = result.get('regularMarketOpen', {}).get('raw', 0)
            dayHigh = result.get('regularMarketDayHigh', {}).get('raw', 0)
            dayLow = result.get('regularMarketDayLow', {}).get('raw', 0)
            marketVolume = result.get('regularMarketVolume', {}).get('fmt', '')
            marketCap = result.get('marketCap', {}).get('fmt', '')
            return [price, percent, premarketPrice, premarketPercent, postmarketPrice, postmarketPercent, marketOpen, dayHigh, dayLow, marketVolume, marketCap], False
        except Exception as e:
            print('failed to get stock price for {}, {}'.format(ticker, e))
            return None, False


@bot.event
async def on_ready():
    print('we have logged in as {0.user}'.format(bot))


@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    if str(message.channel.id) != TARGET_CHANNEL:
        return
    if len(TARGET_ROLE) > 0:
        has_role = False
        for role in message.author.roles:
            if str(role.id) == TARGET_ROLE:
                has_role = True
                break
        if not has_role:
            print('{} does not have role'.format(message.author.name))
            return
    if message.content.startswith(COMMAND_PREFIX):
        await bot.process_commands(message)
        return

    market_status = get_market_status()
    tickers = find_stonks(message.content, dedup=True)
    data = []
    for t in tickers:
        ticker_data, is_crypto = get_price(t)
        if ticker_data:
            # yahoo
            if not is_crypto:
                [price, percent, premarketPrice, premarketPercent, postmarketPrice, postmarketPercent,
                    marketOpen, dayHigh, dayLow, marketVolume, marketCap] = ticker_data
                price_data = price
                percent_data = percent
                if market_status == "premarket":
                    price_data = premarketPrice
                    percent_data = premarketPercent
                elif market_status == "postmarket":
                    price_data = postmarketPrice
                    percent_data = postmarketPercent
                data.append({
                    'ticker': t,
                    'price': "{:.2f}".format(price_data),
                    'percent': "{:.2f}".format(percent_data),
                })
            # crypto
            else:
                [price, percentChange] = ticker_data
                data.append({
                    'ticker': t,
                    'price': "{:.2f}".format(price),
                    'percent': "{:.2f}".format(percentChange)
                })
    if len(data) == 0:
        return
    out_msg = '<@{}>\n'.format(message.author.id)

    for d in data:
        out_msg += '{} is ${} ({}%)\n'.format(d['ticker'], d['price'], d['percent'])
    print('sending: \n{}'.format(out_msg))
    await message.channel.send(out_msg)


def get_market_status():
    [open_time, close_time] = get_market_times_utc()
    if datetime.utcnow() < open_time:
        return "premarket"
    elif datetime.utcnow() > close_time:
        return "postmarket"
    else:
        return "open"


def get_market_times_utc():
    now = datetime.now()
    open_time = datetime(now.year, now.month, now.day, 9, 30)
    open_time = eastern_tz.localize(
        open_time, is_dst=None).astimezone(utc).replace(tzinfo=None)
    close_time = datetime(now.year, now.month, now.day, 16, 0)
    close_time = eastern_tz.localize(
        close_time, is_dst=None).astimezone(utc).replace(tzinfo=None)
    return [open_time, close_time]


@bot.command(name='stats')
async def stats(ctx, command):
    check_ticker = command
    if not check_ticker or len(check_ticker) == 0:
        print('no ticker')
        return
    elif check_ticker.startswith('$'):
        check_ticker = check_ticker[1:]

    market_status = get_market_status()
    out_msg = '{} is '.format(check_ticker)
    ticker_data, is_crypto = get_price(check_ticker)
    if not ticker_data:
        await ctx.send('cannot find {}'.format(check_ticker))
        return
    # extended yahoo data
    if not is_crypto:
        [price, percent, premarketPrice, premarketPercent, postmarketPrice, postmarketPercent,
            marketOpen, dayHigh, dayLow, marketVolume, marketCap] = ticker_data
        if market_status == "premarket":
            out_msg += '${} ({:.2f}%) (premarket)\n'.format(premarketPrice, premarketPercent)
        elif market_status == "postmarket":
            out_msg += '${} ({:.2f}%) (postmarket)\n'.format(postmarketPrice, postmarketPercent)
        else:
            out_msg += '${} ({:.2f}%)\n'.format(price, percent)
        out_msg += 'Market Open is ${:.2f}\n'.format(marketOpen)
        out_msg += 'Day High is ${:.2f}\n'.format(dayHigh)
        out_msg += 'Day Low is ${:.2f}\n'.format(dayLow)
        out_msg += 'Market Volume is {}\n'.format(marketVolume)
        out_msg += 'Market Cap is {}\n'.format(marketCap)
    else:
        out_msg += 'no stats for {}'.format(check_ticker)

    print('sending: \n{}'.format(out_msg))
    await ctx.send(out_msg)


@bot.command(name='report')
async def report(ctx, command):
    check_ticker = None
    if len(ctx.message.mentions) == 0:
        check_ticker = command
        if len(check_ticker) == 0:
            print('no ticker')
            return
        elif check_ticker.startswith('$'):
            check_ticker = check_ticker[1:]
    # scan messages for ticker ref
    async with ctx.message.channel.typing():
        market_status = get_market_status()
        [open_time, close_time] = get_market_times_utc()
        out_msg = ''
        if check_ticker:
            ticker_data, is_crypto = get_price(check_ticker)
            if not ticker_data:
                await ctx.send('cannot find {}'.format(check_ticker))
                return
            # valid ticker, get mentions
            ticker_map = dict()
            count = 0
            async for msg in ctx.message.channel.history(before=close_time, after=open_time):
                if msg.author == bot.user:
                    continue
                if msg.content.startswith(COMMAND_PREFIX):
                    continue

                tickers = find_stonks(msg.content)
                for t in tickers:
                    if not t in ticker_map:
                        ticker_map[t] = 0
                    ticker_map[t] += 1

            if check_ticker in ticker_map:
                count = ticker_map[check_ticker]
            out_msg += 'During market hours today, {} has been mentioned {} times\n'.format(
                check_ticker, count)
        else:
            # user report
            target_user = ctx.message.mentions[0]
            ticker_map = dict()
            async for msg in ctx.message.channel.history(before=close_time, after=open_time):
                if msg.author != target_user:
                    continue
                if msg.content.startswith(COMMAND_PREFIX):
                    continue
                tickers = find_stonks(msg.content)
                for t in tickers:
                    if not t in ticker_map:
                        ticker_map[t] = 0
                    ticker_map[t] += 1

            ticker_map_sorted = dict(
                sorted(ticker_map.items(), key=lambda item: item[1], reverse=True))
            out_msg += 'During market hours today, <@{}> has mentioned:\n'.format(
                target_user.id)
            count = 0

            for k, v in ticker_map_sorted.items():
                ticker_data, is_crypto = get_price(k)
                # make sure valid
                if ticker_data:
                    count += 1
                    plural = ''
                    if v > 1:
                        plural = 's'
                    out_msg += '{} {} time{}\n'.format(k, v, plural)

            if count == 0:
                out_msg = '<@{}> is a gay bear'.format(target_user.id)

        print('sending: \n{}'.format(out_msg))
        await ctx.send(out_msg)

TOKEN = os.getenv('DISCORD_TOKEN')
bot.run(TOKEN)
