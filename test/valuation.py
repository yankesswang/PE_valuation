
from bs4 import BeautifulSoup
import requests
import pandas as pd
import re
from io import StringIO
import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
from requests.exceptions import RequestException

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
current_year = 2025
next_year = current_year + 1

# Year suffixes for the column names
current_year_suffix = str(current_year)[-2:]  # Takes the last two digits of the year
next_year_suffix = str(next_year)[-2:]

col = ["市值", "本季", "下一季", "本年度", "下一年", "後五年", "前五年", "預估PE",
       f"{current_year_suffix}年EPS", f"{current_year_suffix}年合理價",
       f"{next_year_suffix}年EPS", f"{next_year_suffix}年合理價", 
       "五年PE MEDIAN",  "五年PE中位價",
       "股價", f"{current_year_suffix}年估值", f"{current_year_suffix}年相差百分比",
       f"{next_year_suffix}年PE中位價", f"{next_year_suffix}年估值", f"{next_year_suffix}年相差百分比"]

ind = [17,0,1,2,3,5,4,6,7,8,9,10,13,16,18,19,20,21,22,23]
bug_df = pd.DataFrame(columns=["Industry", "Company", "Issue"])
# col = ["市值","本季", "下一季", "本年度","下一年","後五年","前五年","預估PE","23年EPS","23年合理價","24年EPS","24年合理價","五年PE MIN"
# ,"五年PE MEDIAN","五年PE MAX","五年PE最低價","五年PE中位價","五年PE最高價","股價","23年估值","23年相差百分比","24年PE中位價","24年估值","24年相差百分比"]
path =  "/Users/yankesswang/Documents/PYTHON/LLM Project/openai_stock_chatbot/Industry_PE_Evaluation_2024.xlsx"

def get_stock_forecast(company):
    url = f"https://stockanalysis.com/stocks/{company}/forecast/"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            break
        except RequestException as e:
            if attempt == max_retries - 1:
                print(f"Failed to fetch data for {company} after {max_retries} attempts: {e}")
                return None
            time.sleep(2)  # Wait for 2 seconds before retrying
    
    soup = BeautifulSoup(response.text, 'html.parser')
    table = soup.find('table', {'class': 'w-full whitespace-nowrap border border-gray-200 text-right text-sm dark:border-dark-700 sm:text-base'})
    
    if not table:
        print(f"No table found for {company}")
        return None
    
    headers = [header.get('title', header.text).strip() for header in table.find_all('th')]
    rows = table.find_all('tr')[1:]  # Skip the header row
    data = []
    
    for row in rows:
        cells = row.find_all('td')
        cell_data = [cell.text.strip() for cell in cells]
        # Pad the cell_data with empty strings if it's shorter than headers
        cell_data += [''] * (len(headers) - len(cell_data))
        data.append(cell_data[:len(headers)])  # Truncate if longer than headers
    
    if not data:
        print(f"No data extracted for {company}")
        return None
    
    df = pd.DataFrame(data, columns=headers)
    
    try:
        eps_row = df[df['Fiscal Year'] == 'EPS']
        eps_2024 = eps_row['2024'].values[0] if not eps_row.empty and '2024' in df.columns else None
        eps_2025 = eps_row['2025'].values[0] if not eps_row.empty and '2025' in df.columns else None
    except KeyError as e:
        print(f"KeyError: {e}. EPS data not found for {company}")
        eps_2024, eps_2025 = None, None
    
    return {
        'company': company,
        'df': df,
        'eps_2024': eps_2024,
        'eps_2025': eps_2025
    }

