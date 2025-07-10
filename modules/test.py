import yfinance as yf

ticker = yf.Ticker("V")               # 任何美股代號皆可
price  = ticker.info["regularMarketPrice"]  # 也可用 ticker.info["currentPrice"]
print("Apple 近即時價格：", price)

import yfinance as yf

ticker = yf.Ticker("AAPL")          # any symbol works, e.g. TSLA, MSFT …

# Method A – using the high‑level .info dict
beta = ticker.info.get("beta")      # returns float or None
print("Yahoo‑reported beta:", beta)

# Method B – faster, lighter call (requires yfinance ≥ 0.2.18)
beta_fast = ticker.fast_info.get("beta")   # same value if available
print("beta via fast_info:", beta_fast)
