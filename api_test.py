import requests
import json
import sys
import codecs
import urllib3

# 解決 Windows sys.stdout 的 CP950 亂碼問題
sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def test_api(cookie_str):
    if not cookie_str:
        print("請提供 Cookie 字串。")
        return

    # 先改用單純的 GET 請求看看能不能拿到「進入社區二維透視」的 HTML
    url = "https://is.ycut.com.tw/magent/Community.aspx"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Cookie": cookie_str
    }

    print("發送 GET 測試請求至:", url)
    try:
        res = requests.get(url, headers=headers, timeout=10, verify=False)
        print("Status Code:", res.status_code)
        
        res.encoding = 'utf-8' # 強制 UTF-8
        
        # 用 BeautifulSoup 看看網頁裡面有沒有我們熟悉的標題或小人表格
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # 找找看有沒有社區名稱或表格
        title = soup.find('title')
        print("Page Title:", title.text if title else "無標題")
        
        # 找找看有沒有二維透視的特有元素 (例如 tb2DTable)
        table = soup.find(id="tb2DTable")
        if table:
            print("成功找到二維透視表格！總共有", len(table.find_all('tr')), "行資料。")
            
             # 找找藍色小人的點擊事件 (含有 Identifier 的資訊)
            links = table.find_all('a', onclick=lambda t: t and 'ShowPop' in t)
            print("找到", len(links), "個藍色小人圖示。")
            if links:
                 print("第一個小人的 onClick 事件:", links[0]['onclick'])
        else:
            print("沒有找到二維透視表格 tb2DTable，可能登入失敗或頁面不對。")
            
    except Exception as e:
        print("請求發生錯誤:", e)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        test_api(sys.argv[1])
    else:
        print("用法: python api_test.py '<您的 Cookie 字串>'")
