from flask import Flask, Response, request, abort
import pandas as pd
import os

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


if __name__ == "__main__":
	# Run in debug mode when executed directly. In production use a WSGI server.
	app.run(host="0.0.0.0", port=5000, debug=True)
