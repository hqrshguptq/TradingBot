import websocket, json
import dateutil.parser

minutes_processed = {}
minute_candlesticks = []
current_tick = None
previous_tick = None
in_position = False


def on_open(ws):
    print("opened connection")

    subscribe_message = {
        "type": "Subscribe",
        "channels": [
            {
                "name": "ticker",
                "product_ids": [
                   "BTC-USD"
                ]
            }
        ]
    }

    ws.send(json.dumps(subscribe_message))

def on_message(ws, message):
    global current_tick, previous_tick, in_position
    
    previous_tick = current_tick
    current_tick = json.loads(message)[0]

    print("=== Received Tick ===")
    print("{} @ {}".format(current_tick['time'], current_tick['price']))
    tick_datetime_object = datetime.utcfromtimestamp(current_tick['time']/1000)
    tick_dt = tick_datetime_object.strftime('%Y-%m-%d %H:%M')
    print(tick_datetime_object.minute)
    print(tick_dt)

    if not tick_dt in minutes_processed:
        print("starting new candlestick")
        minutes_processed[tick_dt] = True
        print(minutes_processed)

        if len(minute_candlesticks) > 0:
            minute_candlesticks[-1]['close'] = previous_tick['price']
        
        minute_candlesticks.append({
            "minute": tick_dt,
            "open": current_tick['price'],
            "high": current_tick['price'],
            "low": current_tick['price']
        })

    if len(minute_candlesticks) > 0:
        current_candlestick = minute_candlesticks[-1]
        if current_tick['price'] > current_candlestick['high']:
            current_candlestick['high'] = current_tick['price']
        if current_tick['price'] < current_candlestick['low']:
            current_candlestick['low'] = current_tick['price']

    print("== Candlesticks ==")
    for candlestick in minute_candlesticks:
        print(candlestick)

    if len(minute_candlesticks) > 3:
        print("== there are more than 3 candlesticks, checking for pattern ==")
        last_candle = minute_candlesticks[-2]
        previous_candle = minute_candlesticks[-3]
        first_candle = minute_candlesticks[-4]

        print("== let's compare the last 3 candle closes ==")
        if last_candle['close'] > previous_candle['close'] and previous_candle['close'] > first_candle['close']:
            print("=== Three green candlesticks in a row, let's make a trade! ===")
            distance = last_candle['close'] - first_candle['open']
            print("Distance is {}".format(distance))
            profit_price = last_candle['close'] + (distance * 2)
            print("I will take profit at {}".format(profit_price))
            loss_price = first_candle['open']
            print("I will sell for a loss at {}".format(loss_price))

            if not in_position:
                print("== Placing order and setting in position to true ==")
                in_position = True
                place_order(profit_price, loss_price)
                sys.exit()
        else:
            print("No go")
    

def on_close(ws):
    print("closed connection")        


socket = "wss://ws-feed.pro.coinbase.com"

ws=websocket.WebSocketApp(socket,on_open=on_open,  on_message=on_message,on_close=on_close)
ws.run_forever()