import re
import logging
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
from tqdm import tqdm
import time, random
# Configure logging
logging.basicConfig(
    filename='scrape_pe_ratio.log',
    filemode='a',
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def scrape_pe_ratio(url, timeout=30):
    """
    Scrape the 5Y PE average from FinanceCharts by retrieving the full HTML and parsing it.

    Args:
        url (str): The URL to scrape.
        timeout (int): Maximum time to wait for the page to load.

    Returns:
        float: The 5Y PE average value, or None if extraction fails.
    """
    # Set up Chrome options
    chrome_options = Options()
    chrome_options.add_argument('--headless')  # Run in headless mode
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                                "AppleWebKit/537.36 (KHTML, like Gecko) "
                                "Chrome/85.0.4183.102 Safari/537.36")

    # Initialize the driver using webdriver-manager
    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
    except WebDriverException as e:
        logger.error(f"WebDriver initialization failed for URL {url}: {e}")
        return None

    try:
        logger.info(f"Navigating to {url}")
        driver.get(url)

        # Implicit wait to allow dynamic content to load
        driver.implicitly_wait(10)  # Wait up to 10 seconds for elements to load

        # Retrieve the full page HTML
        page_html = driver.page_source
        logger.info(f"Retrieved page HTML successfully for URL {url}")

    except Exception as e:
        logger.error(f"Error while loading the page {url}: {e}")
        return None
    finally:
        driver.quit()
        logger.info(f"WebDriver closed for URL {url}")

    # Parse the HTML with BeautifulSoup
    soup = BeautifulSoup(page_html, 'html.parser')

    # Locate the specific <div> containing the PE ratio
    try:
        # Find all divs with class 'col faq'
        divs = soup.find_all('div', class_='col faq')
        logger.info(f"Found {len(divs)} div(s) with class 'col faq' in URL {url}")

        for div in divs:
            # Check if the div contains the specific text pattern
            if '5 year average price to earnings ratio' in div.text.lower():
                # Find the <b> tag within this div
                b_tag = div.find('b')
                if b_tag:
                    pe_text = b_tag.get_text(strip=True)
                    logger.info(f"Found PE text: '{pe_text}' in URL {url}")

                    # Extract the numerical value using regex
                    match = re.search(r'([\d,]+\.\d+)', pe_text)
                    if match:
                        pe_value = float(match.group(1).replace(',', ''))
                        logger.info(f"Extracted 5Y PE Average: {pe_value} for URL {url}")
                        return pe_value
                    else:
                        logger.error(f"Regex did not match the PE ratio format in URL {url}. PE Text: '{pe_text}'")
                else:
                    logger.error(f"No <b> tag found within the target div in URL {url}.")

        logger.error(f"Failed to locate the 5Y PE average in the HTML for URL {url}.")
        return None

    except Exception as e:
        logger.error(f"Error while parsing the HTML for URL {url}: {e}")
        return None

# Define the stock list as per the user's input
stock_list = {
    "大科技": {"GOOG","META","AMZN","NFLX","AAPL","MSFT","TSLA", "ADBE"},
    "航空郵輪": {"AAL","LUV","DAL","UAL","ALK","BA","EADSY","CCL","RCL"},
    "銀行": {"BAC","JPM","GS","C","WFC","BLK",'NU','SOFI'},
    "傳統": {"DIS","ISRG","UNH","ABBV","CVS",'TRV'},
    "支付": {"MA","V","PYPL","AXP"},
    "零售": {"LULU","GPS","COST","PG","KR","JWN","NKE","DG","FL","LVMHF","EL","PVH","TPR"},
    "食品": {"TSN","MCD","SBUX","KO","PEP","CMG","YUM",'PEP','CMG','DPZ','CAKE','JACK', 'PLAY','FIZZ', 'BLMN', 'DENN', 'DIN'},
    "半導體": {'NVDA',"TSM","AMD","QCOM","MU","INTC","ASML","SWKS","QRVO","AVGO","AMAT", 'MRVL', 'ARM', 'CLS','DELL', 'HPE'},
    "原油": {"CVX","VLO","COP","XOM","OXY","CPE","ENB"},
    "旅遊": {"BKNG","EXPE","MAR","HLT","ABNB","H","WYNN","IHG","LVS","MGM"},
    "工業": {'NEE',"DE","HD","APD","CAT","ETN","HON","WM","GE","MMM","SUM","X",'ENPH','SEDG', "FSLR"},
}

def main():
    # Initialize a list to store the results
    results = []

    # Iterate through each sector and its stocks
    for sector, stocks in stock_list.items():
        logger.info(f"Processing sector: {sector} with {len(stocks)} stocks.")
        for stock in tqdm(stocks, desc=f"Sector: {sector}", unit="stock"):
            url = f"https://financecharts.com/stocks/{stock}/valuation/pe-ratio"
            pe_ratio = scrape_pe_ratio(url)
            if pe_ratio is not None:
                results.append({
                    "Sector": sector,
                    "Stock": stock,
                    "5Y_PE_Average": pe_ratio
                })
                print(f"{stock} 5Y PE Average: {pe_ratio}")
            else:
                results.append({
                    "Sector": sector,
                    "Stock": stock,
                    "5Y_PE_Average": 0
                })
                print(f"Failed to extract PE ratio for {stock}. Set to 0.")
            # time.sleep(random.uniform(1, 3))  # 随机延时1到3秒

    # Create a pandas DataFrame from the results
    df = pd.DataFrame(results)

    # Optionally, you can sort the DataFrame
    df = df.sort_values(by=["Sector", "Stock"]).reset_index(drop=True)

    # Save the DataFrame to a CSV file
    df.to_csv("stock_pe_ratios.csv", index=False, encoding='utf-8-sig')
    logger.info("Saved all PE ratios to 'stock_pe_ratios.csv'.")

    print("\nScraping completed. Results saved to 'stock_pe_ratios.csv'.")

if __name__ == "__main__":
    main()
