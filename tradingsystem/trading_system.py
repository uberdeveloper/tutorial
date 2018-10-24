"""
Trading system as a script.
See the instructions in the notebook on how this works.
The only change here is that the bhav file is
automatically picked up from the web. You need to
change this manually in the utils.py file if there is a holiday.
"""

# Import libraries
import pandas as pd
import os
import datetime
import json
from jinja2 import Environment, FileSystemLoader
from utils import *

# PARAMETERS
# Only change the parameters to 

UNIVERSE = 'NIFTY50' # Universe to be searched
STOP_LOSS = 3 # Stop loss for the order
NUM_STOCKS = 5 # Number of stocks to sell
CAPITAL = 20000
LEVERAGE = 1
ORDERFILE_PREFIX = 'orders_' # Prefix file name to store
DIVERSIFY = False # whether to diversify data among sectors
ACCOUNTID = 'XXXXXX' # For any user
APIKEY = 'xxxxxxxxxxxxxxxx' # For zerodha

# Prepare the dataframe
yesterday, today = pd.bdate_range(end=datetime.datetime.now(), periods=2)
preopen = fetch_preopen_data()
eod = get_bhav_copy(yesterday)
symbols = pd.read_excel('universe.xlsx', sheet_name=UNIVERSE, header=None).values.ravel()
sectors = pd.read_csv('sectors.csv')
df = eod[eod['SYMBOL'].isin(symbols)]
df = df[df['SERIES'] == "EQ"].reset_index(drop=True)
df = df.merge(sectors)


# Diversify function for diversifying sectors
def diversify(frame, n=5):
    """
    Diversify stocks among sectors
    frame
        dataframe
    n
        number of stocks
    """
    industry = set()
    stocks = []
    for k,v in frame.iterrows():
        if v.at['Industry'] not in industry:
            industry.add(v.at['Industry'])
            stocks.append(v)
            if len(stocks) == n:
                break
    f = pd.DataFrame(stocks)
    if len(f) == 0:
        return pd.DataFrame()
    else:
        return f        

# Trading logic

df['RET'] = (df['CLOSE']/df['PREVCLOSE']) - 1
if DIVERSIFY:
    result = diversify(df.sort_values(by='RET', ascending=False), NUM_STOCKS)
else:
    result = df.sort_values(by='RET', ascending = False).iloc[:NUM_STOCKS]
trading_capital = CAPITAL * LEVERAGE
orders = result.merge(preopen, on='SYMBOL')
num_stock = len(orders)

# Pricing logic goes here

orders['trigger_price'] = (orders['OpenPrice'] - 0.05).round(2)
orders['price'] = (orders['trigger_price'] - 0.05).round(2)

# I prefer a constant percentage change instead of value
# If you prefer it, uncomment the below two lines

#orders['trigger_price'] = orders['OpenPrice'] * 0.9985
#orders['price'] = orders['trigger_price'] - 0.05

orders['stop_loss'] = (orders['price'] * (1 + STOP_LOSS * 0.01)).apply(tick).round(2)
orders['qty'] = (trading_capital/num_stock/orders['price']).astype(int)
orders['order'] = 'SELL'
filename = ORDERFILE_PREFIX + datetime.datetime.today().strftime('%Y-%m-%d') + '.csv'
orders.to_csv('orders/' + filename,  index=False)

