from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest, TakeProfitRequest, StopLossRequest
from alpaca.trading.enums import OrderSide, TimeInForce, OrderType
from env import ALPACA_API_KEY, ALPACA_SECRET_KEY

class AlpacaTrading:
    """
    A class for performing trading operations using the Alpaca API.
    """

    def __init__(self, api_key: str, api_secret: str, paper: bool=True):
        """
        Initialize the AlpacaTrading object.

        Args:
            api_key (str): The Alpaca API key.
            api_secret (str): The Alpaca API secret key.
            base_url (str, optional): The Alpaca API base URL. Defaults to 'https://paper-api.alpaca.markets'.
        """
        self.api = TradingClient(api_key, api_secret, paper)
        self.account = self.api.get_account()


    def buy(self, symbol: str, notional: float, limit_price: float=None, take_profit: float=None, stop_price: float=None) -> dict:
        """
        Place a buy order for the specified symbol.

        Args:
            symbol (str): The symbol of the security to buy (e.g., 'AAPL').
            qty (int): The quantity of shares to buy.
            limit_price (float, optional): The limit price for the buy order. Defaults to None.
            stop_price (float, optional): The stop price for the buy order. Defaults to None.

        Returns:
            dict: The buy order response from the Alpaca API.
        """
        market_order_data = MarketOrderRequest(
            symbol=symbol,
            notional=notional,
            side=OrderSide.BUY,
            type=OrderType.LIMIT if limit_price is not None else OrderType.MARKET,
            time_in_force=TimeInForce.DAY,
            limit_price=limit_price,
            stop_price=stop_price,
            take_profit=TakeProfitRequest(limit_price=take_profit)
        )
        market_order = self.api.submit_order(market_order_data)
        return market_order


    def sell(self, symbol: str, qty: int=None, limit_price: float=None, percentage: float=None) -> dict:
        """
        Place a sell order for the specified symbol.

        Args:
            symbol (str): The symbol of the security to sell (e.g., 'AAPL').
            qty (int): The quantity of shares to sell.
                **Does not work if percentage is set**.
            limit_price (float, optional): The limit price for the sell order. Defaults to None.
            percentage (float, optional): How much of the stock you want to sell (only works if factional shares is enabled)

        Returns:
            dict: The sell order response from the Alpaca API.

        Throws:
            fractional shares error: may throw error if frational shares is not enabled
                (only if percentage is set)
            position does not exist: will be thrown on non existant positions
        """

        # sell the whole posistion as if neither qty or percentage is set
        if percentage is None and qty is None:
            percentage = 1

        # get/check if there even is an open position
        position = self.api.get_open_position(symbol)

        # adjust the qty if percentage is set
        if percentage is not None:
            qty = position.qty * percentage

        market_order_data = MarketOrderRequest(
            symbol=symbol,
            qty=qty,
            side=OrderSide.SELL,
            type=OrderType.LIMIT if limit_price is not None else OrderType.MARKET,
            time_in_force=TimeInForce.DAY,
        )
        market_order = self.api.submit_order(market_order_data)
        return market_order

    def get_positions(self) -> list:
        """
        Get the current open positions.

        Returns:
            list: A list of position objects representing the current open positions.
        """
        positions = self.api.get_all_positions()
        return positions

    def get_available_cash(self) -> float:
        """
        Get the available cash in the account.

        Returns:
            float: The available cash amount in the account.
        """
        self.account = self.api.get_account()
        available_cash = float(self.account.buying_power)
        return available_cash