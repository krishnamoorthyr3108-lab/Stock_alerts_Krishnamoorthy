import pandas as pd

# NSE stock list
url = "https://archives.nseindia.com/content/equities/EQUITY_L.csv"
df = pd.read_csv(url)

symbols = df['SYMBOL'].dropna().unique().tolist()
symbols = [s + ".NS" for s in symbols]

pd.DataFrame({"symbol": symbols}).to_csv("stocks.csv", index=False)

print(f"✅ stocks.csv created | Total: {len(symbols)}")