def generate_nest():
    """
    Most brokers and software provide an option to place basket orders. 
    So we are going to create a basket order from our orders.  We would be using the ``create_order`` function from ``utils.py`` file.
    To do this for your specific broker, do the following steps
        1. Know the format of your broker; you can do this by placing a basket order and exporting it
        2. The format would usually have a list of columns to be filled up. We need to fill all the columns to import our order.
        3. We separate the columns into columns that are already in our dataframe and columns to be included
        4. We prepare a list of matching columns and rename them
        5. For new columns, we create a python dictionary with keys as column names and values as the value for the column (we assume that these columns have a single value)

    Thanks @vjay for providing the necessary support
    """
    # List of columns to be included in the output

    cols = [
        'Segment', 'InstrumentName', 'Symbol', 'Option Type', 'Strike Price',
        'ExpiryDate', 'Price', 'Qty', 'LTP', 'Buy/Sell', 'Order Type',
        'TriggerPrice', 'Pro/Cli', 'P Type', 'Validity', 'AccountId',
        'Validity Date', 'Remarks', 'Participant code', 'Validity Time',
        'Market Proc'    
    ]

    # These columns are common for all orders - columns with a single name
    columns = {
        'Segment': 'NSE',
        'InstrumentName': 'EQ',
        'Option Type': 'NA',
        'Strike Price': 'NA',
        'ExpiryDate': 'NA',
        'LTP': 0,
        'Disclosed Qty': 0,
        'AccountId': ACCOUNTID,
        'Pro/Cli': 'CLI',
        'Validity': 'DAY',
        'P Type': 'MIS',
        'Remarks': '',
        'Validity Date': 'NA',
        'Participant code': '',
        'Validity Time': 'NA',
        'Market Proc': 'NA',
        'Order Type': 'SL'
    }

    # These are columns to be renamed
    rename = {
        'order': 'Buy/Sell',
        'price': 'Price',
        'qty': 'Qty',
        'trigger_price': 'TriggerPrice',
        'price': 'Price' ,
        'SYMBOL': 'Symbol'
    }


    # Generating orders in the required format
    entry_orders = orders.copy()
    entry = create_orders(entry_orders, rename=rename, **columns)

    # Exit orders order type and price to be changed
    exit_orders = orders.copy()
    exit_orders['order'] = 'BUY'
    exit_orders['price'] = 0
    exit_orders['trigger_price'] = stop_loss(orders['price'], 3, order='S').round(2)
    columns.update({'Order Type': 'SL-M'})
    exit = create_orders(exit_orders, rename=rename, **columns)

    # File generation
    entry.append(exit, sort=False)[cols].to_csv('orders_to_place.csv', 
                       index=False, header=False)

    print('File generated for NEST')

def generate_zerodha():
    """
    Order generation for Kite Zerodha
        1. Sign up for a zerodha publisher api key at(https://kite.trade/)
        2. Update the API key in parameters
        3. This would create an html file **zerodha_order.html** in your present working directory.
        4. Open the HTML file and click the submit button to log into zerodha and place your orders.
        5. Check the updated at time to make sure that this is the latest generated order.
    """

    # List of columns to be included in the output
    cols = [
       'tradingsymbol', 'exchange', 'transaction_type', 'order_type',
        'quantity', 'product', 'validity', 'price', 'trigger_price'
    ]

    # These columns are common for all orders - columns with a single name
    columns = {
        'exchange': 'NSE',
        'product': 'MIS',
        'validity': 'DAY',
        'order_type': 'SL'
    }

    # These are columns to be renamed
    rename = {
        'order': 'transaction_type',
        'price': 'Price',
        'qty': 'quantity',
        'trigger_price': 'trigger_price',
        'price': 'price' ,
        'SYMBOL': 'tradingsymbol'
    }

    # Generating orders in the required format
    entry_orders = orders.copy()
    entry = create_orders(entry_orders, rename=rename, **columns)

    # Exit orders order type and price to be changed
    exit_orders = orders.copy()
    exit_orders['order'] = 'BUY'
    exit_orders['price'] = 0
    exit_orders['trigger_price'] = stop_loss(orders['price'], 3, order='S').round(2)
    columns.update({'order_type': 'SL-M'})
    exit = create_orders(exit_orders, rename=rename, **columns)
    trades = entry.append(exit, sort=False)[cols].to_dict(orient='records')

    # Order HTML file generated
    env = Environment(loader=FileSystemLoader('.'))
    template = env.get_template('template.html')
    output_from_parsed_template = template.render(api_key = APIKEY,
                                                  orders=json.dumps(trades), 
                                                  date=str(datetime.datetime.now()))

    with open('zerodha_order.html', 'w') as f:
        f.write(output_from_parsed_template)
        print('Zerodha order file generated')

if __name__ == "__main__":
    generate_nest()
    generate_zerodha()


