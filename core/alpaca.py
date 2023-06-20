from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest, TrailingStopOrderRequest, TakeProfitRequest, StopLossRequest, GetOrdersRequest
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
        self.api = TradingClient(api_key=api_key, secret_key=api_secret, paper=paper)
        self.account = self.api.get_account()

    def get_order(self, symbol: str) -> dict:
        """ Returns the order for the given symbol

            Args:
                symbol: The symbol to get the order for
            
            Returns:
                dict: the order object
            
            Raises:
                Exception: "order not found" if the order is not found
        """

        order_request = GetOrdersRequest(symbols=[symbol])
        orders = self.api.get_orders(order_request)

        if len(orders) == 0:
            raise Exception("order not found")
        else:
            return orders[0]

    def buy(self, symbol: str, qty: int, limit_price: float=None, trail_percent: float=6) -> dict:
        """
        Place a buy order for the specified symbol.

        Args:
            symbol (str): The symbol of the security to buy (e.g., 'AAPL').
            qty (int): The quantity of shares to buy.
            limit_price (float, optional): The limit price for the buy order. Defaults to None.
            stop_price (float, optional): The stop price for the buy order. Defaults to None.

        Returns:
            dict: The buy order response from the Alpaca API.
        
        Raises:
            fractional shares error: may throw error if frational shares is not enabled
                (only if percentage is set)
            Exception: "existing pending order" if there is an existing order
        """

        existing_order = False
        try:
            # check if there is an unfulfilled order
            order = self.get_order(symbol=symbol)
            if order.symbol == symbol and order.status in ['new', 'accepted', 'held', 'partially_filled', 'done_for_day', 'pending_new', 'accepted_for_bidding']:
                # we have an exitsing order for this symbol so we should wait for
                # to resolve. orders should only last a day before failing
                # (dont raise exception here because it will do nothing)
                existing_order = True
            
        except Exception as error:
            print(error)
            # should be safe to buy

        if existing_order:
            raise Exception("existing pending order")

        market_order_data = TrailingStopOrderRequest(
            symbol=symbol,
            qty=qty,
            side=OrderSide.BUY,
            type=OrderType.LIMIT if limit_price is not None else OrderType.MARKET,
            time_in_force=TimeInForce.DAY,
            limit_price=limit_price,
            trail_percent=trail_percent,
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

        Raises:
            fractional shares error: may throw error if frational shares is not enabled
                (only if percentage is set)
            position does not exist: will be thrown on non existant positions
        """

        # sell the whole posistion as if neither qty or percentage is set
        if percentage is None and qty is None:
            percentage = 1

        # get/check if there even is an open position
        position = self.api.get_open_position(symbol)

        existing_order = False
        try:
            # check if there is an unfulfilled order
            order = self.get_order(symbol=symbol)
            if order.symbol == symbol and order.status in ['new', 'accepted', 'held', 'partially_filled', 'done_for_day', 'pending_new', 'accepted_for_bidding']:
                # we have an exitsing order for this symbol so we should wait for
                # to resolve. orders should only last a day before failing
                # (dont raise exception here because it will do nothing)
                existing_order = True
            
        except Exception as error:
            print(error)
            # should be safe to sell

        if existing_order:
            raise Exception("existing pending order")

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