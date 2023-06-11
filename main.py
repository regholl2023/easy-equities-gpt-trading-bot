import json
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import yfinance as yf
from datetime import datetime
from core.easy_equities import EasyEquities
from core.gpt import GPTBot
from core.news import get_news

# import env vaiables from env.py
# before using this program you need to
# create a file called "env.py" and put in your details:
# EASY_EQUITIES = {'user_name': 'user_name', 'password': 'password'}
# OPEN_AI_API_KEY = 'banana360kickflip'
# MARKETAUX_API_KEY = 'your_marketaux_api_key'
from env import EASY_EQUITIES, OPEN_AI_API_KEY


# Get Day Number from weekday
weekno = datetime.today().weekday()

# dont run if it is a weekend
if weekno < 5:
    print("Today is a Weekday")
else:
    # 5 Sat, 6 Sun
    print("Today is a Weekend")
    exit(0)


# make the driver
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
driver.get("https://platform.easyequities.io/")

# init Easy Equities class
ee = EasyEquities(driver, EASY_EQUITIES['user_name'], EASY_EQUITIES['password'], 'EasyEquities USD')
# login
ee.login()
# load the account type, in this case we are using the EasyEquities USD account
ee.load_account_type()

# get all the current open positions
open_positions = ee.get_positions()
# updating open positions can take time
# so we only update the open positions when neccisary
update_positions = False

# some stocks that I want to focus on, later on when I sign up for the
# news api I can add many more stocks
# ideally we would load a bunch of stocks in here but it
# costs quite a bit for the news api subscription.
target_symbols = ['AAPL', 'MSFT', 'GOOGL', 'NVDA', 'TSM', 'META', 'AVGO', 'AMD']

# add in the existing positions incase we need to close them
for key in open_positions:
    if key not in target_symbols:
        target_symbols.append(key)

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
    df = ticker.history(period='1mo')[map(str.title, ['open', 'close', 'low', 'high', 'volume'])]

    # get the ammount of money we can spend / have avalable in the account
    balance = ee.get_balance()

    # compile the stock info to feed into gpt
    stock_info = {
        "news": json.dumps(news_item),
        "price_history": df.Close.values,
        "open_position": symbol in open_positions.keys(),
        "capital": balance,
    }

    # add in the position info if there is an open position
    if stock_info['open_position']:
        stock_info['opening_amount'] = open_positions[symbol]['purchase_amount']
        stock_info['current_amount'] = open_positions[symbol]['current_amount']

    # get gpt to make a decision for us
    decision = gpt_Bot.make_trading_decision(stock_info)

    # execute decision
    if not stock_info['open_position'] and decision['buy']:

        if balance < 20:
            print('Not enough money, skipping purchase')
            continue

        if decision['buy'] >= balance:
            print('gpt tried to spend more money than we said it should.')
            decision['buy'] = balance * 0.1

        # buy the stock if gpt says so
        print(f"buying {symbol}")
        ee.buy_stock(symbol, decision['buy'])
        update_positions = True

    # sell the stock if we have an open position and if gpt says so
    elif stock_info['open_position'] and decision['sell']:
        print(f"selling {symbol}")
        ee.sell_position(symbol)
        update_positions = True

    print(f"message from gpt:\n{decision['message']}\n")

    # update open positions if necessary
    if update_positions:
        open_positions = ee.get_positions()
        update_positions = False