import time
from datetime import datetime
from strategy.cashflow import LIFO
from strategy.money_management import NonLeveragedLinear
from sort_client_trading_class import ClassicSpot

class RunBot:
    def __init__(
                self, 
                api_key: str, 
                api_secret: str, 
                subaccount: str, 
                symbol: str, 
                postOnly: bool, 
                capital: float, 
                up_zone: float, 
                down_zone: float, 
                min_delta: float, 
                min_pct: float, 
                allow_live_trading: bool,
                ) -> None:

        self.api_key = str(api_key)
        self.api_secret = str(api_secret)
        self.subaccount = str(subaccount)
        self.symbol = str(symbol)
        self.postOnly = bool(postOnly)
        self.capital = float(capital)
        self.up_zone = float(up_zone)
        self.down_zone = float(down_zone)
        self.min_delta = float(min_delta)
        self.min_pct = float(min_pct)
        self.allow_live_trading =  bool(allow_live_trading)
        
        self._ftx = ClassicSpot(
                                api_key = self.api_key,
                                api_secret = self.api_secret,
                                subaccount_name = self.subaccount,
                                symbol = self.symbol,
                                postOnly = self.postOnly
                    )
        
        self._cs = NonLeveragedLinear(
                                    initialCap = self.capital, 
                                    zone = [self.down_zone, self.up_zone]
                    )

        self.start_time = int(datetime(2022,3,1).timestamp())
        self.end_time = int(time.time()) 
        self.orders_history = self._ftx.get_fills(
                                        self._ftx.symbol,
                                        self.start_time,
                                        self.end_time,
                            )[::-1]
        self._cf = LIFO(self.orders_history)

    def progress_bar(self, max_val, tb):
        tb = tb*0.8
        for done in range(max_val):
            time.sleep(tb/max_val)
            undone = max_val - 1 - done
            proc = (100 * done) // (max_val - 1)
            print(f"\r[{('=' * done) + (' ' * undone)}] ({proc}%)", end='\r')


    def trade(self):

        price = self._ftx.get_price()
        prev_price = self._ftx.get_previous_price()

        pair_coins = self._ftx.get_pair_coins()
        asset = pair_coins[self._ftx.asset_name] if self._ftx.asset_name in pair_coins.keys() else float(0)
        cash = self._ftx.get_pair_coins()[self._ftx.cash_name]

        # round format number
        dec_price = str(price)[::-1].find('.')
        round_size = self._ftx.get_size_increment() 
        round_min_size = str(round_size)[::-1].find('.')

        adj_position = self._cs.cal_output(price)

        # check delta position and delta price percent change 
        delta = asset - adj_position
        pct_change = (price/prev_price-1)*100

        # dd/mm/YY H:M:S
        dt_string = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

        # Log show trading details
        # os.system('cls')
        print('{:<33s}'.format(dt_string))
        print('%-23s %10.{0}f'.format(dec_price) % ('Market price:', price))
        print('%-23s %10.{0}f'.format(dec_price) % ('Previous price:', price))
        print('{0:<23s} {1:10.2f}'.format('Cash:', cash))
        print('%-23s %10.{0}f'.format(round_min_size) % ('Asset:', asset))
        print('%-23s %10.{0}f'.format(round_min_size) % ('Adjust asset:', adj_position))
        print('%-23s %10.{0}f'.format(round_min_size) % ('Delta asset:', delta))
        print('{0:<23s} {1:10.2f}\n'.format('Pct(%) change:', pct_change))

        # Buy 
        if delta <= -self.min_delta and pct_change <= -self.min_pct:
            self._ftx.cancel_all_symbol_orders()
            unit = (abs(delta)//round_size)*round_size
            round_price = round(price-price*0.0005, dec_price)

            if self.allow_live_trading:
                order = self._ftx.create_order('buy', round_price, 'limit', unit)

                if type(order) is str: 
                    result = order
                else:
                    result = '{} {} {} {} @{} {}'.format(
                                            order['side'], 
                                            order['market'], 
                                            order['size'], 
                                            self._ftx.asset_name, 
                                            order['price'],
                                            self._ftx.cash_name,
                                            )    
            else:
                result = f'test buy {self._ftx.symbol} {unit} {self._ftx.asset_name} @{round_price} {self._ftx.cash_name}'
        
        # Sell 
        elif delta >= self.min_delta and pct_change >= self.min_pct:
            self._ftx.cancel_all_symbol_orders()
            unit = (abs(delta)//round_size)*round_size
            round_price = round(price+price*0.0005, dec_price)

            if self.allow_live_trading:
                order = self._ftx.create_order('sell', round_price, 'limit', unit) 

                if type(order) is str: 
                    result = order
                else:
                    result = '{} {} {} {} @{} {}'.format(
                                            order['side'], 
                                            order['market'], 
                                            order['size'], 
                                            self._ftx.asset_name, 
                                            order['price'],
                                            self._ftx.cash_name,
                                            )
            else:
                result = f'test sell {self._ftx.symbol} {unit} {self._ftx.asset_name} @{round_price} {self._ftx.cash_name}'
        
        # Wait
        else:
            result = 'Wait !!!'

        print(result)
        return result

    def cancel_orders(self):
        return self._ftx.cancel_all_symbol_orders()

    def send_report(self):
        self._cf.cal_cashflow()
        cashflow = self._cf.total_cashflow - self._cf.fee
        
        price = self._ftx.get_price()
        prev_price = self._ftx.get_previous_price()

        pair_coins = self._ftx.get_pair_coins()
        asset = pair_coins[self._ftx.asset_name] if self._ftx.asset_name in pair_coins.keys() else float(0)
        cash = self._ftx.get_pair_coins()[self._ftx.cash_name]
        equity = asset*price+cash

        # round format number
        dec_price = str(price)[::-1].find('.')
        round_size = self._ftx.get_size_increment() 
        round_min_size = str(round_size)[::-1].find('.')

        adj_position = self._cs.cal_output(price)

        # check delta position and delta price percent change 
        delta = asset - adj_position
        pct_change = (price/prev_price-1)*100

        # dd/mm/YY H:M:S
        dt_string = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

        return  '{0}\n'.format(dt_string) + \
            '\nSub: {0}\n'.format(self.subaccount) + \
            'Symbol: {0}\n'.format(self.symbol) + \
            'Market price: {0:.{dec_price}f}\n'.format(price, dec_price=dec_price) + \
            'Previous price: {0:.{dec_price}f}\n'.format(prev_price, dec_price=dec_price) + \
            'Delta asset: {0:.{round_min_size}f}\n'.format(delta, round_min_size=round_min_size) + \
            'Pct change: {0:.2f}\n'.format(pct_change) + \
            'Equity: {0:.2f}\n'.format(equity) + \
            'Asset: {0:.{round_min_size}f}\n'.format(asset, round_min_size=round_min_size) + \
            'Cash: {0:.2f}\n'.format(cash) + \
            'Cashflow: {0:.2f}'.format(cashflow) 
            
    def fire_sale(self):
        self._ftx.cancel_all_symbol_orders()
        
        price = self._ftx.get_price()
        unit = self._ftx.get_pair_coins()[self._ftx.asset_name]
        dec_price = str(price)[::-1].find('.')
        round_price = round(price+price*0.0005, dec_price)
        order = self._ftx.create_order('sell', round_price, 'limit', unit)
        if type(order) is str: 
            result = order
        else:
            result = '{} {} {} {} @{} {}'.format(
                                            order['side'], 
                                            order['market'], 
                                            order['size'], 
                                            self._ftx.asset_name, 
                                            order['price'],
                                            self._ftx.cash_name,
                                        )
        return result
    
    def transfer_cashflow(self, size):
        return self._ftx.transfer_subaccount(self._ftx.cash_name, size, self._ftx.subaccount, 'main')
        


if __name__ == '__main__':

    bot = RunBot(
        api_key = 'dM5SI_88s6ihuBFre9QZaqSOmw5Cnx17Dq5PMpet', 
        api_secret = 'eBfj1ucfEANnL-89qqTFxlqXqhC8hTxmkt9o6CYT', 
        subaccount = 'Night_XRP_1.0', 
        symbol = 'XRP/USD', 
        postOnly = 1,
        capital = 300, 
        up_zone = 1.0, 
        down_zone = 0.3, 
        min_delta = 1.0, 
        min_pct = 3.0,
        allow_live_trading = 0)


    # bot._cf.cal_cashflow()
    # print(bot._cf.total_cashflow)
    
    