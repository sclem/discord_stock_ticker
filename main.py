import os
import re
from datetime import datetime
from pytz import timezone, utc

import discord
from discord.ext import commands
from yahoo import get_stock_price
from crypto import get_crypto_price
from dotenv import load_dotenv

load_dotenv()

COMMAND_PREFIX = '!'
TARGET_CHANNEL = os.getenv('DISCORD_CHANNEL_ID')
TARGET_ROLE = os.getenv('DISCORD_ROLE_ID')
STOCK_REGEX = "\\b([A-Z]{3,5})\\b"
prog = re.compile(STOCK_REGEX)
bot = commands.Bot(command_prefix=COMMAND_PREFIX)
eastern_tz = timezone('America/New_York')

print('checking for role {}'.format(TARGET_ROLE))


def get_price(ticker):
    symbol = ''
    if ticker == 'BTC':
        symbol = 'bitcoin'
    elif ticker == 'ETH':
        symbol = 'ethereum'
    elif ticker == 'DOGE':
        symbol = 'dogecoin'

    if symbol != '':
        try:
            market_data = get_crypto_price(symbol)
            result = market_data['data']
            price = result['priceUsd']
            percentChange = result['changePercent24Hr']
            return [price, percentChange]
        except:
            return None
    else:
        try:
            market_data = get_stock_price(ticker)
            result = market_data['quoteSummary']['result'][0]
            price = result['price']['regularMarketPrice']['fmt']
            percent = result['price']['regularMarketChangePercent']['fmt']
            premarketPrice = result['price']['preMarketPrice']['fmt']
            premarketPercent = result['price']['preMarketChangePercent']['fmt']

            postmarketPrice = ''
            if 'fmt' in result['price']['postMarketPrice']:
                postmarketPrice = result['price']['postMarketPrice']['fmt']

            postmarketPercent = ''
            if 'fmt' in result['price']['postMarketChange']:
                postmarketPercent = result['price']['postMarketChange']['fmt']

            marketOpen = result['price']['regularMarketOpen']['fmt']
            dayHigh = result['price']['regularMarketDayHigh']['fmt']
            dayLow = result['price']['regularMarketDayLow']['fmt']
            marketVolume = result['price']['regularMarketVolume']['fmt']
            marketCap = result['price']['marketCap']['fmt']
            return [price, percent, premarketPrice, premarketPercent, postmarketPrice, postmarketPercent, marketOpen, dayHigh, dayLow, marketVolume, marketCap]
        except:
            return None


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

    tickers = prog.findall(message.content)
    # dedup
    tickers = list(dict.fromkeys(tickers))
    data = []
    for t in tickers:
        ticker_data = get_price(t)
        if ticker_data and len(ticker_data) > 2:
            [price, percent, premarketPrice, premarketPercent, postmarketPrice, postmarketPercent,
                marketOpen, dayHigh, dayLow, marketVolume, marketCap] = ticker_data
            data.append({
                'ticker': t,
                'price': price,
                'percent': percent,
                'premarketPrice': premarketPrice,
                'premarketPercent': premarketPercent,
                'postmarketPrice': postmarketPrice,
                'postmarketPercent': postmarketPercent,
                'marketOpen': marketOpen,
                'dayHigh': dayHigh,
                'dayLow': dayLow,
                'marketVolume': marketVolume,
                'marketCap': marketCap
            })
        elif ticker_data and len(ticker_data) <= 2:
            [price, percentChange] = ticker_data
            data.append({
                'ticker': t,
                'price': price,
                'percentChange': percentChange
            })
    if len(data) == 0:
        return
    out_msg = '<@{}>\n'.format(message.author.id)
    market_status = get_market_status()

    for d in data:
        if len(d) == 3:
            out_msg += '{} is ${:.2f} (${:.2f})\n\n'.format(d['ticker'], float(d['price']), float(d['percentChange']))
        else:
            out_msg += '{} is ${} ({})\n'.format(d['ticker'], d['price'], d['percent'])
            if market_status == "premarket":
                out_msg += 'PreMarket Price is ${} ({})\n'.format(d['premarketPrice'], d['premarketPercent'])
            elif market_status == "postmarket":
                out_msg += 'PostMarket Price is ${} ({})\n'.format(d['postmarketPrice'], d['postmarketPercent'])
            else:
                out_msg += 'Market Open is ${}\n'.format(d['marketOpen'])
            out_msg += 'Day High is ${}\n'.format(d['dayHigh'])
            out_msg += 'Day Low is ${}\n'.format(d['dayLow'])
            out_msg += 'Market Volume is {}\n'.format(d['marketVolume'])
            out_msg += 'Market Cap is {}\n\n'.format(d['marketCap'])
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


@bot.command(name='report')
async def report(ctx, command):
    check_ticker = None
    if len(ctx.message.mentions) == 0:
        check_ticker = command
        if len(check_ticker) == 0:
            print('no ticker')
            return
    # scan messages for ticker ref
    async with ctx.message.channel.typing():
        [open_time, close_time] = get_market_times_utc()
        out_msg = ''
        if check_ticker:
            ticker_data = get_price(check_ticker)
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

                tickers = prog.findall(msg.content)
                for t in tickers:
                    if not t in ticker_map:
                        ticker_map[t] = 0
                    ticker_map[t] += 1

            if check_ticker in ticker_map:
                count = ticker_map[check_ticker]
            out_msg += 'During market hours today, {} has been mentioned {} times'.format(
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
                tickers = prog.findall(msg.content)
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
                ticker_data = get_price(k)
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
