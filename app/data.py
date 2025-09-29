from flask import Flask, Response, request, abort
import pandas as pd
import os
import io
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# Absolute path to the data file
FILE_PATH = r"C:\Users\avram\OneDrive\Desktop\Bloomtech TRG\TRG Week 43\dis.us.txt"

app = Flask(__name__)


def load_dataframe():
	"""Load the CSV at FILE_PATH into a pandas DataFrame.

	Raises FileNotFoundError if the path does not exist.
	"""
	if not os.path.exists(FILE_PATH):
		raise FileNotFoundError(f"Data file not found: {FILE_PATH}")
	# The file is CSV with a header; let pandas infer types
	df = pd.read_csv(FILE_PATH, parse_dates=["Date"], infer_datetime_format=True)

	# Remove the OpenInt column if present (second-commit change)
	if "OpenInt" in df.columns:
		df = df.drop(columns=["OpenInt"])

	# Ensure Date is datetime and sorted
	df["Date"] = pd.to_datetime(df["Date"]) 
	df = df.sort_values("Date").reset_index(drop=True)

	return df


def split_into_three(df):
	"""Split the dataframe into three time-based partitions.

	The split is based on equal thirds of the time span between the
	minimum and maximum dates in `df`.

	Returns (part1, part2, part3) as DataFrame objects.
	"""
	if df is None or df.empty:
		return None, None, None

	start = df["Date"].min()
	end = df["Date"].max()
	total = end - start
	cut1 = start + total / 3
	cut2 = start + 2 * total / 3

	part1 = df[df["Date"] <= cut1].copy().reset_index(drop=True)
	part2 = df[(df["Date"] > cut1) & (df["Date"] <= cut2)].copy().reset_index(drop=True)
	part3 = df[df["Date"] > cut2].copy().reset_index(drop=True)

	return part1, part2, part3


def quarterly_returns(df):
	"""Compute quarterly percent returns based on 'Close' column.

	Note: the dataset does not contain explicit dividend payments. This
	function computes quarterly percentage change of the Close price
	(as a proxy for quarterly earnings/returns). If you have a 'Dividends'
	column later, replace this logic accordingly.
	"""
	if df is None or df.empty:
		return pd.Series(dtype=float)

	q = df.set_index('Date').resample('Q')['Close'].last().pct_change().dropna()
	return q


def ma180(df):
	"""Compute 180-day moving average of the 'Close' price.

	Uses a time-based window so it handles irregular trading days.
	Returns a Series indexed by Date with the moving average (drops NaNs).
	"""
	if df is None or df.empty:
		return pd.Series(dtype=float)

	s = df.set_index('Date')['Close'].sort_index()
	# 180 calendar-day window; min_periods=1 to allow early values if desired
	ma = s.rolling('180D', min_periods=1).mean()
	return ma.dropna()


def vol180(df, annualize=True):
	"""Compute 180-day rolling volatility of daily returns.

	Returns a Series indexed by Date. If annualize=True, multiplies by sqrt(252).
	Uses time-based rolling window of 180 calendar days.
	"""
	if df is None or df.empty:
		return pd.Series(dtype=float)

	s = df.set_index('Date')['Close'].sort_index()
	daily_ret = s.pct_change().dropna()
	# rolling std over 180 calendar days
	vol = daily_ret.rolling('180D', min_periods=1).std()
	if annualize:
		vol = vol * (252 ** 0.5)
	return vol.dropna()


@app.route("/")
def index():
	"""Simple index pointing to the data endpoint."""
	html = "<p>Open <a href='/data'>/data</a> to view the dataset as an HTML table.</p>"
	return Response(html, content_type="text/html; charset=utf-8")


@app.route("/data")
def data_table():
	"""Return the dataset rendered as an HTML table.

	Optional query parameter `rows` (int) limits the number of rows shown.
	"""
	try:
		df = load_dataframe()
	except FileNotFoundError:
		abort(404, description="Data file not found on server")

	# Allow limiting the number of rows returned for faster previewing
	rows = request.args.get("rows")
	try:
		if rows is not None:
			n = int(rows)
			df = df.head(n)
	except ValueError:
		abort(400, description="Invalid `rows` parameter; must be an integer")

	# Render DataFrame to HTML. Use classes for light styling by consumer.
	table_html = df.to_html(classes="dataframe", index=False, border=0)
	page = f"<html><head><meta charset='utf-8'><title>Dataset</title></head><body>{table_html}</body></html>"
	return Response(page, content_type="text/html; charset=utf-8")


