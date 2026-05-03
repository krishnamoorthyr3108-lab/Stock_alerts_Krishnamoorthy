import yfinance as yf
import pandas as pd
import json
import smtplib
import os
from email.mime.text import MIMEText
from datetime import datetime

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

# =========================
# LOAD STOCK LIST
# =========================
stocks_df = pd.read_csv("stocks.csv")

# =========================
# FETCH DATA
# =========================
def fetch_data(symbols):
    data = yf.download(symbols, period="10d", interval="1d", group_by="ticker")
    return data

# =========================
# PROCESS
# =========================
def process():
    symbols = stocks_df['symbol'].tolist()
    data = fetch_data(symbols)

    results = []

    for symbol in symbols:
        try:
            df = data[symbol].dropna()

            if len(df) < 5:
                continue

            # Current + Previous close
            current_price = df['Close'].iloc[-1]
            prev_price = df['Close'].iloc[-2]

            # Return %
            return_1d = ((current_price - prev_price) / prev_price) * 100

            # Avg volume (last 5 days)
            avg_vol = df['Volume'].tail(5).mean()

            # Market cap
            market_cap = stocks_df.loc[stocks_df['symbol'] == symbol, 'market_cap'].values[0]

            # FILTER CONDITIONS
            if (
                return_1d > RETURN_THRESHOLD and
                market_cap > MIN_MARKET_CAP and
                avg_vol > MIN_VOLUME and
                current_price > MIN_PRICE
            ):
                results.append({
                    "symbol": symbol,
                    "return": round(return_1d, 2),
                    "price": round(current_price, 2),
                    "avg_vol": int(avg_vol)
                })

        except Exception as e:
            print(f"Error processing {symbol}: {e}")

    return results

# =========================
# EMAIL ALERT
# =========================
def send_email(results):
    if not results:
        print("No alerts")
        return

    body = "Stocks matching criteria:\n\n"
    for r in results:
        body += f"{r['symbol']} | Return: {r['return']}% | Price: {r['price']} | Vol: {r['avg_vol']}\n"

    msg = MIMEText(body)
    msg['Subject'] = "🚨 Stock Alert"
    msg['From'] = EMAIL_SENDER
    msg['To'] = EMAIL_RECEIVER
... 
...     server = smtplib.SMTP("smtp.gmail.com", 587)
...     server.starttls()
...     server.login(EMAIL_SENDER, EMAIL_PASSWORD)
...     server.send_message(msg)
...     server.quit()
... 
... # =========================
... # STATE TRACKING (Avoid duplicate alerts)
... # =========================
... def load_last():
...     try:
...         with open("last_run.json", "r") as f:
...             return json.load(f)
...     except:
...         return []
... 
... def save_last(data):
...     with open("last_run.json", "w") as f:
...         json.dump(data, f)
... 
... # =========================
... # MAIN
... # =========================
... def main():
...     print(f"Running at {datetime.now()}")
... 
...     results = process()
...     last = load_last()
... 
...     # Send only new alerts
...     new_results = [r for r in results if r['symbol'] not in last]
... 
...     send_email(new_results)
... 
...     # Save current symbols
...     save_last([r['symbol'] for r in results])
... 
... if __name__ == "__main__":
