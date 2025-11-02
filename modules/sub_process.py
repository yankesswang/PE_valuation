# run_all.py
import subprocess
import threading
import os

def run_script(script):
    os.system(f'python3 {script}')
# 三個 Python 檔案
scripts = ['ratio_scraper.py', 'pe_scraper.py', 'forecast_scarper.py']

# 同時啟動

threads = []
for script in scripts:
    t = threading.Thread(target=run_script, args=(script,))
    t.start()
    threads.append(t)

for t in threads:
    t.join()