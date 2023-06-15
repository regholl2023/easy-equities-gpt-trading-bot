import json
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import yfinance as yf
from datetime import datetime
from core.easy_equities import EasyEquities
from core.alpaca import AlpacaTrading
from core.gpt import GPTBot
from core.news import News
import sched
from time import time, sleep

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
        self.target_symbols = ['AAPL', 'MSFT', 'GOOGL', 'NVDA', 'TSM', 'META', 'AVGO', 'AMD']

        # add in the existing positions incase we need to close them
        for position in self.open_positions:
            self.target_symbols.append(position.symbol)
        
        # initalise the GPT decision maker
        self.gpt_Bot = GPTBot(OPEN_AI_API_KEY)

        # inintalise news and pass on_news
        self.news = News(api_key=ALPACA_API_KEY, api_secret=ALPACA_SECRET_KEY, on_news=self.on_news)


    def process_stock(self, symbol: str, news: dict=None):

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
            stock_info['opening_price'] = position['avg_entry_price']
            stock_info['current_price'] = position['current_price']

        # get gpt to make a decision for us
        decision = self.gpt_Bot.make_trading_decision(stock_info)

        # execute decision
        if position is False and decision['buy']:

            if self.balance < 20:
                print('Not enough money, skipping purchase')

            if decision['buy'] >= self.balance:
                print('gpt tried to spend more money than we said it should.')
                decision['buy'] = self.original_balance * 0.1

            # buy the stock if gpt says so
            print(f"buying {symbol}")

            try:
                self.alpaca.buy(symbol=symbol, notional=decision['buy'], trail_percent=decision['trail_percent'])
            except Exception as error:
                # must be an existing order
                print(error)

            self.update_positions = True

        # sell the stock if we have an open position and if gpt says so
        elif stock_info['open_position'] and decision['sell']:
            print(f"selling {symbol}")

            try:
                self.alpaca.sell(symbol=symbol, percentage=decision['percentage'])
            except Exception as error:
                # must be an existing order
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

