import pandas as pd
import requests

def tick(price, tick_size=0.05):
    """
    Rounds a given price to the requested tick
    """
    return round(price / tick_size)*tick_size

def stop_loss(price, stop_loss, order='B', tick_size=0.05):
    """
    Return the stop loss for the order
    price
        price from which stop loss is to be calculated
    stop_loss
        stop loss percentage from price
    order
        the original order type - B for Buy and S for Sell
        If the original order is buy, then a sell stop
        loss is generated and vice-versa
    tick_size
        tick_size to be rounded off
    >>> stop_loss(100, 3)
    >>> 97

    Notes
    ------
    * passing a negative value may throw unexpected results
    * raises ValueError if order is other than B or S

    """
    if order == 'B':
        return tick(price * (1 - stop_loss * 0.01), tick_size)
    elif order == 'S':
        return tick(price * (1 + stop_loss * 0.01), tick_size)
    else:
        raise ValueError('order should be either B or S')

def create_orders(data, rename, **kwargs):
    """
    create an orders dataframe from an existing dataframe
    by renaming columns and providing additional columns
    data
        dataframe
    rename
        columns to be renamed as dictionary
    kwargs
        key value pairs with key being column names
        and values being dataframe values
    """
    data = data.rename(rename, axis='columns')
    for k,v in kwargs.items():
        data[k] = v
    return data

def fetch_preopen_data(url=None):
    """
    Fetch preopen data
    """
    import requests
    if url is None:
        url = "https://www1.nseindia.com/live_market/dynaContent/live_analysis/pre_open/nifty.json"
    req = requests.get(url)     
    dct = req.json()    
    agg = []
    for x in dct["data"]:
        agg.append((x["symbol"], x["perChn"], x["iep"]))
    df = pd.DataFrame(agg)
    df.columns = ["SYMBOL", "perChn", "iep"]
    df["perChn"] = df.perChn.astype("f8")
    df["iep"] = df.iep.replace(",", "", regex = True)
    df["iep"] = df.iep.astype("f8")
    df.columns = ['SYMBOL', 'PctChange', 'OpenPrice']
    return df
