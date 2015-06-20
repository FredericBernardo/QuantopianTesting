# For this example, we're going to write a simple momentum script.  
# When the stock goes up quickly, we're going to buy; 
# when it goes down we're going to sell.  
# Hopefully we'll ride the waves.

# To run an algorithm in Quantopian, you need two functions: 
# initialize and handle_data
from operator import itemgetter
import math

class Stats(object):
    pass

def initialize(context):
    context.topMom = 10
    context.rebal_int = 3
    context.lookback = 250
    set_symbol_lookup_date('2015-01-01')
    context.stocks = symbols('SPY', 'EFA', 'BND', 'VNQ', 'GSG', 'BIL')
 
    # Add statistics
    context.stats = Stats()
    context.stats.variances = dict()
    context.stats.count = 0
    for stock in context.stocks:
        context.stats.variances[stock.symbol] = 0
    
    schedule_function(rebalance,
                      date_rule=date_rules.month_start(),
                      time_rule=time_rules.market_open())
    

def rebalance(context, data):
    #Create stock dictionary of momentum
    MomList = GenerateMomentumList(context, data)

    #List next position to buy
    nextPosition = set()
    for l in MomList:
        stock = l[0]
        if stock in data and data[stock].close_price > data[stock].mavg(200):
            nextPosition.add(stock)
            
    #sell if not among the next positions
    for stock in context.portfolio.positions:
        if stock not in nextPosition:
            order_target(stock, 0)
        else:
            nextPosition.discard(stock)
    
    if len(nextPosition) > 0:
        weight = 0.95/(len(nextPosition)+len(context.portfolio.positions))

        #buy
        for stock in nextPosition:
            print ('Buy ' + str(weight) + ' of ' + stock.symbol)
            order_percent(stock, weight)
        
    pass
    
    
def GenerateMomentumList(context, data):
    
    MomList = []
    price_history = history(bar_count=context.lookback, frequency="1d", field='price')
    context.stats.count += 1
    
    for stock in context.stocks:
        now = price_history[stock].ix[-1]
        old = price_history[stock].ix[0]
        pct_moment = moment1(price_history[stock].ix)
        context.stats.variances[stock.symbol] += math.pow(pct_moment, 2)
        MomList.append([stock, pct_moment, now])

    MomList = sorted(MomList, key=itemgetter(1), reverse=True)

    # return only the top "topMom" number of securities
    MomList = MomList[0:context.topMom]

    return MomList
    

def moment1(history):
    return(( history[-1] - history[0])/history[0])


def handle_data(context, data):
    pass
	