import pandas as pd
import numpy as np

from bokeh.io import curdoc
from bokeh.layouts import row, column, gridplot, layout
from bokeh.palettes import Spectral6
from bokeh.models import ColumnDataSource, Range1d
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
    pct_pivot = pivot.pct_change()*100
    return (list(pivot.columns), pivot.reset_index())

output_file('futures_oi.html')
df = load_data()
symbols = list(df.symbol.unique())
source = ColumnDataSource()

# Create widgets
select_symbol = Select(options=symbols, title='Select a symbol',
    value='NIFTY')
button = Button(label='Refresh', button_type="success")

# Create plots
p = figure(title='Open interest chart for NIFTY futures')
cols, data = get_open_interest(df, 'NIFTY')
colors = Spectral6[:len(cols)]
source.data = source.from_df(data)
print(cols, colors)
p.vbar_stack(cols, width=0.6, x='index', color=colors, source=source)

# setup callbacks
def update():
    symbol = select_symbol.value
    cols, data = get_open_interest(df, symbol)
    source.data = source.from_df(data)
    max_val = data.sum(axis=1).max()
    print(cols, symbol, max_val)
    p.y_range = Range1d(100, max_val)
    p.title.text = 'Open interest chart for {} futures'.format(symbol)


# set up event triggers
button.on_click(update)


# Display the dashboard
l = layout(
    column(
        row(select_symbol,button),
        p)
    )

curdoc().add_root(l)
show(l)