with pd.ExcelWriter(path) as writer:
    for industry, company_name in stock_list.items():
        ser = pd.Series(col,index = ind)
        f = pd.DataFrame()
        f["股票代號"] = ser
    
        for company in company_name:
            result = get_stock_forecast(company)
            if not result:
                continue
            eps_2024 = result['eps_2024']
            eps_2025 = result['eps_2025']

            headers ={
                "user-agent": 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36'
            }

            web = "https://hk.finance.yahoo.com/quote/" +company + "/analysis?p=" +company #從Yahooo Finance抓取23年和24年EPS
            res = requests.get(web, headers = headers)
            res.encoding = ("utf-8")
            soup = BeautifulSoup(res.text, 'html.parser')
            data = soup.select_one('#Col1-0-AnalystLeafPage-Proxy')
            if not data:
                continue
            html_content = StringIO(data.prettify())
            dfs = pd.read_html(html_content)
            try:
                # if f"本年度  ({current_year})" in dfs[0]:
                #     current_year_col = dfs[0][f"本年度  ({current_year})"][2]
                #     earning_next_year = dfs[0][f"下一年  ({next_year})"][2]
                # elif f"本年度  ({next_year})" in dfs[0]:
                #     current_year_col = dfs[0][f"本年度  ({next_year})"][2]
                #     earning_next_year = dfs[0][f"下一年  ({next_year+1})"][2]
                # else:
                #     raise ValueError(f"Column for 本年度  ({current_year}) not found")
            
                 # 發送HTTP請求獲取網頁內容
                

                stock = pd.DataFrame((dfs[5])[["預計增長", company]], index = ind)
                
                stock = stock.rename(columns={"預計增長":"股票代號"})
                
                stock["股票代號"][4]="後五年"     #從Yahooo Finance抓取分析師預期增長率
                stock["股票代號"][5]="前五年"

                stock["股票代號"][6] = "預估PE"
                stock[company][6] = round(float(stock[company][4].replace("%","").replace('無','0')) *2)

                stock["股票代號"][7] = f"{current_year_suffix}年EPS" 
                stock[company][7] = float(eps_2024)  

                stock["股票代號"][8] = f"{current_year_suffix}年合理價"
                stock[company][8] = round(stock[company][7] * stock[company][6])

                stock["股票代號"][9] = f"{next_year_suffix}年EPS" 
                stock[company][9] = float(eps_2025) 

                stock["股票代號"][10] = f"{next_year_suffix}年合理價" 
                stock[company][10] = round(stock[company][9] * stock[company][6])
                

                web1 = "https://ycharts.com/companies/"+company+"/pe_ratio" #從ychart抓取公司過去五年度avg and median PE
                res1 = requests.get(web1, headers = headers)
                res1.encoding = ("utf-8")

                soup1 = BeautifulSoup(res1.text, 'html.parser')
                data1 = soup1.select(".key-stat")

                string = ""
                for i in range(len(data1)):
                    string += data1[i].getText()
                string= string.replace(" ","")

                num = re.findall('-?\d+\.?\d*',string)
                final =[]
                for i in range(len(num)):
                    res = round(float(num[i]))
                    if(len(str(res)) <= 4):
                        final.append(res)
        
                if len(final) < 3:
                    print(f"No data found for stock {company}. Skippcompany...")
                    continue

                
                # stock["股票代號"][11] = "五年PE MIN"
                # stock[company][11] = final[0]

                # stock["股票代號"][12] = "五年PE 平均"
                # stock[company][12] = final[2]

                
                stock["股票代號"][13] = "五年PE MEDIAN"
                stock[company][13] = final[3]

                # stock["股票代號"][14] = "五年PE最低價"
                # stock[company][14] = round(stock[company][11]*stock[company][7])

                # stock["股票代號"][15] = "五年PE平均價"
                # stock[company][15] = round(stock[company][12]*stock[company][7])
            
                stock["股票代號"][16] = "五年PE中位價"
                stock[company][16] = round(stock[company][13]*stock[company][7])


                web2 = "https://hk.finance.yahoo.com/quote/"+company+"?p="+company+"&.tsrc=fin-srch"
                res2 = requests.get(web2, headers = headers)
                res2.encoding = ("utf-8")



                soup2 = BeautifulSoup(res2.text, 'html.parser')
                data2 = soup2.select_one('#quote-summary')
                dfs2 = pd.read_html(StringIO(data2.prettify()))

                stock["股票代號"][17] = "市值"
                stock[company][17] = dfs2[1][1][0]

                stock["股票代號"][18] = "股價"
                stock[company][18] = float(dfs2[0][1][0])

                

                stock["股票代號"][19] = f"{current_year_suffix}年估值"
                if stock[company][18] > stock[company][16]:  #與現有股價進行比對，檢視股票為高估或是低估
                    stock[company][19] = "高估"
                else:
                    stock[company][19] = "低估"

                stock["股票代號"][20] = f"{current_year_suffix}年相差百分比"   #計算股價高估或低估的百分比
                if stock[company][16] != 0:
                    stock[company][20] = str(round(100*(stock[company][16]- stock[company][18])/stock[company][16]))+"%"

                stock["股票代號"][21] = f"{next_year_suffix}年PE中位價"
                stock[company][21] = round(stock[company][9]*stock[company][13])

                stock["股票代號"][22] = f"{next_year_suffix}年估值"
                if stock[company][18] > stock[company][21]:  #與現有股價進行比對，檢視股票為高估或是低估
                    stock[company][22] = "高估"
                else:
                    stock[company][22] = "低估"

                stock["股票代號"][23] = f"{next_year_suffix}年相差百分比"   #計算股價高估或低估的百分比
                if stock[company][21] != 0:
                    stock[company][23] = str(round(100*(stock[company][21]- stock[company][18])/stock[company][21]))+"%"
                f= pd.merge(f,stock)
            except Exception as e:
                # Update the bug_df with the error details
                # bug_df = bug_df.append({
                #     "Industry": industry,
                #     "Company": company,
                #     "Issue": str(e)
                # }, ignore_index=True)
                print(f"Encountered an issue with {company}: {e}")
                continue
        
        f.to_excel(writer, sheet_name = industry)
        # file = key+"23年 PE估值表.csv"  #將所有資料整合為csv檔輸出
        # f.to_csv(file, encoding='big5')
        print(f)
    print(bug_df)