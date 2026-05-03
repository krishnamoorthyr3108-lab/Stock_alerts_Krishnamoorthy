import pandas as pd
import yfinance as yf
import time

# =========================
# STEP 1: Get NSE stock list
# =========================
url = "https://archives.nseindia.com/content/equities/EQUITY_L.csv"
df = pd.read_csv(url)

symbols = df['SYMBOL'].tolist()

# Convert to Yahoo format
symbols = [s + ".NS" for s in symbols]

print(f"Total stocks: {len(symbols)}")

# =========================
# STEP 2: Fetch data
# =========================
data = []

for symbol in symbols:
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info

        price = info.get("currentPrice", None)
        market_cap = info.get("marketCap", None)
        sector = info.get("sector", "Unknown")

        # Convert market cap to crores
        if market_cap:
            market_cap = market_cap / 1e7

        # Apply filter
        if price and price > 20:
            data.append({
                "symbol": symbol,
                "price": round(price, 2),
                "market_cap": int(market_cap) if market_cap else 0,
                "sector": sector
            })

        print(f"Processed: {symbol}")

        time.sleep(0.5)

    except Exception as e:
        print(f"Error: {symbol}")

# =========================
# STEP 3: Save CSV
# =========================
final_df = pd.DataFrame(data)

final_df.to_csv("stocks.csv", index=False)

print("✅ stocks.csv created!")