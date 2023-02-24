import numpy as np
import matplotlib.pyplot as plt

class NonLeveragedLinear:

    def __init__(self,initialCap=300, zone=[0, 1]):
        self.initialCap = initialCap
        self.lower = zone[0]
        self.upper = zone[1]
        self.maxPos = self.initialCap/((self.upper+self.lower)/2)

    def cal_output(self, price):
        x1 = np.min([self.upper, price])
        x2 = np.max([self.lower, x1])
        m = self.maxPos/(self.lower-self.upper)
        pos = m*(x2-self.upper)
        return pos
    
    def cal_value_without_cashflow(self, price):
        price = np.min([self.upper, price])
        rect = np.min([self.lower, price])
        y1 = self.linearFunc(price)
        value = 0.5*(self.maxPos+y1)*(price-rect)+self.maxPos*rect
        return value
    
    def plot_linear(self):
        # For plot
        # plot linear
        x1 = np.arange(self.lower-self.lower*0.05, self.upper+self.upper*0.03, self.upper/100)
        y1 = np.array([self.cal_output(i) for i in x1])
        # plot port value without cashflow
        x2 = np.arange(0, self.upper+self.upper*0.05, self.upper/100)
        y2 = np.array([self.cal_value_without_cashflow(i) for i in x2])
        
        fig = plt.figure(figsize=(15,4))
        ax1 = fig.add_subplot(121)
        ax2 = fig.add_subplot(122)
        
        ax1.plot(x1, y1, 'orange')
        ax1.title.set_text('Linear Function')
        ax1.grid()
        ax1.set_ylabel('Position')
        ax1.set_xlabel('Price')
        
        ax2.plot(x2, y2, 'orange')
        ax2.title.set_text('Port Value Curve without Cashflow')
        ax2.grid()
        ax2.set_ylabel('Port Value')
        ax2.set_xlabel('Price')
        plt.show()


class LeveragedLinear():

    def __init__(self, capital=1000, leverage=1, zone=[0, 1]):
        self.capital = capital
        self.leverage = leverage
        self.lev_capital = self.capital*self.leverage
        self.down_zone = zone[0]
        self.up_zone = zone[1]
        self.avg_price = (self.up_zone+self.down_zone)/2
        self.max_position = self.lev_capital/self.avg_price
        
    def linearFunction(self, price):
        x1 = np.min([self.up_zone, price])
        x2 = np.max([self.down_zone, x1])
        m = self.max_position/(self.down_zone-self.up_zone)
        pos = m*(x2-self.up_zone)
        return pos
    
    def estLiquidationPrice(self, mmr=0.03, side=None):
        # mmr = maintenance margin requirement
        total_notional_size = self.avg_price*self.max_position
        if(side.lower() == 'long'):
            est_lp = self.avg_price*(1+mmr-self.capital/total_notional_size)
        elif(side.lower() == 'short'):
            est_lp = self.avg_price*(1-mmr+self.capital/total_notional_size)
        else:
            est_lp = 0
            print('Est. liquidation price error.')
        pct_change = abs((est_lp/self.avg_price-1)*100)

        return est_lp, pct_change

    def plotLinearCurve(self, side, dec_price, dec_pos):
        x1 = np.arange(self.down_zone-self.down_zone*0.05, self.up_zone+self.up_zone*0.03, self.up_zone/100)
        y1 = np.array([self.linearFunction(i) for i in x1])
        
        print('{0:^33}'.format('LEVERAGE FUNCTION DETAILS'))
        print('{0:<23s} {1:10.2f}'.format('Initial capital:', self.capital))
        print('{0:<23s} {1:10.1f}'.format('Leverage factor:', self.leverage))
        print('{0:<23s} {1:10.2f}'.format('Total notional size:', self.lev_capital))
        print('%-23s %10.{0}f'.format(dec_price) % ('Down zone:', self.down_zone))
        print('%-23s %10.{0}f'.format(dec_price) % ('Up zone:', self.up_zone))
        print('%-23s %10.{0}f'.format(dec_price) % ('Average price:', self.avg_price))
        print('%-23s %10.{0}f'.format(dec_pos) % ('Max position size:', self.max_position))
        print('%-23s %10.{0}f'.format(dec_price) % ('Est. liquidation price:', self.estLiquidationPrice(side=side)[0]))
        print('-'*30)
        
        fig = plt.figure(figsize=(10,6))
        ax1 = fig.add_subplot(111)
        ax1.plot(x1, y1, 'orange')
        ax1.title.set_text('Linear Function')
        ax1.grid()
        ax1.set_ylabel('Position')
        ax1.set_xlabel('Price')
        plt.show()

if __name__ == "__main__":
    
    cs = NonLeveragedLinear(1000, [0.3, 1.2])
    #cs.plot_linear()