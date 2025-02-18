import yfinance as yf
import requests
from bs4 import BeautifulSoup
import re

def get_wacc(ticker: str):
    """
    從指定的 URL 中，抓取加權平均資本成本 (WACC)。
    假設截圖中的 HTML 結構直接存在於回傳的原始碼裡。
    """
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36"
        )
    }
    url = f"https://www.gurufocus.cn/stock/{ticker.upper()}/term/wacc"
    # 1. 向目標網站發送 GET 請求
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"無法連線到 {url}，HTTP 狀態碼：{response.status_code}")
        return None

    # 2. 使用 BeautifulSoup 解析 HTML
    soup = BeautifulSoup(response.text, "html.parser")

    # 3. 找到包含 WACC 文字的 h1（根據截圖，此標籤 id 為 "term-page-title"）
    title_element = soup.find("h1", {"id": "term-page-title"})
    if not title_element:
        print("找不到 h1#term-page-title 標籤，請檢查網頁結構。")
        return None

    # 4. 取得文字，例如："蘋果加權平均資本成本 WACC % 11.33% (4期)"
    text = title_element.get_text(strip=True)
    # 5. 用正則表達式提取像 "11.33％" 這樣的數字（含百分號）
    match = re.search(r"WACC.*?(\d+(?:\.\d+)?％)", text)
    if match:
        wacc = match.group(1)
        return wacc
    else:
        return None

def get_recent_fcf(ticker_symbol):
    """
    從 yfinance 取得最新一期的自由現金流數據
    """
    ticker = yf.Ticker(ticker_symbol)
    cashflow = ticker.cashflow
    if cashflow is None or cashflow.empty:
        print("無法取得現金流數據。")
        return None

    # 嘗試以 "Free Cash Flow" 作為索引取得資料
    if "Free Cash Flow" in cashflow.index:
        recent_fcf = cashflow.loc["Free Cash Flow"].iloc[0]
        return recent_fcf
    else:
        print("找不到自由現金流數據。")
        return None

def get_net_debt(ticker_symbol):
    """
    從 balance sheet 取得淨債務：總債務扣除現金及現金等價物
    """
    ticker = yf.Ticker(ticker_symbol)
    balance_sheet = ticker.balance_sheet
    if balance_sheet is None or balance_sheet.empty:
        print("無法取得資產負債表數據，將假設淨債務為0。")
        return 0

    total_debt = 0
    cash = 0
    # 嘗試取得總債務
    if "Total Debt" in balance_sheet.index:
        total_debt = balance_sheet.loc["Total Debt"].iloc[0]
    # 嘗試取得現金（不同公司名稱可能不同）
    if "Cash" in balance_sheet.index:
        cash = balance_sheet.loc["Cash"].iloc[0]
    elif "Cash And Cash Equivalents" in balance_sheet.index:
        cash = balance_sheet.loc["Cash And Cash Equivalents"].iloc[0]
    
    net_debt = total_debt - cash
    return net_debt

def get_shares_outstanding(ticker_symbol):
    """
    從 ticker.info 取得流通在外股數
    """
    ticker = yf.Ticker(ticker_symbol)
    info = ticker.info
    if "sharesOutstanding" in info:
        return info["sharesOutstanding"]
    else:
        print("無法取得流通股數。")
        return None

def determine_terminal_growth_rate(forecast_growth_rate):
    """
    根據預測成長率動態計算永續成長率的建議值：
      - 若預測成長率低於 2%，則直接使用該值
      - 若預測成長率較高，則採用預測成長率的一半，但上限為 3%
    """
    if forecast_growth_rate < 0.02:
        return forecast_growth_rate
    else:
        suggested = forecast_growth_rate * 0.5
        return min(suggested, 0.05)

def calculate_dcf(fcf, growth_rate, discount_rate, forecast_period, terminal_growth_rate):
    """
    計算DCF估值（企業價值）
      - fcf：最新一期自由現金流
      - growth_rate：預測期間的成長率（例如0.05代表5%）
      - discount_rate：WACC/折現率（例如0.08代表8%）
      - forecast_period：預測年期（例如5年）
      - terminal_growth_rate：永續成長率（例如0.02代表2%）
    """
    discounted_fcfs = []
    # 預測各年度自由現金流並折現
    for year in range(1, forecast_period + 1):
        projected_fcf = fcf * ((1 + growth_rate) ** year)
        discounted_fcf = projected_fcf / ((1 + discount_rate) ** year)
        discounted_fcfs.append(discounted_fcf)

    # 計算預測期結束後的終值 (Gordon 永續成長模型)
    fcf_terminal = fcf * ((1 + growth_rate) ** forecast_period)
    terminal_value = fcf_terminal * (1 + terminal_growth_rate) / (discount_rate - terminal_growth_rate)
    discounted_terminal_value = terminal_value / ((1 + discount_rate) ** forecast_period)

    dcf_value = sum(discounted_fcfs) + discounted_terminal_value
    return dcf_value

# if __name__ == "__main__":
    # 輸入股票代碼與預測增長率參數
while True:
    ticker_symbol = input("請輸入股票代碼（例如 AAPL）：").strip().upper()
    try:
        growth_rate = float(input("請輸入預期自由現金流增長率（例如 0.05 代表 5%）："))
        # 透過 guruFocus 網站抓取 WACC 並轉換為小數格式
        wacc_str = get_wacc(ticker_symbol)
        if wacc_str is None:
            print("無法取得 WACC，請手動設定折現率。")
            exit()
        discount_rate = float(wacc_str.replace("％", "")) / 100
        forecast_period = 5
    except ValueError:
        print("輸入格式有誤，請重新執行程式。")
        exit()

    # 根據預測成長率動態調整永續成長率
    terminal_growth_rate = determine_terminal_growth_rate(growth_rate)
    print(f"根據預測增長率 {growth_rate*100:.2f}%，自動設定的永續成長率為 {terminal_growth_rate*100:.2f}%")

    # 取得最新一期自由現金流
    recent_fcf = get_recent_fcf(ticker_symbol)
    if recent_fcf is None:
        print("無法取得必要的自由現金流數據，程式結束。")
        exit()

    # 計算DCF企業估值
    dcf_enterprise_value = calculate_dcf(recent_fcf, growth_rate, discount_rate, forecast_period, terminal_growth_rate)
    print(f"\n股票 {ticker_symbol} 的DCF企業估值約為：${dcf_enterprise_value:,.2f}")

    # 取得淨債務
    net_debt = get_net_debt(ticker_symbol)
    print(f"{ticker_symbol} 的淨債務約為：${net_debt:,.2f}")

    # 股權價值 = 企業價值 - 淨債務
    equity_value = dcf_enterprise_value - net_debt
    print(f"{ticker_symbol} 的股權價值約為：${equity_value:,.2f}")

    # 取得流通在外的股票數
    shares_outstanding = get_shares_outstanding(ticker_symbol)
    if shares_outstanding is None or shares_outstanding == 0:
        print("無法取得流通股數或流通股數為0，無法計算每股價格。")
        exit()

    # 換算每股價格
    share_price = equity_value / shares_outstanding
    print(f"{ticker_symbol} 的每股價格估值約為：${share_price:,.2f}")
