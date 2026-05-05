import yfinance as yf
import pandas as pd
import json
import smtplib
import os
from email.mime.text import MIMEText
from datetime import datetime, date
import time

# =========================
# CONFIG
# =========================
EMAIL_SENDER = os.getenv("EMAIL_SENDER")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
EMAIL_RECEIVER = os.getenv("EMAIL_RECEIVER")

RETURN_THRESHOLD = 5
MIN_MARKET_CAP = 500
MIN_VOLUME = 50000
MIN_PRICE = 20

BATCH_SIZE = 150

# =========================
# LOAD DATA
# =========================
stocks_df = pd.read_csv("stocks.csv")
sector_df = pd.read_csv("sector_map.csv")

all_symbols = stocks_df['symbol'].tolist()

# =========================
# FETCH DATA
# =========================
def fetch_batch(symbols):
    return yf.download(
        tickers=" ".join(symbols),
        period="10d",
        interval="1d",
        group_by="ticker",
        threads=True
    )

# =========================
# PROCESS
# =========================
def process_all():
    results = []

    for i in range(0, len(all_symbols), BATCH_SIZE):
        batch = all_symbols[i:i+BATCH_SIZE]
        print(f"Processing {i} → {i+len(batch)}")

        data = fetch_batch(batch)

        for symbol in batch:
            try:
                if symbol not in data:
                    continue

                df = data[symbol].dropna()

                if len(df) < 5:
                    continue

                current_price = df['Close'].iloc[-1]
                prev_price = df['Close'].iloc[-2]

                return_1d = ((current_price - prev_price) / prev_price) * 100
                avg_vol = df['Volume'].tail(5).mean()

                results.append({
                    "symbol": symbol,
                    "return": round(return_1d, 2),
                    "price": round(current_price, 2),
                    "avg_vol": int(avg_vol)
                })

            except Exception as e:
                print(f"Error {symbol}: {e}")

        time.sleep(1)

    return pd.DataFrame(results)

# =========================
# EMAIL
# =========================
def send_email(df, sector_summary):
    if df.empty:
        print("No alerts")
        return

    if not (EMAIL_SENDER and EMAIL_PASSWORD and EMAIL_RECEIVER):
        print("Email not configured")
        return

    body = "🚨 STOCK ALERTS\n\n"

    for _, r in df.iterrows():
        body += f"{r['symbol']} | {r['sector']} | {r['return']}% | Vol:{r['avg_vol']}\n"

    body += "\n📊 SECTOR STRENGTH\n\n"

    for sector, row in sector_summary.iterrows():
        body += f"{sector} → {round(row['avg_return'],2)}% ({row['stock_count']} stocks)\n"

    msg = MIMEText(body)
    msg['Subject'] = "Stock Screener Alert"
    msg['From'] = EMAIL_SENDER
    msg['To'] = EMAIL_RECEIVER

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        server.send_message(msg)
        server.quit()
        print("📧 Email sent!")
    except Exception as e:
        print("Email failed:", e)

# =========================
# STATE TRACKING
# =========================
def load_last():
    try:
        with open("last_run.json", "r") as f:
            return json.load(f)
    except:
        return {}

def save_last(data):
    with open("last_run.json", "w") as f:
        json.dump(data, f)

# =========================
# MAIN
# =========================
def main():
    print(f"Running at {datetime.now()}")

    df = process_all()

    if df.empty:
        print("No stocks found")
        return

    # Merge sector + market cap
    df = df.merge(sector_df, on="symbol", how="left")
    df['sector'] = df['sector'].fillna("Unknown")
    df['market_cap'] = df['market_cap'].fillna(0)

    # Apply Screener Filters
    df = df[
        (df['return'] > RETURN_THRESHOLD) &
        (df['market_cap'] > MIN_MARKET_CAP) &
        (df['avg_vol'] > MIN_VOLUME) &
        (df['price'] > MIN_PRICE)
    ]
    
    df.to_csv("latest_results.csv", index=False)

    print("\n🔍 STOCK RESULTS:")
    print(df)

    # Sector analysis
    sector_summary = df.groupby("sector").agg(
        stock_count=("symbol", "count"),
        avg_return=("return", "mean")
    ).sort_values(by="avg_return", ascending=False)

    print("\n📊 SECTOR STRENGTH:")
    print(sector_summary)

    today = str(date.today())
    last_data = load_last()

    if last_data.get("date") == today:
        last_symbols = last_data.get("symbols", [])
    else:
        last_symbols = []

    new_df = df[~df['symbol'].isin(last_symbols)]

    send_email(new_df, sector_summary)

    save_last({
        "date": today,
        "symbols": df['symbol'].tolist()
    })


if __name__ == "__main__":
    main()