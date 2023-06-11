# Stock Trading Bot with GPT-3 Integration

The Stock Trading Bot is an intelligent automated system designed to assist in making trading decisions based on real-time stock information and news updates. Leveraging the power of OpenAI's GPT-3.5 language model, the bot analyzes stock-related news from marketaux.com and other sources, providing valuable insights to aid in decision-making.

The bot takes into account various factors, including the latest news about a specific stock, its past price history, the trader's available capital, and the current status of their trading account. Additionally, it considers whether the trader has an open position on the given stock, along with the opening value and current value of the stock.

Using this comprehensive information, the Stock Trading Bot communicates with GPT-3.5 to generate well-informed trading decisions. GPT-3.5 processes the data and provides the bot with suggested actions, such as buying or selling a specific quantity of shares.

Once the trading decision is received from GPT-3.5, the bot executes the action through automation using the Selenium library in Python. It securely logs into the trader's Easy Equities account, a popular online trading platform, and performs the necessary actions on the web page, such as placing orders or closing positions.

The integration of GPT-3.5 with the Stock Trading Bot brings cutting-edge natural language processing capabilities to the world of algorithmic trading. By combining real-time news analysis with historical price data and the trader's account information, the bot provides personalized and data-driven trading recommendations.

This project showcases the potential of artificial intelligence in financial decision-making and highlights the power of automation in executing trading actions seamlessly. The Stock Trading Bot not only assists traders in making informed decisions but also saves time and effort by automating the execution process.

With its ability to process vast amounts of information and generate intelligent insights, the Stock Trading Bot represents an innovative solution for traders seeking an edge in the dynamic and fast-paced world of stock trading.

## Create a file env.py file with the following:
EASY_EQUITIES = {'user_name': 'user_name', 'password': 'password'}

OPEN_AI_API_KEY = 'your_openai_api_key'

MARKETAUX_API_KEY = 'your_marketaux_api_key'

then create a Python virtual environment called env and install requirements.txt with
pip install -r requirements.txt

then you can run the program by dobble clicking on the run.bat