import pandas as pd
import numpy as np

from bokeh.io import curdoc
from bokeh.layouts import row, column, gridplot, layout
from bokeh.palettes import Spectral6
from bokeh.models import ColumnDataSource
from bokeh.models.widgets import Select, Button
from bokeh.plotting import figure, output_file, show


def load_data():
    """
    Load all data into memory
    return a dataframe with all the data.
    This should be called only once with all data being fetched
    """
    return pd.read_hdf('~/Desktop/todaydata.h5')

def get_open_interest(data, symbol):
    """
    Given data and symbol, return the expiry dates and
    open_interest for various expiry dates in columns
    data
        dataframe with all the data
    symbol
        symbol to extract
    return a 2-tuple with list of column names and 
    a dataframe with open interest
    """
    temp = data[data.symbol == symbol]
    cols = ['timestamp', 'expiry_dt', 'open_int']
    pivot = temp.pivot(index='timestamp', columns='expiry_dt', values='open_int')
    pivot.rename(lambda x: x.strftime('%Y-%m-%d'),
                axis='columns', inplace=True)
    return (list(pivot.columns), pivot.reset_index())

def main():
    output_file('futures_oi.html')
    df = load_data()
    symbols = list(df.symbol.unique())
    source = ColumnDataSource()
    
    # Create widgets
    select_symbol = Select(options=symbols, title='Select a symbol')


    # Create plots
    p = figure(title='Open interest chart for futures')
    cols, data = get_open_interest(df, 'SBIN')
    colors = Spectral6[:len(cols)]
    source.data = source.from_df(data)
    print(cols, colors)
    p.vbar_stack(cols, width=0.6, x='index', color=colors, source=source)

    # Display the dashboard
    l = layout(
        row([select_symbol, p])
        )
    show(l)


if __name__ == "__main__":
    main()