# For this example, we're going to write a simple momentum script.
# When the stock goes up quickly, we're going to buy;
# when it goes down we're going to sell.
# Hopefully we'll ride the waves.

# To run an algorithm in Quantopian, you need two functions:
# initialize and handle_data
from operator import itemgetter
import math

class StatsMarket():
    def __init__(self):
        self.variances = dict()
        self.count = 0


class StatsPosition():
    def __init__(self,symbol,price):
        self.symbol = symbol
        self.buyPrice = price
        self.count = 1

    def hold(self):
        self.count += 1

    def gain(self,price):
        return (price-self.buyPrice)/self.buyPrice


class StatsPortfolio():
    def __init__(self):
        self.symbols = []
        self.gains = []
        self.minutes = []

    def stats(self):
        if len(self.symbols) > 0:
            print '\nSymbol used (Total / Unique) : ' \
                + str(len(self.symbols))+' / '+str(len(set(self.symbols))) \
                + '\nTime held (Max / Avg) : ' \
                + str(max(self.minutes))+' / '+str(sum(self.minutes)/len(self.minutes)) \
                + '\nGains (Max / Avg / Min) : ' \
                + str(max(self.gains))+' / '+str(sum(self.gains)/len(self.gains))+' / '+ str(min(self.gains))


    def add(self,position, price):
        self.symbols.append(position.symbol)
        self.gains.append(position.gain(price))
        self.minutes.append(position.count)



def initialize(context):
    context.topMom = 20
    context.rebal_int = 3
    context.lookback = 10
    set_do_not_order_list(security_lists.leveraged_etf_list)
    set_universe(universe.DollarVolumeUniverse(floor_percentile=98, ceiling_percentile=100))

    # Add mkt statistics
    context.stats = StatsMarket()

    # Add portfolio stats
    context.statsPortfolio = StatsPortfolio()
    context.statsPositions = dict()

    schedule_function(printStats,
                      date_rule=date_rules.every_day(),
                      time_rule=time_rules.market_close())


def printStats(context, data):
    context.statsPortfolio.stats()


def handle_data(context, data):
    #Create stock dictionary of momentum
    [momList,currentPositions] = GenerateMomentumList(context, data)

    #List next position to buy
    nextPosition = []
    holdPosition = []
    for position in momList:
        stock = position[0]
        if stock in data and stock not in context.portfolio.positions:
            nextPosition.append(stock)

    #sell if not among the next positions
    for position in currentPositions:
        stock = position[0]
        symbol = stock.symbol
        mom1 = position[1]
        mom2 = position[2]
        if mom1 <= 0 or mom2 <= 0:
            if symbol in context.statsPositions:
                context.statsPortfolio.add(context.statsPositions[symbol],data[stock].close_price)
                del context.statsPositions[symbol]
            order_target(stock, 0)
        else:
            if symbol in context.statsPositions:
                context.statsPositions[symbol].hold()
            holdPosition.append(stock)

    # Up to topMom positions in ptf
    if len(nextPosition) > 0:
        nbNewPosition = context.topMom-len(holdPosition)
        nextPosition = nextPosition[0:nbNewPosition]

        weight = 0.95/(len(nextPosition)+len(holdPosition))

        #buy
        for stock in nextPosition:
            order_percent(stock, weight)
            context.statsPositions[stock.symbol] = StatsPosition(stock.symbol, data[stock].price)


def GenerateMomentumList(context, data):

    momList = []
    currentPositions = []
    price_history = history(bar_count=context.lookback, frequency="1d", field='price')
    context.stats.count += 1

    for stock in data:
        # Avoid ETFs
        if stock not in security_lists.leveraged_etf_list:
            # initialize
            if stock.symbol not in context.stats.variances:
                context.stats.variances[stock.symbol] = 0

            pct_moment1 = moment1(price_history[stock].ix, 0)
            pct_moment2 = moment2(price_history[stock].ix, 0)
            context.stats.variances[stock.symbol] += math.pow(pct_moment1, 2)
            result = [stock, pct_moment1, pct_moment2, price_history[stock].ix[0]]
            if stock in context.portfolio.positions:
                currentPositions.append(result)
            momList.append(result)

    momList = filter(lambda el: el[2] > 0 and el[1] > 0, momList)
    momList = sorted(momList, key=itemgetter(1), reverse=True)

    # return only the top "topMom" number of securities
    momList = momList[0:context.topMom]

    return [momList, currentPositions]


def moment1(history, n):
    return (history[n] - history[n-1])/history[n-1]


def moment2(history, n):
    now = moment1(history,n)
    before = moment1(history,n-1)
    return (now-before)/before

    
