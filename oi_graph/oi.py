import numpy as np
import pandas as pd
import datetime

from bokeh.io import curdoc, show, output_file
from bokeh.layouts import row, column
from bokeh.plotting import figure
from bokeh.models import ColumnDataSource, FactorRange
from bokeh.models.widgets import Select, TextInput, DatePicker, Button
from bokeh.transform import factor_cmap

# Load data, probably from a database. I am loading it directly from a file
df = pd.read_hdf('derivatives_may_2019.h5')
symbols = sorted(list(df.symbol.unique()))
source = ColumnDataSource(df)

def update_expiry_date(attrname, old, new):	
	"""
	Update expiry date for this particular symbol
	"""
	q = 'symbol == "{}"'.format(new)
	dates = sorted(df.query(q).expiry_dt.unique())
	dates = [str(dt)[:10] for dt in dates]
	expiry_select.options = dates
	expiry_select.value = dates[0]
	print(select_symbols, select_symbols.value, date_picker.value)

def update_oi_chart():
	pass

def query(dataframe, symbol='NIFTY', date='2019-05-02', expiry='2019-05-30'):
	"""
	Given a dataframe and query string, return the queried data
	"""
	cond = '(symbol=="{symbol}") & (timestamp == "{dt}") & (expiry_dt=="{exp}") & (option_typ != "XX")'
	q = cond.format(symbol=symbol, dt=str(date)[:10], exp=str(expiry)[:10])
	print('QUERY IS', q)
	df2 = dataframe.query(q)[['strike_pr', 'option_typ', 'open_int']]
	df2.sort_values(by=['strike_pr'], inplace=True)
	return df2

def get_data_as_source(data):
	"""
	Get data in source format
	"""
	x = [(str(int(a)), str(b)) for a,b in zip(q.strike_pr, q.option_typ)]
	source = ColumnDataSource(data=dict(x=x, values=data.open_int.values))
	return source

def fig1():
	"""
	Generate the first figure
	"""
	q = query(df, symbol=select_symbols.value, date=date_picker.value,
		expiry=expiry_select.value)
	#q = query(df, symbol='ACC', date='2019-05-23', expiry='2019-05-30')
	if (q is None) or (len(q) == 0):
		return figure()

	x = [(str(int(a)), str(b)) for a,b in zip(q.strike_pr, q.option_typ)]
	source = ColumnDataSource(data=dict(x=x, values=q.open_int.values))

	TOOLTIPS = [
		('index', '$index'),
		('open_interest', '@values'),
		('option', '@x')   
		]
	p = figure(x_range=FactorRange(*x), 
           title="Open Interest", tooltips=TOOLTIPS,
           tools="pan,wheel_zoom,box_zoom,hover,reset")
	p.vbar(x='x', top='values', width=0.9, source=source,
      fill_color=factor_cmap('x', palette=['red', 'green'],
                                  factors=['PE', 'CE'], start=1, end=2))


def update():
	"""
	Update chart data
	"""
	data = query(df, symbol=select_symbols.value, date=date_picker.value,
	expiry=expiry_select.value)
	x_range = [(str(int(a)), str(b)) for a,b in 
		zip(data.strike_pr, data.option_typ)]
	p1.x_range.factors = x_range
	src = ColumnDataSource({'x': x_range, 'values': data.open_int.values})
	source.data = src.data



# Create widgets
select_symbols = Select(title='Pick a symbol', options=symbols)
expiry_select = Select(title='Select an expiry date', options=None)
date_picker = DatePicker(title='Select a date', 
	value=datetime.datetime.today().date())
button = Button(label="Update", button_type="success")

# Create charts
q = query(df, symbol=select_symbols.value, date=date_picker.value,
	expiry=expiry_select.value)
q = query(df, symbol='BANKBARODA')
x = [(str(int(a)), str(b)) for a,b in zip(q.strike_pr, q.option_typ)]
source = ColumnDataSource(data=dict(x=x, values=q.open_int.values))
TOOLTIPS = [
	('index', '$index'),
	('open_interest', '@values'),
	('option', '@x')   
	]
p1 = figure(x_range=FactorRange(),
	title="Open Interest", tooltips=TOOLTIPS,
	tools="pan,wheel_zoom,box_zoom,hover,reset")
p1.x_range = FactorRange(*x)
bar = p1.vbar(x='x', top='values', width=0.9, source=source,
	alpha=0.7,
	fill_color=factor_cmap('x', palette=['red', 'green'],
		factors=['PE', 'CE'], start=1, end=2))


# Event handlers
select_symbols.on_change('value', update_expiry_date)
#date_picker.on_change('value', lambda x,y,z: print(z))
button.on_click(update)

layout = column(
	row(select_symbols, expiry_select),
	row(date_picker, button),
	row(p1)
	)

# add the layout to curdoc
curdoc().add_root(layout)

if __name__ == "__main__":
	print('Hello')


