# TRG Week 43

## $DIS (Disney)

- A large U.S. multinational bank offering consumer & commercial banking, investment services, and wealth/asset management.

- https://www.kaggle.com/borismarjanovic/datasets

### 1st Commit

- Flask API added: serves `dis.us.txt` as an HTML table at `/data` (see `app/data.py`).

### 2nd Commit

- Removed `OpenInt` column and split the dataset into three time-based DataFrames for further analysis (see `app/data.py`).

### 3rd Commit

- Added `/dividends` route that computes quarterly percent returns (Close price) for each of the three partitions and returns a PNG visualization (or JSON via `?show=json`).

### 4th Commit

- Added `/ma180` route that computes and visualizes the 180-day moving average of Close for each of the three partitions (PNG plot or `?show=json`).

### 5th Commit

- Added `/vol180` route that computes and visualizes the 180-day rolling (annualized) volatility of daily returns for each partition (PNG plot or `?show=json`).