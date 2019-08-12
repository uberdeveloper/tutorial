import pandas as pd
import numpy as np

from bokeh.io import curdoc
from bokeh.layouts import row, column, gridplot, layout
from bokeh.palettes import Spectral6
from bokeh.models import ColumnDataSource, Range1d, LinearAxis
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

def get_price_oi(data, symbol):
    """
    Get the price and combined open_interest for the symbol
    data
        dataframe with all data
    symbol 
        symbol to extract data
    """
    temp = data[data.symbol == symbol]
    grouped = temp.groupby('timestamp')
    agg = grouped.agg({'open_int': sum, 'close': 'mean'}).reset_index()
    agg['date'] = agg.timestamp.dt.date.astype(str)
    agg['index'] = range(len(agg))
    return agg

def twin_plot(data, y_axis, x_axis='timestamp'):
    """
    Create a bokeh plot with twin axes
    """

    TOOLTIPS = [
    ('datetime', '@x{%F %H:%M}'),
    ('value', '$y{0.00}')
    ]

    y1,y2 = y_axis[0], y_axis[1]
    h0 = data[y1].max()
    l0 = data[y1].min()
    h1 = data[y2].max()
    l1 = data[y2].min()
    p = figure(x_axis_type='datetime', y_range=(l0, h0),
        tooltips=TOOLTIPS, height=240, width=600)
    p.line(data[x_axis].values, data[y1].values, 
        color="red", legend=y1)
    p.extra_y_ranges = {"foo": Range1d(l1,h1)}
    p.line(data[x_axis], data[y2].values, color="blue", 
        y_range_name="foo", legend=y2)
    p.add_layout(LinearAxis(y_range_name="foo", axis_label=y2), 'left')
    p.hover.formatters= {'x': 'datetime'}
    p.legend.location = 'top_center'
    p.legend.click_policy = 'hide'
    return p

output_file('futures_oi.html')
df = load_data()
symbols = list(df.symbol.unique())
source = ColumnDataSource()

# Create widgets
select_symbol = Select(options=symbols, title='Select a symbol',
    value='NIFTY')
button = Button(label='Refresh', button_type="success")

# Create plots
p = figure(title='Open interest chart for NIFTY futures',
    tooltips=[
        ('date', '@date'),
        ('value', '$y{0 a}')
    ],
    height=250)
cols, data = get_open_interest(df, 'NIFTY')
data['date'] = data.timestamp.dt.date.astype(str)
colors = Spectral6[:len(cols)]
source.data = source.from_df(data)
print(cols, colors)
p.vbar_stack(cols, width=0.6, x='index', color=colors, source=source)
price_data = get_price_oi(df, 'NIFTY')
price_chart = twin_plot(price_data, y_axis=['close', 'open_int'])

# setup callbacks
def update():
    symbol = select_symbol.value
    cols, data = get_open_interest(df, symbol)
    data['date'] = data.timestamp.dt.date.astype(str)
    source.data = source.from_df(data)
    max_val = data.sum(axis=1).max()
    print(cols, symbol, max_val)
    p.y_range = Range1d(100, max_val)
    p.title.text = 'Open interest chart for {} futures'.format(symbol)
    pdata = get_price_data(df, symbol)
    price_chart = twin_plot(pdata, y_axis=['close', 'open_int'])


# set up event triggers
button.on_click(update)


# Display the dashboard
l = layout(
    column(
        row(select_symbol,button),
        price_chart,
        p)
    )

curdoc().add_root(l)
show(l)