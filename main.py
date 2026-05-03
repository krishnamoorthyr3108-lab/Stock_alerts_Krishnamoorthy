import yfinance as yf
import pandas as pd
import json
import smtplib
import os
from email.mime.text import MIMEText
from datetime import datetime
from datetime import date
import time

# =========================
# CONFIG
# =========================
EMAIL_SENDER = os.getenv("EMAIL_SENDER")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
EMAIL_RECEIVER = os.getenv("EMAIL_RECEIVER")

RETURN_THRESHOLD = 5   # change to 5 after testing
MIN_MARKET_CAP = 500
MIN_VOLUME = 50000
MIN_PRICE = 20

BATCH_SIZE = 100   # 🔥 important to avoid rate limit

# =========================
# LOAD STOCK LIST
# =========================
stocks_df = pd.read_csv("stocks.csv")

# =========================
# FETCH DATA
# =========================
def fetch_data(symbols):
    return yf.download(
        tickers=" ".join(symbols),
        period="10d",
        interval="1d",
        group_by="ticker",
        threads=False
    )

# =========================
# PROCESS
# =========================
def process_all():
    all_symbols = stocks_df['symbol'].tolist()
    results = []

    for i in range(0, len(all_symbols), BATCH_SIZE):
        batch = all_symbols[i:i+BATCH_SIZE]
        print(f"Processing batch {i} → {i+len(batch)}")

        data = fetch_data(batch)

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

                row = stocks_df[stocks_df['symbol'] == symbol]
                market_cap = row['market_cap'].values[0]
                sector = row['sector'].values[0]

                if (
                    return_1d > RETURN_THRESHOLD and
                    market_cap > MIN_MARKET_CAP and
                    avg_vol > MIN_VOLUME and
                    current_price > MIN_PRICE
                ):
                    results.append({
                        "symbol": symbol,
                        "sector": sector,
                        "return": round(return_1d, 2),
                        "price": round(current_price, 2),
                        "avg_vol": int(avg_vol)
                    })

            except Exception as e:
                print(f"Error {symbol}: {e}")

        time.sleep(2)  # 🔥 avoid rate limit

    return pd.DataFrame(results)

# =========================
# SECTOR ANALYSIS
# =========================
def analyze_sectors(df):
    if df.empty:
        return pd.DataFrame()

    sector_summary = df.groupby("sector").agg({
        "symbol": "count",
        "return": "mean"
    }).rename(columns={
        "symbol": "stock_count",
        "return": "avg_return"
    }).sort_values(by="stock_count", ascending=False)

    return sector_summary

# =========================
# EMAIL ALERT
# =========================
def send_email(results_df, sector_df):
    if results_df.empty:
        print("No alerts to send")
        return

    if not (EMAIL_SENDER and EMAIL_PASSWORD and EMAIL_RECEIVER):
        print("Email not configured")
        return

    body = "🔥 STOCK ALERTS\n\n"

    for _, r in results_df.iterrows():
        body += f"{r['symbol']} | {r['sector']} | {r['return']}%\n"

    body += "\n📊 SECTOR SUMMARY\n\n"

    for _, r in sector_df.iterrows():
        body += f"{_} | Count: {r['stock_count']} | Avg Return: {round(r['avg_return'],2)}%\n"

    msg = MIMEText(body)
    msg['Subject'] = "🚨 Stock + Sector Alert"
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
        return []

def save_last(data):
    with open("last_run.json", "w") as f:
        json.dump(data, f)

# =========================
# MAIN
# =========================
def main():
    print(f"Running at {datetime.now()}")

    results_df = process_all()

    print("\n🔍 STOCK RESULTS:")
    print(results_df)

    sector_df = analyze_sectors(results_df)

    print("\n📊 SECTOR STRENGTH:")
    print(sector_df)

    today = str(date.today())

    last_data = load_last()

    if isinstance(last_data, dict) and last_data.get("date") == today:
        last_symbols = last_data.get("symbols", [])
    else:
        last_symbols = []

    new_df = results_df[~results_df['symbol'].isin(last_symbols)]

    send_email(new_df, sector_df)
    

    save_last({
              "date": today,
              "symbols": results_df['symbol'].tolist()
             })


if __name__ == "__main__":
    main()
