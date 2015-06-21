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
    context.topMom = 50
    context.rebal_int = 3
    context.lookback = 10
    set_universe(universe.DollarVolumeUniverse(floor_percentile=48, ceiling_percentile=52))

    # Add statistics
    context.stats = Stats()
    context.stats.variances = dict()
    context.stats.count = 0

    schedule_function(rebalance,
                      date_rule=date_rules.month_start(),
                      time_rule=time_rules.market_open())


def rebalance(context, data):
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
        mom1 = position[1]
        mom2 = position[2]
        if mom1 <= 0 or mom2 <= 0:
            order_target(position[0], 0)
        else:
            holdPosition.append(position[0])

    # Up to topMom positions in ptf
    if len(nextPosition) > 0:
        nbNewPosition = context.topMom-len(holdPosition)
        nextPosition = nextPosition[0:nbNewPosition]

        weight = 0.95/(len(nextPosition)+len(holdPosition))

        #buy
        for stock in nextPosition:
            order_percent(stock, weight)

    pass


def GenerateMomentumList(context, data):

    momList = []
    currentPositions = []
    price_history = history(bar_count=context.lookback, frequency="1d", field='price')
    context.stats.count += 1

    for stock in data:
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


def handle_data(context, data):
    pass
	
