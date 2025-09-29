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

### 5th Commit