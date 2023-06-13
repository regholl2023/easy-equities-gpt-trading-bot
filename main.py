import json
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import yfinance as yf
from datetime import datetime
from core.easy_equities import EasyEquities
from core.alpaca import AlpacaTrading
from core.gpt import GPTBot
from core.news import get_news

# import env vaiables from env.py
# before using this program you need to
# create a file called "env.py" and put in your details:
# ALPACA_API_KEY = 'banana360kickflip'
# ALPACA_SECRET_KEY = 'banana360kickflip'
# OPEN_AI_API_KEY = 'banana360kickflip'
# todo: make marketaux a class instead
# MARKETAUX_API_KEY = 'your_marketaux_api_key'
from env import ALPACA_API_KEY, ALPACA_SECRET_KEY, OPEN_AI_API_KEY


# Get Day Number from weekday
weekno = datetime.today().weekday()

# dont run if it is a weekend
if weekno < 5:
    print("Today is a Weekday")
else:
    # 5 Sat, 6 Sun
    print("Today is a Weekend")
    exit(0)


# init AlpacaTrading
alpaca = AlpacaTrading(api_key=ALPACA_API_KEY, api_secret=ALPACA_SECRET_KEY, paper=True)

# get all the current open positions
open_positions = alpaca.get_positions()
# updating open positions can take time
# so we only update the open positions when neccisary
update_positions = False

# get the ammount of money we can spend / have avalable in the account
balance = alpaca.get_available_cash()
original_balance = balance

# some stocks that I want to focus on, later on when I sign up for the
# news api I can add many more stocks
# ideally we would load a bunch of stocks in here but it
# costs quite a bit for the news api subscription.
target_symbols = ['AAPL', 'MSFT', 'GOOGL', 'NVDA', 'TSM', 'META', 'AVGO', 'AMD']

# add in the existing positions incase we need to close them
for position in open_positions:
    target_symbols.append(position["symbol"])

# get the news for all the symbols
news_items = get_news(target_symbols)

# initalise the GPT decision maker
gpt_Bot = GPTBot(OPEN_AI_API_KEY)

# loop through each news item
for news_item in news_items:

    symbol = news_item['stock']
    print(f"processing {symbol}")

    # get the stock info from yahoo finance
    ticker = yf.Ticker(symbol)
    # then get a dataframe
    df = ticker.history(period='5d', interval='15m')[map(str.title, ['open', 'close', 'low', 'high', 'volume'])]

    

    # get the position if there is one
    position = False
    for _position in open_positions:
        if _position['symbol'] == symbol:
            position = _position
            break

    
    # compile the stock info to feed into gpt
    stock_info = {
        "news": json.dumps(news_item),
        "price_history": df.Close.values,
        "open_position": position is not False,
        "capital": balance,
    }

    # add in the position info if there is an open position
    if position is not False:
        stock_info['opening_price'] = position['avg_entry_price']
        stock_info['current_price'] = position['current_price']

    # get gpt to make a decision for us
    decision = gpt_Bot.make_trading_decision(stock_info)

    # execute decision
    if position is not False and decision['buy']:

        if balance < 20:
            print('Not enough money, skipping purchase')
            continue

        if decision['buy'] >= balance:
            print('gpt tried to spend more money than we said it should.')
            decision['buy'] = original_balance * 0.1

        # buy the stock if gpt says so
        print(f"buying {symbol}")
        alpaca.buy(symbol=symbol, notional=decision['buy'], take_profit=decision['take_profit'], stop_price=decision['stop_price'])
        update_positions = True

    # sell the stock if we have an open position and if gpt says so
    elif stock_info['open_position'] and decision['sell']:
        print(f"selling {symbol}")
        alpaca.sell(symbol=symbol, percentage=decision['percentage'])
        update_positions = True

    print(f"message from gpt:\n{decision['message']}\n")

    # update open positions if necessary
    if update_positions:
        balance = alpaca.get_available_cash()
        open_positions = alpaca.get_positions()
        update_positions = False