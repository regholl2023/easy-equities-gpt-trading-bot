from operator import getitem
import time

from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException

class EasyEquities:
    """A selenium based browser contorller to buy, sell, manage stocks on easy equities

    Args:
        driver: a selenium webdriver
        account: the type of account inside easy equities, default is 'Demo USD'
    """
    def __init__(self, driver, username, password, account = 'Demo USD'):
        self.driver = driver
        self.account = account
        self.driver.implicitly_wait(10)
        self.username = username
        self.password = password

    def login(self):
        """Directs the webdriver to the login page and logs in

        Returns:
            bool: True if successful login
        
        Raises:
            Exception: raises exception if username and password feilds dont exist
            Exception: raises exception if the login page loads successfully
                but fails to login or navigate to the profile page after submitting
        """

        # goto login page
        self.driver.get("https://platform.easyequities.co.za/Account/SignIn")

        # return true if already logged in
        if self.get_element((By.CSS_SELECTOR, '#myProfileNavBar') ):
            return True

        # wait for page to load and fill and submit login form
        self.wait_for((By.CSS_SELECTOR, ".login-form-container"))
        username = self.get_element((By.CSS_SELECTOR, '#user-identifier-input') )
        password = self.get_element((By.CSS_SELECTOR,'#Password'))
        if username and password:
            username.clear()
            username.send_keys(self.username)
            password.clear()
            password.send_keys(self.password)
            button = self.get_element((By.CSS_SELECTOR,'.login-form-container #SignIn'))
            button.click()
            self.wait_for((By.CSS_SELECTOR, "#myProfileNavBar"))
            return True
        else:
            # something happend and the username and password feilds dont exist
            raise Exception("Username and password feilds do not exist")

    def load_account_type(self):
        """Loads the account type by clicking on the right div

        Raises:
            Exception: raises exception if div takes tool long to be found
        """
        xpath = (By.XPATH, f"//div[text()='{self.account}'][@id='trust-account-types']")
        self.wait_for(xpath)
        button = self.get_element(xpath)
        button.click()
        time.sleep(3)
        return

    def prep_stock_search(self):
        """navigates to the stock search page

        Raises:
            Exception: raises exception if it fails to load account type
            Exception: raises exception if the page fails to load
        """
        self.driver.get("https://platform.easyequities.io/Equity")
        self.load_account_type()
        self.wait_for((By.XPATH, f"//div[@class='browse-the-market']//div[@class='label-icon']"))
        options = self.get_elements((By.XPATH, f"//div[@class='browse-the-market']//div[@class='label-icon']"))
        for elem in options:
            try:
                if elem.text.strip() == "Equities":
                    elem.click()
            except:
                pass
            
    def load_stock(self, symbol):
        """searches for a stock symbol

        Note: you need to call prep_stock_search befor calling this function or else if will break
            use buy_stock instead

        Args:
            string: the symbol you want to load

        Raises:
            Exception: raises exception if the input feild cannot be found, make sure
                prep_stock_search is called before calling this function
        
        Returns:
            Bool: true if the symbol was found, false if not
        """
        xpath = (By.XPATH, "//input[@id='InstrumentSearchString']")
        search_box = self.wait_and_get_element(xpath)
        search_box.clear()
        search_box.send_keys(symbol)
        time.sleep(3)
        results = self.get_elements((By.XPATH, f"//div[@id='stockContainer']//a"))
        target_elem = None

        def search_page():
            """loops through each result to find the matching symbol

            Returns:
                webdriver element: returns the target element (a link) or None
            """
            for result in results:
                url = result.get_attribute("href").lower()
                if symbol.lower() in url.split("."):
                    return result
            return None
        
        # loop through each page while the next page button is displayed
        while True:
            target_elem = search_page()
            if target_elem:
                break
            elif (not target_elem
                and self.get_element((By.XPATH, "//div[@class='pagination']//a[contains(text(), '»')]"))
                ):
                # go to next page
                self.get_element((By.XPATH, "//div[@class='pagination']//a[contains(text(), '»')]")).click()
                # wait for items to load, they are loaded via javascript so we cant wait for
                # an element to appear because its already there.
                time.sleep(3)

        # go to the stock page
        if target_elem is not None:
            target_elem.click()
            return True
        else:
            return False
        
    
    def buy_stock(self, symbol, ammount):
        """Buys a stock

        Args:
            symbol: The symbol of the stock to buy.
            ammount: how much money you want to spend
        """
        self.prep_stock_search()
        is_stock_loaded = self.load_stock(symbol)
        if is_stock_loaded:
            # wait for ammount input to appear
            money_input = self.wait_and_get_element((By.CSS_SELECTOR, '#js-value-amount'))
            if money_input:
                # clear any existing ammount and send new ammount
                money_input.clear()
                money_input.send_keys(ammount)
                money_input.send_keys(Keys.ENTER)
                time.sleep(5)
                button = self.get_element((By.CSS_SELECTOR,".trade-action-container__right-action-button div"))
                if button:
                    # click buy button and wait for Congratulations page
                    # button.click()
                    # self.wait_for((By.XPATH, "//div[@class='js-quote']/div[contains(@class, 'value-allocations__quote')]"))
                    button.click()
                    self.wait_for((By.XPATH, "//h1[text()='Congratulations']"))
                    return True
                else:
                    return False
            else:
                return False
        else:
            return False
        
    def get_positions(self):
        """Gets all the open positions

        Note: this does not get any pending positions

        Returns:
            dict:
                symbol:
                    purchase_amount: float
                    current_amount: float
                    item: webdriver element
        Raises:
            Exception: would only raise an exception if the html changed
        """
        self.driver.get("https://platform.easyequities.co.za/AccountOverview")
        self.load_account_type()
        time.sleep(3)
        button = self.wait_and_get_element((By.CSS_SELECTOR, '#loadHoldings'))
        button.click()

        try: 
            self.wait_for((By.CSS_SELECTOR, ".holding-table-body .table-display"))
        except Exception as e:
            print(e)
            if self.get_element((By.CSS_SELECTOR,'#no-holdings-message')):
                print('no open postitions')
                return {}

        items = self.get_elements((By.CSS_SELECTOR, ".holding-table-body .table-display"))
        postitions = {}
        for item in items:
            try:
                buy_more_link = item.find_element(By.XPATH, ".//div[@class='actions-cell']//a[2]")
                symbol = self.get_symbol_from_link(buy_more_link.get_attribute("href"))
                purchase_amount = item.find_element(By.XPATH, ".//div[@class='purchase-value-cell']").text
                purchase_amount = self.string_to_float(purchase_amount)
                current_amount = item.find_element(By.XPATH, ".//div[@class='purchase-value-cell']").text
                current_amount = self.string_to_float(current_amount)
                postitions[symbol] = {
                    "purchase_amount": purchase_amount,
                    "current_amount": current_amount,
                    "item": item,
                }
            except Exception as e:
                raise Exception(e)
        return postitions

    def get_position(self, symbol):
        """gets a single open postition

        Args:
            symbol: The symbol of the stock to buy.

        Returns:
            dict:
                purchase_amount: float
                current_amount: float
                item: webdriver element
        """
        postitions = self.get_positions()
        return postitions.get(symbol, None)
        
    
    def sell_position(self, symbol, percentage=100):
        """Sells an open position

        Args:
            symbol: The symbol of the stock to sell.

        Returns:
            bool: True if the position was successfully closed and False if not
        """

        position = self.get_position(symbol)
        if position is not None:
            position['item'].find_element(By.XPATH, ".//div[@class='actions-cell']//a[1]").click()
            sell_percentage_input = self.wait_and_get_element((By.XPATH, "//input[@name='TradePercentage']"))
            sell_percentage_input.clear()
            sell_percentage_input.send_keys(percentage)
            sell_button = self.get_element((By.CSS_SELECTOR, '.value-allocations__trade-button'))

            # some times selling does not go very smoothly so the proccess needs to be
            # repeated until easy equities allows us to click the sell button
            i = 0
            while(not self.get_element((By.XPATH, "//h1[text()='Success']"))):
                i += 1
                try:
                    print('attemping click')
                    time.sleep(3)
                    sell_percentage_input.clear()
                    sell_percentage_input.send_keys(percentage)
                    sell_percentage_input.send_keys(Keys.ENTER)
                    time.sleep(5)
                    sell_button = self.get_element((By.CSS_SELECTOR, '.value-allocations__trade-button'))
                    sell_button.click()
                except:
                    print('click failed')
                    if i >= 3:
                        return False
            
            return True

    def get_balance(self):
        """Gets how much money is available
        
        Returns:
            float: amount of money available in the account
        """
        money_element = self.get_element((By.XPATH, "//div[@class='slider-container']//div[contains(@class, 'active-tab')]//div[contains(@class, 'bold-heavy')]/span"))
        if money_element:
            return self.string_to_float(money_element.text)
        else:
            return False

    def string_to_float(self, string):
        """Turns a money string to a float eg "$ 10.00" to 10.0

        Args:
            string: string to convert to float
        
        Returns:
            float
        """
        return float(''.join(c for c in string if (c.isdigit() or c =='.')))

    def get_symbol_from_link(self, link):
        """Gets the symbol from the link to a stock
        
        Args:
            link (string): string to stock
        
        Returns:
            symbol: stock symbol
        """
        return link.split(".")[-1].upper()

    def wait_and_get_element(self, by_selector):
        """Waits for the element to load then returns it

        Args:
            by_selector: needs to be imported using "from selenium.webdriver.common.by import By"
        """
        self.wait_for(by_selector)
        return self.get_element(by_selector)

    def get_element(self, by_selector):
        """Gets an html element from the page matching the given selector

        Args:
            by_selector: needs to be imported using "from selenium.webdriver.common.by import By"

        Returns: a webdriver element or False if the element is not found
        """
        try:
            return self.driver.find_element(by_selector[0], by_selector[1])
        except NoSuchElementException:
            return False
    
    def get_elements(self, by_selector):
        """Returns a list of elements from the page matching the given selector

        TODO: perhaps sending an empty list might be better than returning False

        Args:
            by_selector: needs to be imported using "from selenium.webdriver.common.by import By"

        Returns:
            a list of webdriver elements or False if the elements is not found
        """
        try:
            elems = self.driver.find_elements(by_selector[0], by_selector[1])
        except NoSuchElementException:
            return False
        return elems
    
    def wait_for(self, by_selector, timeout=10 ):
        """Waits for an element to load on the page matching the given selector

        Args:
            by_selector: needs to be imported using "from selenium.webdriver.common.by import By"

        Raises:
            Exception: if the element is not found after a timeout has passed
        """
        try:
            element = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located(by_selector)
            )
        except:
            raise Exception("Element took too long to be found or was not found")