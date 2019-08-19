import pandas as pd
import numpy as np

from bokeh.io import curdoc
from bokeh.layouts import row, column, gridplot, layout
from bokeh.palettes import Spectral6, Dark2
from bokeh.models import ColumnDataSource, Range1d, LinearAxis, NumeralTickFormatter
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
    columns = pivot.columns
    pivot['combined_oi'] = pivot.sum(axis=1)
    return (columns, pivot.reset_index())

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

output_file('futures_oi.html')
df = load_data()
symbols = list(df.symbol.unique())
source = ColumnDataSource()
prices = ColumnDataSource()
pct_chg = ColumnDataSource()


# Create widgets
select_symbol = Select(options=symbols, title='Select a symbol',
    value='NIFTY')
button = Button(label='Refresh', button_type="success")

# Create plots
p = figure(title='Open interest chart for NIFTY futures',
    x_axis_type='datetime',
    tooltips=[
        ('date', '@date'),
        ('combined OI', '@combined_oi{0 a}'),
        ('expiry_at', '$name q:@$name{0.0 a}')
    ],background_fill_color='beige', background_fill_alpha=0.4)
cols, data = get_open_interest(df, 'NIFTY')
data['date'] = data.timestamp.dt.date
colors = Dark2[6][:len(cols)]
source.data = source.from_df(data)
p.yaxis[0].formatter = NumeralTickFormatter(format='0.00 a')
p.vbar_stack(cols, width=3.6e7, x='date', color=colors, source=source, fill_alpha=0.7)

price_data = get_price_oi(df, 'NIFTY')
prices.data = prices.from_df(price_data)
h0 = price_data['close'].max()
l0 = price_data['close'].min()
h1 = price_data['open_int'].max()
l1 = price_data['open_int'].min()

p2 = figure(title='Price vs Open Interest', 
    x_axis_type='datetime', y_range=(l0,h0),
    tooltips = [
        ('date', '@timestamp{%F}'),
        ('value', '$y{0.00 a}')
    ],
    background_fill_color='beige', background_fill_alpha=0.4)
p2.line('timestamp', 'close', line_width=2, source=prices)
p2.extra_y_ranges = {'foo': Range1d(l1,h1)}
p2.line('timestamp', 'open_int', source=prices, y_range_name='foo',
    line_color='firebrick', line_width=2)
p2.add_layout(LinearAxis(y_range_name='foo'), 'right')
p2.yaxis[1].formatter = NumeralTickFormatter(format='0.0 a')
p2.hover.formatters = {'timestamp': 'datetime'}

pct_change = data[['date', 'combined_oi']].copy()
pct_change['date'] = pd.to_datetime(pct_change['date'])
pct_change['chg'] = pct_change.combined_oi.pct_change()
pct_chg.data = pct_chg.from_df(pct_change)
p3 = figure(title='Change in open_interest',
    x_axis_type='datetime',
    tooltips=[
        ('change', '$y{0.00%}')
    ],
    background_fill_color='beige', background_fill_alpha=0.4)
p3.vbar(x='date', top='chg', width=3.6e7, 
    fill_alpha=0.7, color='gold', source=pct_chg)


# setup callbacks
def update():
    symbol = select_symbol.value
    cols, data = get_open_interest(df, symbol)
    data['date'] = data.timestamp.dt.date.astype(str)
    max_val = data[cols].sum().max()
    p.y_range.start = 0
    p.y_range.end = max_val
    p.title.text = 'Open interest chart for {} futures'.format(symbol)
    source.data = source.from_df(data)
    pdata = get_price_oi(df, symbol)
    h0 = pdata['close'].max()
    l0 = pdata['close'].min()
    h1 = pdata['open_int'].max()
    l1 = pdata['open_int'].min()
    print(symbol, l0, h0, l1, h1)
    prices.data = prices.from_df(pdata)
    p2.y_range.start = l0
    p2.y_range.end = h0
    p2.extra_y_ranges['foo'].start = l1
    p2.extra_y_ranges['foo'].end = h1
    pct_change = data[['date', 'combined_oi']].copy()
    pct_change['chg'] = pct_change.combined_oi.pct_change()
    pct_chg.data = pct_chg.from_df(pct_change)  


# set up event triggers
button.on_click(update)

grid = gridplot([p2,p,p3], ncols=1, plot_width=640, plot_height=180)
# Display the dashboard
l = layout(
        row(select_symbol,button),
        grid
    )

curdoc().add_root(l)
show(l)