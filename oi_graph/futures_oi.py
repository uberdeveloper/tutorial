import pandas as pd
import numpy as np

from bokeh.io import curdoc
from bokeh.layouts import row, column, gridplot, layout
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



def main():
	output_file('futures_oi.html')
	df = load_data()
	symbols = list(df.symbol.unique())
	
	# Create widgets
	select_symbol = Select(options=symbols, title='Select a symbol')


	# Display the dashboard
	l = layout(
		row(select_symbol)
		)
	show(l)


if __name__ == "__main__":
	main()