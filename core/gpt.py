import json
import openai

class GPTBot:
    """
    A stock trading bot that uses GPT-3.5 to make trading decisions based on given stock information.

    Usage:
        Initialize an instance of the GPTBot class with your OpenAI API key.
        Use the `make_trading_decision` method to generate a trading decision.

    Example:
        bot = GPTBot('YOUR_API_KEY')
        stock_info = {
            'news': "{'title': 'Company X announces positive earnings report'}",
            'price_history': "[100, 110, 105, 95, 100, 115, 120]",
            'open_position': True,
            'capital': 50000,
            'opening_price': 105.5,
            'current_price': 102.5,
        }
        decision = bot.make_trading_decision(stock_info)
        print(decision)

    """
    def __init__(self, api_key):
        openai.api_key = api_key

    def make_trading_decision(self, stock_info, symbol):
        """Generate a trading decision based on the given stock information.

        Args:
            api_key: your open AI api key
            stock_info (dict): stock information to be feed into gpt
                {
                    "news": (str) in json format,
                    "price_history": (list) price history in 15 min interval,
                    "open_position": (bool) is there an existing open position,
                    "capital": (float) how much money is available to spend on stocks,
                    ** if there is an open position**
                    "opening_price": (float) opening price of the position,
                    "current_price": (float) current price of the position,
                }
        
        Return:
            dict: should return a desision in this format
            {
                "buy": quantity (int) or null,
                "sell": true or null,
                "trail_percent": percentage for trailing stop loss,
                "message": "optional feed back"
            }
        """
        news = stock_info['news']
        price_history = stock_info['price_history']
        open_position = stock_info['open_position']
        opening_price = stock_info.get('opening_price')
        current_price = stock_info.get('current_price')
        capital = stock_info['capital']

        # Generate a prompt for GPT-3.5 based on the given information
        prompt = f"News for symbol {symbol}: {news}\n\nPrice History(old to new, 15 min interval): {price_history}\n\nDo we own this stock currently: {open_position}\n"
        if open_position:
            prompt += f"Opening Price: {opening_price}\nCurrent Price: {current_price}\n"
        prompt += f"\nCapital: {capital}\n\n"
        # looks like you can only do full shares when doing trailing stop
        # prompt += "note: fractional shares is allowed, you dont need to buy a full share\n"
        # if fractional is not allowed for trailing stop orders then this line is useless as well
        # prompt += "note: you cannot exceed the capital amount, rather buy smaller ammount (fractional), also keep in mind good risk managmant\n"
        prompt += "note: do not spend all money on one stock!\n"
        # this line can easly be checked for on client side
        # prompt += "note: you may only spend a maximum amount of 10% of the capital amount\n"
        prompt += "note: trail_percent default is generally 6.0 (which is 6%), you can choose whatever value is appropriate\n"
        prompt += """based on the given information Please suggest the best trading decision in this JSON format:\n
{
    "buy": quantity (int) or null,
    "sell": true or null,
    "trail_percent": percentage_for_trailing_stop_loss,
    "message": "optional feed back"
}

note: only return valid JSON
"""

        print(f"prompt: {prompt}")

        # Generate a completion using GPT-3.5
        keep_trying = True
        response = None
        while keep_trying:
            try:
                response = openai.Completion.create(
                    engine="text-davinci-003",
                    prompt=prompt,
                    max_tokens=64,
                    n=1,
                    stop=None,
                    temperature=0.7
                )
                keep_trying = False
            except Exception as error:
                print(error)
                print('failed to get answer from gpt')
                keep_trying = True

        print(response.choices[0].text)

        # Parse the response and extract the trading decision
        decision = self._parse_trading_decision(response.choices[0].text)

        print(f"decision: {decision}")

        return decision



    def _parse_trading_decision(self, decision_text):
        """Parse the trading decision from the given text.

        Args:
            decision_text (str): The text containing the trading decision.

        Returns:
            dict: A dictionary representing the trading decision with 'buy' and 'sell' amounts.

        """

        try:
            # fix the json if gpt adds any extra charaters
            arr = list(decision_text)

            while arr[0] != '{':
                arr.pop(0)

            while arr[-1] == ' ':
                arr.pop(-1)
            
            if  arr[-1] != '}':
                arr.append('"}')

            decision_text = ''.join(arr)

            result = json.loads(decision_text)
            return result
        except:
            # perfaps the json is malfromed
            raise Exception(decision_text)
