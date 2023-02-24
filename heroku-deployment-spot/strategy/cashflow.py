# For ftx only
import numpy as np

class LIFO:
    def __init__(self, orders_history):
        self.orders_history = orders_history
        self.lifo_price = []
        self.lifo_unit = []
        self.total_cashflow = 0
        self.cum_cashflow = []
        self.fee = 0
    
    def _buy_in(self, unit, price):
        self.lifo_price.append(price)
        self.lifo_unit.append(unit)

    def _sell_out(self, unit, price):
        sum_unit = 0
        list_unit = []
        list_price = []
          
        while  sum_unit < unit:
            u = self.lifo_unit.pop()
            p = self.lifo_price.pop()
            sum_unit += u
            list_unit.append(u)
            list_price.append(p)
    
        for u, p in zip(list_unit, list_price):
            if u > unit:
                cf = unit*(price-p) 
                self.total_cashflow += cf
                self.lifo_unit.append(u-unit)
                self.lifo_price.append(p)
            else:
                cf = u*(price-p) 
                self.total_cashflow += cf
                unit-=u
        self.cum_cashflow.append(self.total_cashflow)
    
    def cal_cashflow(self):
        orders = self.orders_history
        if not orders:
            return 0

        for order in orders:
            if order['side'] == 'buy':
                self._buy_in(order['size'], order['price'])
 
            elif order['side'] == 'sell':
                self._sell_out(order['size'], order['price'])
                self.fee += float(order['fee'])

    # def cal_cashflow(self):
    #     orders = self.orders_history
    #     if not orders:
    #         return 0

    #     for order in orders:
    #         if order['side'] == 'buy' and order['status'] == 'closed':
    #             if order['type'] == 'limit':
    #                 self._buy_in(order['size'], order['price'])

    #             elif order['type'] == 'market':
    #                 self._buy_in(order['size'], order['avgFillPrice'])
            
    #         elif order['side'] == 'sell' and order['status'] == 'closed':
    #             if order['type'] == 'limit':
    #                 self._sell_out(order['size'], order['price'])

    #             elif order['type'] == 'market':
    #                 self._sell_out(order['size'], order['avgFillPrice'])

if __name__ == '__main__':

    pass
    
    