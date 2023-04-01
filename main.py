import ccxt
import time

exchange = ccxt.binance({
    'apiKey': 'your_api_key',
    'secret': 'your_secret_key',
})

symbol = 'BTC/USDT'
timeframe = '1h'
quantity = 0.001
slippage_buffer = 0.5
fee_rate = 0.001

# Define the moving averages to use for the strategy
short_ma = 20
long_ma = 50

# Define the minimum distance between the short and long MA to trigger a trade
ma_distance_threshold = 50

# Define the minimum holding period for a position
holding_period = 24  # in hours

# Define the amount of capital to allocate to each trade
capital_per_trade = 1000

# Define the stop loss percentage
stop_loss_percentage = 0.05

# Define the trailing stop percentage
trailing_stop_percentage = 0.02

# Initialize variables
last_buy_price = None
last_sell_price = None
holding_start_time = None

while True:
    # Get the latest price data for the symbol
    data = exchange.fetch_ohlcv(symbol, timeframe)
    close_prices = [x[4] for x in data]

    # Calculate the moving averages
    short_sma = sum(close_prices[-short_ma:]) / short_ma
    long_sma = sum(close_prices[-long_ma:]) / long_ma

    # Calculate the distance between the short and long MA
    ma_distance = abs(short_sma - long_sma)

    # Check if the short MA has crossed above the long MA
    if short_sma > long_sma and ma_distance > ma_distance_threshold:
        # Calculate the buy price with a buffer for slippage
        buy_price = exchange.fetch_ticker(symbol)['ask'] * (1 + slippage_buffer)

        # Calculate the amount to buy based on the allocated capital per trade
        allocation = capital_per_trade / buy_price
        quantity_to_buy = min(allocation, quantity)

        # Place the buy order with a limit price
        order = exchange.create_limit_buy_order(symbol, quantity_to_buy, buy_price)

        # Record the buy price and holding start time
        last_buy_price = buy_price
        holding_start_time = time.time()

    # Check if the short MA has crossed below the long MA
    elif short_sma < long_sma and ma_distance > ma_distance_threshold:
        # Calculate the sell price with a buffer for slippage
        sell_price = exchange.fetch_ticker(symbol)['bid'] * (1 - slippage_buffer)

        # Calculate the holding period
        holding_period_hours = (time.time() - holding_start_time) / 3600

        # Calculate the stop loss price
        stop_loss_price = last_buy_price * (1 - stop_loss_percentage)

        # Calculate the trailing stop price
        trailing_stop_price = max(last_sell_price, sell_price) * (1 - trailing_stop_percentage)

        # Place the sell order with a limit price
        order = exchange.create_limit_sell_order(symbol, quantity, sell_price)

        # Record the sell price
        last_sell_price = sell_price

    # Check if the holding period has exceeded the threshold
    if holding_start_time is not None and holding_period_hours >= holding_period:
        # Calculate the holding period in days
        holding_period_days = holding_period_hours / 24

        # Calculate the fee for the trade
        fee = fee_rate * (last_buy_price + last_sell_price) * quantity

        # Calculate the profit or loss
        pnl = (last_sell_price - last_buy_price) * quantity - fee

        # Print the trade information
        print(f'Trade executed: Buy {quantity_to_buy:.8f} {symbol.split("/")[0]} at {last_buy_price:.2f}, sell {quantity:.8f} {symbol.split("/")[0]} at {last_sell_price:.2f}')
        print(f'Holding period: {holding_period_days:.2f} days')
        print(f'Fee: {fee:.8f} {symbol.split("/")[1]}')
        print(f'Profit or loss: {pnl:.8f} {symbol.split("/")[1]}')

        # Reset the variables
        last_buy_price = None
        last_sell_price = None
        holding_start_time = None

    # Wait for the next price update
    time.sleep(60)