# inintalise news and pass on_news
news = News(api_key=ALPACA_API_KEY, api_secret=ALPACA_SECRET_KEY, on_news=trading_bot.on_news)
message = '[{"T":"n","id":32862733,"headline":"China ETFs Climb On Hopes Of Better US Relations As State Department Confirms Blinken\\u0026#39;s Beijing Visit","summary":" ","author":"Natan Ponieman","created_at":"2023-06-14T19:22:02Z","updated_at":"2023-06-14T19:33:21Z","url":"https://www.benzinga.com/markets/asia/23/06/32862733/china-etfs-climb-on-hopes-of-better-us-relations-as-state-department-confirms-blinkens-beijing-visit","content":"\\u003cp\\u003eHope is building up across the Pacific as U.S. Secretary of State \\u003cstrong\\u003eAntony Blinken\\u003c/strong\\u003e prepares for a highly anticipated visit to \\u003ca href=\\"https://www.benzinga.com/topic/china\\"\\u003eChina later this week\\u003c/a\\u003e.\\u003c/p\\u003e\\n\\n\\n\\n\\u003cp\\u003eThe Department of State confirmed Blinken\'s diplomatic trip, which will span from Friday to the following Wednesday and will also include a brief visit to the U.K.\\u003c/p\\u003e\\n\\n\\n\\n\\u003cp\\u003eOfficial communications state Blinken will meet with \\"senior PRC officials where he will discuss the importance of maintaining open lines of communication.\\"\\u003c/p\\u003e\\n\\n\\n\\n\\u003cp\\u003eBlinken\'s visit, which will be his first in five years and a first in his current role, was slated to occur in February but got suspended after the two countries entered a feud over the \\u003ca href=\\"https://www.benzinga.com/markets/asia/23/02/30712293/us-china-tensions-rise-as-secretary-of-state-cancels-high-stakes-visit-after-suspected-surveillance\\"\\u003eunauthorized appearance of a Chinese surveillance balloon over U.S. soil\\u003c/a\\u003e.\\u003c/p\\u003e\\n\\n\\n\\n\\u003cp\\u003eChina said the event had no aggressive intentions and happened by accident: a weather surveillance balloon was blown off course. \\u003ca href=\\"https://www.benzinga.com/news/23/02/30973295/blinken-meets-with-chinas-top-diplomat-on-balloon-incursion-no-credible-explanation-provided\\"\\u003eBlinken met top Chinese diplomat \\u003cstrong\\u003eWang Yi\\u003c/strong\\u003e in Germany\\u003c/a\\u003e after the balloon incident, where he also raised other matters including China\'s involvement in the Russian invasion of Ukraine.\\u003c/p\\u003e\\n\\n\\n\\n\\u003cp\\u003eU.S.-China tensions have been on the rise in the first half of the year. The two countries\' conflicts as natural competitors in the global economic arena have led to several points of friction.\\u003c/p\\u003e\\n\\n\\n\\n\\u003cp\\u003eThe sovereignty of Taiwan, \\u003ca href=\\"https://www.benzinga.com/general/23/05/32428707/china-warns-it-will-resolutely-smash-taiwan-independence-as-us-bolsters-support\\"\\u003ea country that China claims as part of its own territory\\u003c/a\\u003e and whose independence is of strategic importance for the U.S., has become central \\u003ca href=\\"https://www.benzinga.com/news/23/04/31930916/taiwan-reportedly-urges-us-to-tone-down-chip-rhetoric-amid-china-invasion-fears\\"\\u003eto the escalating rhetoric of both nations\\u003c/a\\u003e. Taiwan is home to \\u003cstrong\\u003eTaiwan Semiconductor Manufacturing Company\\u003c/strong\\u003e (NASDAQ:\\u003ca class=\\"ticker\\" href=\\"https://www.benzinga.com/stock/TSM#NASDAQ\\"\\u003eTSM\\u003c/a\\u003e), which produces the world\'s most advanced microchips, as well as many other companies in the semiconductor sector.\\u003c/p\\u003e\\n\\n\\n\\n\\u003cp\\u003eBoth Beijing and Washington have launched measures aimed at hampering the other country\'s ability to \\u003ca href=\\"https://www.benzinga.com/news/23/03/31515648/are-us-sanctions-on-china-working-china-tech-etfs-paint-a-picture\\"\\u003edominate the semiconductor supply chain\\u003c/a\\u003e, which could turn out a key to maintaining global influence in the near future as chips become a commodity used in almost every product, from refrigerators to cars and military equipment.\\u003c/p\\u003e\\n\\n\\n\\n\\u003cp\\u003eYet both countries continue to rely on each other a lot more than they would prefer. Despite\\u003cstrong\\u003e \\u003ca href=\\"https://www.benzinga.com/markets/asia/23/05/32431478/china-tensions-are-top-of-mind-for-bidens-weeklong-asia-tour-we-are-not-going-to-arm-twist\\"\\u003ePresident\\u003c/a\\u003e\\u003c/strong\\u003e\\u003ca href=\\"https://www.benzinga.com/markets/asia/23/05/32431478/china-tensions-are-top-of-mind-for-bidens-weeklong-asia-tour-we-are-not-going-to-arm-twist\\"\\u003e \\u003cstrong\\u003eJoe Biden\\u003c/strong\\u003e\'s call to \\"decouple\\" from China\'s economy\\u003c/a\\u003e at the latest G7 meeting, China and the U.S. continue to be each other\'s largest trading partners. Total U.S. goods and services imports from China reached a new record in 2022 at $564 billion, \\u003ca href=\\"https://apps.bea.gov/international/bp_web/tb_download_type_modern.cfm?list=1\\u0026amp;RowID=30164\\"\\u003eas per\\u003c/a\\u003e the Bureau of Economic Analysis.\\u003c/p\\u003e\\n\\n\\n\\n\\u003cp\\u003eThe U.S. position has since slowly \\u003ca href=\\"https://www.benzinga.com/news/23/04/32069698/us-aligning-with-europe-over-china-favors-de-risking-over-decoupling-says-top-biden-administration-o\\"\\u003emoved to align with Europe\'s strategy of \\"de-risk\\" but not \\"decouple\\"\\u003c/a\\u003e from China.\\u003c/p\\u003e\\n\\n\\n\\n\\u003cp\\u003eThese and other issues are expected to come up in Blinken\'s upcoming meeting in Beijing with China\'s Foreign Minister \\u003cstrong\\u003eQin Gang\\u003c/strong\\u003e. The Department of State said Blinken will raise \\"bilateral issues of concern, global and regional matters, and potential cooperation on shared transnational challenges.\\" According to the Washington Post, Chinese President\\u003cstrong\\u003e Xi Jinping \\u003c/strong\\u003ecould also be present at the meetings.\\u003c/p\\u003e\\n\\n\\n\\n\\u003cp\\u003eThe ability to establish fluid communications between the two countries\' militaries is also key, as a failure to interpret routine military actions in the Pacific as aggression could plunge the two countries into a much dreaded and easily preventable military clash.\\u003c/p\\u003e\\n\\n\\n\\n\\u003cp\\u003eOn a Wednesday preliminary phone call with Qin Gang, Blinken raised \\"the importance of maintaining open lines of communication\\" to \\"avoid miscalculation and conflict,\\" in the management of U.S.-China relations.\\u003c/p\\u003e\\n\\n\\n\\n\\u003cp\\u003eYet, according to a communication by China\'s Foreign Ministry, Qin urged the U.S. to \\"stop interfering in China\'s internal affairs\\" and \\"stop undermining China\'s sovereignty, security and development interests in the name of competition.\\"\\u003c/p\\u003e\\n\\n\\n\\n\\u003cp\\u003eThe Chinese official\'s wordings continue to showcase a looming air of distrust for U.S. behavior overseas.\\u0026nbsp;\\u003c/p\\u003e\\n\\n\\n\\n\\u003cp\\u003eLate last month, the Pentagon said it \\"believes strongly in the importance of maintaining open lines of military-to-military communication between Washington and Beijing to ensure that competition does not veer into conflict.\\"\\u003c/p\\u003e\\n\\n\\n\\n\\u003cp\\u003e\\u003cstrong\\u003eChina ETFs reacted positively to the confirmation of Blinken\'s visit.\\u003c/strong\\u003e\\u003c/p\\u003e\\n\\n\\n\\n\\u003cul\\u003e\\n\\u003cli\\u003e\\u003cstrong\\u003eiShares MSCI China ETF\\u003c/strong\\u003e (NASDAQ:\\u003ca class=\\"ticker\\" href=\\"https://www.benzinga.com/stock/MCHI#NASDAQ\\"\\u003eMCHI\\u003c/a\\u003e) is up 1.5% on Wednesday at the time of writing.\\u003c/li\\u003e\\n\\n\\n\\n\\u003cli\\u003e\\u003cstrong\\u003eiShares China Large-Cap ETF \\u003c/strong\\u003e(NYSE:\\u003ca class=\\"ticker\\" href=\\"https://www.benzinga.com/stock/FXI#NYSE\\"\\u003eFXI\\u003c/a\\u003e) is up 1.3%.\\u003c/li\\u003e\\n\\n\\n\\n\\u003cli\\u003e\\u003cstrong\\u003eKraneShares CSI China Internet ETF \\u003c/strong\\u003e(NYSE:\\u003ca class=\\"ticker\\" href=\\"https://www.benzinga.com/stock/KWEB#NYSE\\"\\u003eKWEB\\u003c/a\\u003e) is up 2.3%.\\u003c/li\\u003e\\n\\n\\n\\n\\u003cli\\u003e\\u003cstrong\\u003eXtrackers Harvest CSI 300 China A-Shares ETF\\u003c/strong\\u003e (NYSE:\\u003ca class=\\"ticker\\" href=\\"https://www.benzinga.com/stock/ASHR#NYSE\\"\\u003eASHR\\u003c/a\\u003e) is up 0.9%.\\u003c/li\\u003e\\n\\n\\n\\n\\u003cli\\u003e\\u003cstrong\\u003eSPDR S\\u0026amp;P China ETF\\u003c/strong\\u003e (NYSE:\\u003ca class=\\"ticker\\" href=\\"https://www.benzinga.com/stock/GXC#NYSE\\"\\u003eGXC\\u003c/a\\u003e) is up 1.6%\\u003c/li\\u003e\\n\\u003c/ul\\u003e\\n\\n\\n\\n\\u003cp\\u003e\\u003c/p\\u003e\\n\\n\\n\\n\\u003cp\\u003e\\u003cem\\u003ePhoto: Shutterstock\\u003c/em\\u003e\\u003c/p\\u003e","symbols":["ASHR","FXI","GXC","KWEB","MCHI","TSM"],"source":"benzinga"}]'
news.on_message(ws=None, message=message)
news.run()


# {
#     "buy": 1601.69,
#     "sell": null,
#     "trail_percent": 6.0,
#     "message": "Investing in China ETFs based on positive outlook of US-China relations"
# }