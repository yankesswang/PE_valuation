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

    # 3. 找到包含 WACC 文字的 h1（根據您提供的截圖，id="term-page-title"）
    #    請根據實際網頁調整搜尋方式
    title_element = soup.find("h1", {"id": "term-page-title"})
    if not title_element:
        print("找不到 h1#term-page-title 標籤，請檢查網頁結構。")
        return None

    # 4. 取出文字，例如："蘋果加權平均資本成本 WACC % 11.33% (4期)"
    text = title_element.get_text(strip=True)
    # 5. 用正則表達式提取像 "11.33%" 這樣的數字（含百分號）
    # match = re.search(r"(\d+(?:\.\d+)%)", text)
    match = re.search(r"WACC.*?(\d+(?:\.\d+)％)", text)
    if match:
        wacc = match.group(1)
        return wacc
    else:
        return None

if __name__ == "__main__":
    ticker = 'AAPL'
    wacc_value = get_wacc(ticker)
    if wacc_value:
        print(f"成功取得 WACC：{wacc_value}")
    else:
        print("無法取得 WACC 或網頁結構不符合預期。")
