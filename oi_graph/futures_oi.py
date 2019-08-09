from bokeh.io import curdoc
from bokeh.layouts import row, column, gridplot
from bokeh.models import ColumnDataSource
from bokeh.models.widgets import Select
from bokeh.plotting import figure, output_file, show


def main():
	output_file('futures_oi.html')
	p = figure()
	show(p)


if __name__ == "__main__":
	main()