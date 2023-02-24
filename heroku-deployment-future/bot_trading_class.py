import time
from datetime import datetime
from risk_management.cashflow import LIFO
from risk_management.money_management import LeveragedLinear
from sort_client_trading_class import ClassicFuture

class RunBot:
    def __init__(
                self, 
                api_key: str, 
                api_secret: str, 
                subaccount: str, 
                symbol: str, 
                postOnly: bool, 
                capital: float,
                leverage: str, 
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
        self.leverage = float(leverage)
        self.up_zone = float(up_zone)
        self.down_zone = float(down_zone)
        self.min_delta = float(min_delta)
        self.min_pct = float(min_pct)
        self.allow_live_trading =  bool(allow_live_trading)
        
        self._ftx = ClassicFuture(
                                api_key = self.api_key,
                                api_secret = self.api_secret,
                                subaccount_name = self.subaccount,
                                symbol = self.symbol,
                                postOnly = self.postOnly
                    )
        
        self._cs = LeveragedLinear(
                                capital = self.capital, 
                                leverage = self.leverage,
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
        market = self._ftx.symbol.split('-')[0] # ETH, BTC
        set_lev = self._ftx.set_leverage(20)

        price = self._ftx.get_price()
        prev_price = self._ftx.get_previous_price()

        total_position = self._ftx.get_position_size()  
        total_col = self._ftx.get_total_collateral()     
        free_col = self._ftx.get_free_collateral()
        notional_size = self._ftx.get_national_size()
        max_lev = self._ftx.get_leverage() 
        lev_used = self._ftx.get_leverage_used()
        liq_price = self._ftx.est_liquidation_price()

        # round format number
        dec_price = str(price)[::-1].find('.')
        round_size = self._ftx.get_size_increment()
        dec_position = str(round_size)[::-1].find('.')

        adj_position = self._cs.cal_output(price)

        # check delta position and delta price percent change 
        delta = total_position - adj_position

        pct_change = (price/prev_price-1)*100

        # dd/mm/YY H:M:S
        dt_string = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

        # Log show trading details
        # os.system('cls')
        print('{:<33s}'.format(dt_string))
        print('{0:<23s} {1:10.2f}'.format('Total collateral:', total_col))
        print('{0:<23s} {1:10.2f}'.format('Free collateral:', free_col))
        print('{0:<23s} {1:10.2f}'.format('Leverage:', lev_used))
        print('{0:<23s} {1:10.2f}'.format('Notional size:', notional_size))
        print('%-23s %10.{0}f'.format(dec_price) % ('Est. liquidation price:', liq_price))
        print('%-23s %10.{0}f'.format(dec_price) % ('Market price:', price))
        print('%-23s %10.{0}f'.format(dec_position) % ('Total position:', total_position))
        print('%-23s %10.{0}f'.format(dec_position) % ('Adjust position:', adj_position))
        print('%-23s %10.{0}f'.format(dec_position) % ('Delta position:', delta))
        print('{0:<23s} {1:10.2f}\n'.format('Pct(%) change:', pct_change))
        
        # Long if asset == 0
        if total_position < self._ftx.get_min_provide_size() and delta <=-self.min_delta:
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
                                                market, 
                                                order['price'],
                                                'USD',
                                            )    
            else:
                result = f'test buy {self._ftx.symbol} {unit} {market} @{round_price} USD'

        # Long
        elif delta <= -self.min_delta and pct_change <= -self.min_pct:
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
                                                market, 
                                                order['price'],
                                                'USD',
                                            )    
            else:
                result = f'test buy {self._ftx.symbol} {unit} {market} @{round_price} USD'
        
        # Short
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
                                                market, 
                                                order['price'],
                                                'USD',
                                            )
            else:
                result = f'test sell {self._ftx.symbol} {unit} {market} @{round_price} USD'
        
        # Wait
        else:
            result = 'Wait !!!'
        
        return result


    def cancel_orders(self):
        return self._ftx.cancel_all_symbol_orders()


    def send_lev_details(self):
        price = self._ftx.get_price()

        dec_price = str(price)[::-1].find('.')
        round_size = self._ftx.get_size_increment()
        dec_position = str(round_size)[::-1].find('.')

        return 'LEVERAGE FUNCTION DETAILS\n' + \
            '\nInitial capital: {}\n'.format(self._cs.capital) + \
            'Leverage factor: {}\n'.format(self._cs.leverage) + \
            'Total notional size: {}\n'.format(self._cs.lev_capital) + \
            'Down zone: {0:.{dec_price}f}\n'.format(self._cs.down_zone, dec_price=dec_price) + \
            'Up zone: {0:.{dec_price}f}\n'.format(self._cs.up_zone, dec_price=dec_price) + \
            'Average price: {0:.{dec_price}f}\n'.format(self._cs.avg_price, dec_price=dec_price) + \
            'Max position size: {0:.{dec_position}f}\n'.format(self._cs.max_position, dec_position=dec_position) + \
            'Est. liq price: {0:.{dec_price}f}'.format(self._cs.est_liq_price(side='long')[0], dec_price=dec_price)
        
    def send_report(self):

        self._cf.cal_cashflow()
        # funding = self._ftx.cal_funding_payments('long')
        cashflow = self._cf.total_cashflow - self._cf.fee # + funding

        price = self._ftx.get_price()
        prev_price = self._ftx.get_previous_price()

        total_position = self._ftx.get_position_size()  
        total_col = self._ftx.get_total_collateral()     
        free_col = self._ftx.get_free_collateral()
        notional_size = self._ftx.get_national_size()
        lev_used = self._ftx.get_leverage_used()
        liq_price = self._ftx.est_liquidation_price()

        # round format number
        dec_price = str(price)[::-1].find('.')
        round_size = self._ftx.get_size_increment()
        dec_position = str(round_size)[::-1].find('.')

        adj_position = self._cs.cal_output(price)

        # check delta position and delta price percent change 
        delta = total_position - adj_position

        pct_change = (price/prev_price-1)*100

        # dd/mm/YY H:M:S
        dt_string = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

        return  '{0}\n'.format(dt_string) + \
            '\nSub: {0}\n'.format(self.subaccount) + \
            'Symbol: {0}\n'.format(self.symbol) + \
            'Total collateral: {0:.2f}\n'.format(total_col) + \
            'Free collateral: {0:.2f}\n'.format(free_col) + \
            'Leverage used: {0:.2f}\n'.format(lev_used) + \
            'Notional size: {0:.2f}\n'.format(notional_size) + \
            'Est. liq price: {0:.{dec_price}f}\n'.format(liq_price, dec_price=dec_price) + \
            '\nMarket price: {0:.{dec_price}f}\n'.format(price, dec_price=dec_price) + \
            'Previous price: {0:.{dec_price}f}\n'.format(prev_price, dec_price=dec_price) + \
            'Position: {0:.{dec_position}f}\n'.format(total_position, dec_position=dec_position) + \
            'Delta position: {0:.{dec_position}f}\n'.format(delta, dec_position=dec_position) + \
            'Pct change: {0:.2f}\n'.format(pct_change) + \
            'Cashflow: {0:.2f}'.format(cashflow) 
            
    def fire_sale(self):
        self._ftx.cancel_all_symbol_orders()

        market = self._ftx.symbol.split('-')[0] # ETH, BTC
        price = self._ftx.get_price()
        dec_price = str(price)[::-1].find('.')
        round_price = round(price+price*0.0005, dec_price)
        position = self._ftx.get_position_size()
        order = self._ftx.create_order('sell', round_price, 'limit', position)
        if type(order) is str: 
            result = order
        else:
            result = '{} {} {} {} @{} {}'.format(
                                            order['side'], 
                                            order['market'], 
                                            order['size'], 
                                            market, 
                                            order['price'],
                                            'USD',
                                        )
        return result


        

if __name__ == '__main__':

    bot = RunBot(
        api_key = 'HuCUQVxUgzlm8PWeGKjbesbI5BWN5FnhT2UgiWPW', 
        api_secret = '0J0TCivfvdMLLQ4ckxf6-MEI_JqujobKjNUM59fi', 
        subaccount = 'K_XRP_PERP_1.1', 
        symbol = 'XRP-PERP', 
        postOnly = 1,
        capital = 500, 
        leverage = 2,
        up_zone = 50000, 
        down_zone = 18000, 
        min_delta = 0.0001, 
        min_pct = 3.0,
        allow_live_trading = 0
    )

    pass