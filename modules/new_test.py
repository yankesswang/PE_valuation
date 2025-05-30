from utils import fetch_url, parse_html, extract_percentage
import re, json
from names import ratio_names, forecast_names

ticker = "NVDA"  # Example ticker symbol, replace with actual ticker
# url = f"https://stockanalysis.com/stocks/{ticker}/statistics/"
url = f"https://stockanalysis.com/stocks/{ticker}/forecast/"
headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)'
                      ' Chrome/91.0.4472.124 Safari/537.36'
        }

response = fetch_url(url,headers)
soup = str(parse_html(response.text))
# print(soup)

def clean_soup_value(soup):
    """Clean and convert the value to a numeric type if applicable."""  
    clean_soup = soup.split('const data = ')[1].split(";")[0]
    data_string = clean_soup.replace("void 0", "null")
    data_string = re.sub(r'([{,]\s*)([a-zA-Z_$][a-zA-Z0-9_$]*)(:)', r'\1"\2"\3', data_string)
    data_string = data_string.replace("'", '"')
    return data_string

data_string = clean_soup_value(soup)    
# print(data_string)

r_string = data_string.split("quarterly")
j_string = r_string[-1].split("estimatesCharts")[0]

json_part = j_string[2:-4]
# json_part = json_part.replace("[PRO]", '0.0').replace("null", "None").replace("undefined", "None")
json_part = json_part.replace("[PRO]", 'null') # Assuming [PRO] should become a number
json_part = json_part.replace("undefined", "null").strip() # Convert 'undefined' to JSON 'null'
json_part = re.sub(r'(?<!\d)(-\.)(\d+)', r'-0.\2', json_part) # Handles -.X (e.g., -.5 -> -0.5)
json_part = re.sub(r'(?<!\d)(\.)(\d+)', r'0.\2', json_part)   # Handles .X (e.g., .5 -> 0.5)

print(json_part)
# json_part = '{"eps":[0.6,0.67,0.78, 0.900845,0.76,1.0660734,1.1671146,1.2944412,1.3194720000000002,1.3815594,0.0,0.0]}'

print(json.loads(json_part))