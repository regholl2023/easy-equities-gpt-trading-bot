import json
import yfinance as yf
from core.alpaca import AlpacaTrading
from core.gpt import GPTBot
from core.news import News

# import env vaiables from env.py
# before using this program you need to
# create a file called "env.py" and put in your details:
# ALPACA_API_KEY = 'banana360kickflip'
# ALPACA_SECRET_KEY = 'banana360kickflip'
# OPEN_AI_API_KEY = 'banana360kickflip'
from env import ALPACA_API_KEY, ALPACA_SECRET_KEY, OPEN_AI_API_KEY

class TradingBot():
    """ Wrapper for trading to make life easyer when accesing global variables

        usage example:
            trading_bot = TradingBot()
            trading_bot.news.run()
        
        idealy this should be run with systemctl and auto restart if it fails
    """

    def __init__(self):
        # init AlpacaTrading
        self.alpaca = AlpacaTrading(api_key=ALPACA_API_KEY,
                                    api_secret=ALPACA_SECRET_KEY,
                                    paper=True)
        
        # get the ammount of money we can spend / have avalable in the account
        self.balance = self.alpaca.get_available_cash()
        self.original_balance = self.balance

        # get all the current open positions
        self.open_positions = self.alpaca.get_positions()

        # updating open positions can take time
        # so we only update the open positions when neccisary
        self.update_positions = False

        # some stocks that I want to focus on, later on when I sign up for the
        # news api I can add many more stocks
        # ideally we would load a bunch of stocks in here but it
        # costs quite a bit for the news api subscription.
        self.target_symbols = ['AAPL', 'MSFT', 'GOOGL', 'NVDA', 'TSM', 'META', 'AVGO', 'AMD', 'TSLA', 'AMZN', 'RBLX', 'ACN', 'ATVI']

        # add in the existing positions incase we need to close them
        for position in self.open_positions:
            self.target_symbols.append(position.symbol)
        
        # initalise the GPT decision maker
        self.gpt_Bot = GPTBot(OPEN_AI_API_KEY)

        # inintalise news and pass on_news
        self.news = News(api_key=ALPACA_API_KEY, api_secret=ALPACA_SECRET_KEY, target_symbols=self.target_symbols, on_news=self.on_news)


    def process_stock(self, symbol: str, news: dict=None, decision: dict=None):

        """ does processes the stock, this should be called every time news
            drops for a particular stock

            Args:
                symbol: (str) the stock symbol to process.
                news: (dict) the news for the stock, doesnt require any
                    particular structure
        """

        print(f"processing {symbol}")

        # get the stock info from yahoo finance
        ticker = yf.Ticker(symbol)
        # then get a dataframe
        dataframe = ticker.history(period='5d', interval='15m')[map(str.title, ['open', 'close', 'low', 'high', 'volume'])]

        

        # get the position if there is one
        position = False
        for _position in self.open_positions:
            if _position.symbol == symbol:
                position = _position
                break

        
        # compile the stock info to feed into gpt
        stock_info = {
            "news": json.dumps(news) if news is not None else None,
            "price_history": dataframe.Close.values,
            "open_position": position is not False,
            "capital": self.balance,
        }

        # add in the position info if there is an open position
        if position is not False:
            stock_info['opening_price'] = position.avg_entry_price
            stock_info['current_price'] = position.current_price

        # get gpt to make a decision for us
        if not decision:
            decision = self.gpt_Bot.make_trading_decision(stock_info=stock_info, symbol=symbol)

        # execute decision
        if position is False and decision['buy']:

            if self.balance < 20:
                print('Not enough money, skipping purchase')

            # this isnt valid anymore, a better sollution needs to be made
            # if decision['buy'] >= self.balance:
            #     print('gpt tried to spend more money than we said it should.')
            #     decision['buy'] = self.original_balance * 0.1

            # buy the stock if gpt says so
            print(f"buying {symbol}")

            try:
                self.alpaca.buy(symbol=symbol, qty=int(decision['buy']), trail_percent=decision['trail_percent'])
            except Exception as error:
                # must be an existing order
                print(f"problem buying {symbol}")
                print(error)

            self.update_positions = True

        # sell the stock if we have an open position and if gpt says so
        elif stock_info['open_position'] and decision['sell']:
            print(f"selling {symbol}")

            try:
                self.alpaca.sell(symbol=symbol, percentage=1)
            except Exception as error:
                # must be an existing order
                print(f"problem selling {symbol}")
                print(error)

            self.update_positions = True

        print(f"message from gpt:\n{decision['message']}\n")

        # update open positions if necessary
        if self.update_positions:
            self.balance = self.alpaca.get_available_cash()
            self.open_positions = self.alpaca.get_positions()
            self.update_positions = False


    def on_news(self, news):
        """ function to run when ever news drops on a particular stock

        Args:
            news: (dict) a dictionary with details from the news item.
                no particular structure is neccisary
        """

        print('got news: ', news)

        for symbol in news["symbols"]:
            # only run for our trageted symbols
            if symbol in self.target_symbols:
                self.process_stock(symbol, news)


trading_bot = TradingBot()
# trading_bot.process_stock(symbol="AAPL", news=None, decision=json.loads('{"buy": 1, "sell": null, "trail_percent": 6.0, "message": "The current news and price history for AAPL indicate positive sentiment and a potential increase in stock price. It is recommended to buy 19 shares of AAPL."}'))
# trading_bot.process_stock(symbol="TSLA", news=None, decision={'buy': None, 'sell': True, 'trail_percent': 1.0, 'message': 'It is recommended to sell the NVDA stock.'})
trading_bot.news.run()


