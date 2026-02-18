from flask import Flask, render_template, request
import yfinance as yf
import pandas as pd
import numpy as np

app = Flask(__name__)

def calculate_rsi(data, window=14):
    delta = data['Close'].diff()

    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.rolling(window=window).mean()
    avg_loss = loss.rolling(window=window).mean()

    rs = avg_gain / avg_loss.replace(0, np.nan)
    rsi = 100 - (100 / (1 + rs))

    return rsi


@app.route("/", methods=["GET", "POST"])
def home():
    signal = None
    error = None

    if request.method == "POST":
        stock = request.form["stock"].upper().strip()

        try:
            data = yf.download(stock, start="2022-01-01", progress=False)

            if data.empty:
                error = "Invalid stock symbol or no data found."
                return render_template("index.html", signal=None, error=error)

            if isinstance(data.columns, pd.MultiIndex):
                data.columns = data.columns.get_level_values(0)

            data['MA_50'] = data['Close'].rolling(50).mean()
            data['MA_200'] = data['Close'].rolling(200).mean()
            data['RSI'] = calculate_rsi(data)

            data = data.dropna()

            if data.empty:
                error = "Not enough data to calculate indicators."
                return render_template("index.html", signal=None, error=error)

            last = data.iloc[-1]

            if last['MA_50'] > last['MA_200'] and last['RSI'] < 70:
                signal = "BUY"
            elif last['MA_50'] < last['MA_200'] and last['RSI'] > 30:
                signal = "SELL"
            else:
                signal = "HOLD"

        except Exception as e:
            error = str(e)

    return render_template("index.html", signal=signal, error=error)


# IMPORTANT: Do NOT use debug=True in production
if __name__ == "__main__":
    app.run()
