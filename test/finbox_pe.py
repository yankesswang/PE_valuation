from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import re
import time

stock_list = {
    "大科技":{"GOOG","META","AMZN","NFLX","AAPL","MSFT","TSLA", "ADBE"},
    "航空郵輪":{"AAL","LUV","DAL","UAL","ALK","BA","EADSY","CCL","RCL"},
    "銀行":{"BAC","JPM","GS","C","WFC","BLK",'NU','SOFI'},
    "傳統":{"DIS","ISRG","UNH","ABBV","CVS",'TRV'},
    "支付":{"MA","V","PYPL","AXP"},
    "零售":{"LULU","GPS","COST","PG","KR","JWN","NKE","DG","FL","LVMHF","EL","PVH","TPR"},
    "食品":{"TSN","MCD","SBUX","KO","PEP","CMG","YUM",'PEP','CMG','DPZ','CAKE','JACK', 'PLAY','FIZZ', 'BLMN', 'DENN', 'DIN'},
    "半導體":{'NVDA',"TSM","AMD","QCOM","MU","INTC","ASML","SWKS","QRVO","AVGO","AMAT", 'MRVL', 'ARM', 'CLS','DELL', 'HPE'},
    "原油":{"CVX","VLO","COP","XOM","OXY","CPE","ENB"},
    "旅遊":{"BKNG","EXPE","MAR","HLT","ABNB","H","WYNN","IHG","LVS","MGM"},
    "工業":{'NEE',"DE","HD","APD","CAT","ETN","HON","WM","GE","MMM","SUM","X",'ENPH','SEDG', "FSLR"},
    'SaaS':{'SAP SE','CFLT','ACN','BSX','SHOP','ADBE','CRM', 'DDOG', 'NOW', 'INTU', 'SQ', 'WDAY', 'SNOW', 'MDB', 'OKTA', 'ADSK' ,'TTD'}
} 
def get_pe_ratio_from_url(url):
    """
    Fetch and extract the 5-year P/E ratio using Selenium to handle dynamic content
    
    Args:
        url (str): URL of the page containing the P/E ratio
        
    Returns:
        float: The 5-year P/E ratio value
        None: If ratio cannot be found or in case of error
    """
    chrome_options = Options()
    chrome_options.add_argument('--headless')  # Run in headless mode
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    
    try:
        # Initialize the driver
        driver = webdriver.Chrome(options=chrome_options)
        driver.get(url)
        
        # Wait for the content to load (adjust timeout as needed)
        wait = WebDriverWait(driver, 20)
        
        # Wait for the specific element containing P/E ratio
        pe_element = wait.until(
            EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'avg p/e ratio (5y)')]"))
        )
        
        if pe_element:
            text = pe_element.text
            # Extract the numeric value using regex
            match = re.search(r'(\d+\.?\d*)x', text)
            if match:
                return float(match.group(1))
                
    except Exception as e:
        print(f"Error processing data: {e}")
        
    finally:
        try:
            driver.quit()
        except:
            pass
            
    return None

def main():
    for stock in stock_list['大科技']:
        url = f"https://finbox.com/NASDAQGS:{stock}/explorer/pe_ltm_avg_5y"
        pe_ratio = get_pe_ratio_from_url(url)
        if pe_ratio is not None:
            print(f"{stock} 5-year P/E Ratio: {pe_ratio}")
        else:
            print(f"{stock} Failed to extract P/E ratio")
    # url = "https://finbox.com/NASDAQGS:TSM/explorer/pe_ltm_avg_5y"
    # pe_ratio = get_pe_ratio_from_url(url)
    
    # if pe_ratio is not None:
    #     print(f"5-year P/E Ratio: {pe_ratio}")
    # else:
    #     print("Failed to extract P/E ratio")

if __name__ == "__main__":
    main()