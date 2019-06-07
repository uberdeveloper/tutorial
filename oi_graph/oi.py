import numpy as np
import pandas as pd
import datetime

from bokeh.io import curdoc
from bokeh.layouts import row, column
from bokeh.plotting import figure
from bokeh.models import ColumnDataSource
from bokeh.models.widgets import Select, TextInput, DatePicker, Button

# Load data, probably from a database. I am loading it directly from a file
df = pd.read_hdf('derivatives_may_2019.h5')
symbols = sorted(list(df.symbol.unique()))
source = ColumnDataSource(df)

def update_expiry_date(attrname, old, new):	
	"""
	Update expiry date for this particular symbol
	"""
	print(attrname, old, new)
	q = 'symbol == "{}"'.format(new)
	dates = sorted(df.query(q).expiry_dt.unique())
	dates = [str(dt)[:10] for dt in dates]
	expiry_select.options = dates


# Create widgets
select_symbols = Select(title='Pick a symbol', options=symbols)
expiry_select = Select(title='Select an expiry date', options=None)
date_picker = DatePicker(title='Select a date')
button = Button(label="Update", button_type="success")

# Event handlers
select_symbols.on_change('value', update_expiry_date)
date_picker.on_change('value', lambda x,y,z: print(z))

layout = column(
	row(select_symbols, expiry_select),
	row(date_picker, button)
	)

# add the layout to curdoc
curdoc().add_root(layout)

if __name__ == "__main__":
	print('Hello')