@app.route("/health")
def health():
	return {"status": "ok"}


@app.route("/dividends")
def dividends_plot():
	"""Compute quarterly returns for each partition and return a PNG plot.

	Optional query param `show` accepts 'png' (default) or 'json'.
	"""
	try:
		df = load_dataframe()
	except FileNotFoundError:
		abort(404, description="Data file not found on server")

	p1, p2, p3 = split_into_three(df)

	q1 = quarterly_returns(p1)
	q2 = quarterly_returns(p2)
	q3 = quarterly_returns(p3)

	# Create plot
	fig, ax = plt.subplots(figsize=(10, 5))
	if not q1.empty:
		ax.plot(q1.index, q1.values, label='Part 1')
	if not q2.empty:
		ax.plot(q2.index, q2.values, label='Part 2')
	if not q3.empty:
		ax.plot(q3.index, q3.values, label='Part 3')

	ax.axhline(0, color='gray', linewidth=0.5)
	ax.set_title('Quarterly Percent Returns (Close price) for 3 partitions')
	ax.set_ylabel('Quarterly pct change')
	ax.legend()

	buf = io.BytesIO()
	fig.tight_layout()
	fig.savefig(buf, format='png')
	plt.close(fig)
	buf.seek(0)

	show = request.args.get('show', 'png').lower()
	if show == 'json':
		# Return numeric data as JSON
		out = {
			'part1': q1.round(6).to_dict(),
			'part2': q2.round(6).to_dict(),
			'part3': q3.round(6).to_dict(),
		}
		return out

	return Response(buf.getvalue(), content_type='image/png')


@app.route('/vol180')
def vol180_plot():
	"""Compute 180-day rolling volatility for each partition and return PNG.

	Optional `?show=json` returns numeric series for each part.
	"""
	try:
		df = load_dataframe()
	except FileNotFoundError:
		abort(404, description="Data file not found on server")

	p1, p2, p3 = split_into_three(df)

	v1 = vol180(p1)
	v2 = vol180(p2)
	v3 = vol180(p3)

	fig, ax = plt.subplots(figsize=(10, 5))
	if not v1.empty:
		ax.plot(v1.index, v1.values, label='Part 1')
	if not v2.empty:
		ax.plot(v2.index, v2.values, label='Part 2')
	if not v3.empty:
		ax.plot(v3.index, v3.values, label='Part 3')

	ax.set_title('180-day Rolling Volatility (annualized) for 3 partitions')
	ax.set_ylabel('Volatility (annualized)')
	ax.legend()

	buf = io.BytesIO()
	fig.tight_layout()
	fig.savefig(buf, format='png')
	plt.close(fig)
	buf.seek(0)

	show = request.args.get('show', 'png').lower()
	if show == 'json':
		out = {
			'part1': v1.round(6).to_dict(),
			'part2': v2.round(6).to_dict(),
			'part3': v3.round(6).to_dict(),
		}
		return out

	return Response(buf.getvalue(), content_type='image/png')


@app.route('/ma180')
def ma180_plot():
	"""Compute 180-day moving averages for each partition and return PNG.

	Optional `?show=json` returns numeric series for each part.
	"""
	try:
		df = load_dataframe()
	except FileNotFoundError:
		abort(404, description="Data file not found on server")

	p1, p2, p3 = split_into_three(df)

	m1 = ma180(p1)
	m2 = ma180(p2)
	m3 = ma180(p3)

	fig, ax = plt.subplots(figsize=(10, 5))
	if not m1.empty:
		ax.plot(m1.index, m1.values, label='Part 1')
	if not m2.empty:
		ax.plot(m2.index, m2.values, label='Part 2')
	if not m3.empty:
		ax.plot(m3.index, m3.values, label='Part 3')

	ax.set_title('180-day Moving Average (Close price) for 3 partitions')
	ax.set_ylabel('180-day MA')
	ax.legend()

	buf = io.BytesIO()
	fig.tight_layout()
	fig.savefig(buf, format='png')
	plt.close(fig)
	buf.seek(0)

	show = request.args.get('show', 'png').lower()
	if show == 'json':
		out = {
			'part1': m1.round(6).to_dict(),
			'part2': m2.round(6).to_dict(),
			'part3': m3.round(6).to_dict(),
		}
		return out

	return Response(buf.getvalue(), content_type='image/png')


if __name__ == "__main__":
	# Run in debug mode when executed directly. In production use a WSGI server.
	app.run(host="0.0.0.0", port=5000, debug=True)
