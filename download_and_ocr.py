import urllib.request
import os
import subprocess
import ssl
import sys
import json
from concurrent.futures import ThreadPoolExecutor
from process_pdf import process_pdf, get_ocr_reader

ssl._create_default_https_context = ssl._create_unverified_context

def main():
    community_name = sys.argv[1] if len(sys.argv) > 1 else "output"
    json_file = f"{community_name}_data.json"
    
    # 未來由 Subagent 將網址列表存入此 json
    if os.path.exists(json_file):
        with open(json_file, 'r', encoding='utf-8') as f:
            pdf_data = json.load(f)
    else:
        # Fallback 測試資料
        pdf_data = [
            ("北新路 182巷32號 16樓之11", "新ＯＯＯＯＯ (2025/05/31)", "https://docs.evertrust.com.tw/ycut/pdf/25151062qQjoO7rOB5RyN4QpCt5xw/.pdf/"),
            ("北新路 182巷16號 15樓之4", "新ＯＯＯＯＯ (2025/10/17)", "https://docs.evertrust.com.tw/ycut/pdf/25290063h2OimbcVpwF9WHwtWMQNV/.pdf/"),
            ("北新路 182巷32號 14樓之4", "新ＯＯＯＯＯ (2025/08/21)", "https://docs.evertrust.com.tw/ycut/pdf/25233063N0rUEWxs7F9ZiGsIUVtD1/.pdf/"),
            ("北新路 182巷16號 6樓之5", "新ＯＯＯＯＯ (2025/10/17)", "https://docs.evertrust.com.tw/ycut/pdf/25290061MW6mseHeS2u7ZceJmbxjH/.pdf/"),
            ("北新路 182巷32號 5樓之5", "新ＯＯＯＯＯ (2025/10/17)", "https://docs.evertrust.com.tw/ycut/pdf/25290060QoTOgNGtz7bSzIeVHJd0r/.pdf/"),
            ("北新路 182巷16號 4樓之5", "新ＯＯＯＯＯ (2025/08/05)", "https://docs.evertrust.com.tw/ycut/pdf/25217067cDlRMK58GLaxideT1Ztu3/.pdf/"),
            ("北新路 182巷32號 3樓之1", "新ＯＯＯＯＯ (2025/10/17)", "https://docs.evertrust.com.tw/ycut/pdf/25290062DUPoIQES2GXj4fCFhJzWd/.pdf/"),
            ("北新路 182巷16號 1樓", "新ＯＯＯＯＯ (2024/10/22)", "https://docs.evertrust.com.tw/ycut/pdf/24296062nwWi4h3LHLjJ63YzP7k7j/.pdf/"),
            ("北新路 182巷18號 1樓", "新ＯＯＯＯＯ (2024/05/13)", "https://docs.evertrust.com.tw/ycut/pdf/24135066u0r2cU6UgB12Z7i3bfhuc/.pdf/")
        ]
        print(f"提示: 找不到 {json_file}，使用內建的 Hi-City 測試資料。")
        
    download_dir = "pdfs"
    if not os.path.exists(download_dir):
        os.makedirs(download_dir)

    def process_item(item):
        i, data = item
        # 兼容 array 和 json dict 結構
        if isinstance(data, dict):
            addr = data.get("address", "")
            owner = data.get("owner", "")
            url = data.get("url", "")
        else:
            addr, owner, url = data
            
        pdf_path = os.path.join(download_dir, f"{community_name}_file_{i}.pdf")
        try:
            print(f"Downloading {url} to {pdf_path}")
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req) as response, open(pdf_path, 'wb') as out_file:
                out_file.write(response.read())
                
            print(f"Downloaded, processing text for {addr}...")
            # 傳遞 community_name 給 process_pdf 進行處理
            process_pdf(pdf_path, addr, owner, community_name)
        except Exception as e:
            print(f"Failed to process {addr}: {e}")

    import pandas as pd
    # 預先初始化 CSV 表頭避免多執行緒寫入時的競態條件 (Race Condition)
    csv_file = f"{community_name}.csv"
    if not os.path.exists(csv_file):
        pd.DataFrame(columns=["下拉選單地址", "所有權人姓名", "擷取到的地址文字"]).to_csv(csv_file, index=False, encoding='utf-8-sig')

    # 預先載入 OCR 模型，避免多執行緒競爭下載
    print("正在初始化 OCR 模型 (首次使用需下載，請稍候)...")
    get_ocr_reader()
    print("OCR 模型就緒！")

    # 使用多執行緒同時下載與處理
    print(f"開始多線程處理社區: {community_name}，共 {len(pdf_data)} 筆。")
    with ThreadPoolExecutor(max_workers=5) as executor:
        executor.map(process_item, enumerate(pdf_data))
    print(f"處理完成！結果已儲存至 {community_name}.csv")

if __name__ == "__main__":
    main()
