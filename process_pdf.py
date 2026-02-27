import fitz  # PyMuPDF
import pytesseract
from PIL import Image
import pandas as pd
import sys
import os
import re

# 如果系統環境沒有將 tesseract 加入 PATH，可能需要指定安裝路徑
# pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def process_pdf(pdf_path, address_dropdown, owner_name):
    """
    處理單一 PDF，截取第二頁特定區塊進行 OCR。
    預計：擷取『建物所有權部』的地址欄位。
    """
    try:
        # 開啟 PDF
        doc = fitz.open(pdf_path)
        if len(doc) < 2:
            print(f"Error: {pdf_path} 頁數不足兩頁。")
            return
            
        # 取得第二頁 (index=1)
        page = doc[1]
        
        # 定義裁切區域 (x0, y0, x1, y1) - 這些座標需視實際 PDF 版面調整
        # 由於尚未有實際 PDF 測試，先假設一個抓取上半部偏左或特定表格位置的區域
        # 調整時，可以使用 page.rect 確認整體寬高
        rect = fitz.Rect(100, 200, 500, 400) # 假設區塊
        
        # 將該區域渲染為圖片 (放大倍率以提高 OCR 辨識率)
        zoom_x = 2.0  # horizontal zoom
        zoom_y = 2.0  # vertical zoom
        mat = fitz.Matrix(zoom_x, zoom_y)
        pix = page.get_pixmap(matrix=mat, clip=rect)
        
        # 將 pixmap 轉為 PIL Image
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        
        # 進行 OCR 辨識 (限定繁體中文 chi_tra)
        # 確保系統有安裝 tesseract 且包含 chi_tra
        text = pytesseract.image_to_string(img, lang='chi_tra')
        
        # 清理文字：去除多餘換行、空白
        clean_text = re.sub(r'\s+', '', text)
        
        # 寫入 CSV
        csv_file = "output.csv"
        file_exists = os.path.isfile(csv_file)
        
        new_row = pd.DataFrame([{
            "下拉選單地址": address_dropdown,
            "所有權人姓名": owner_name,
            "擷取到的地址文字": clean_text
        }])
        
        # a=append mode
        new_row.to_csv(csv_file, mode='a', index=False, header=not file_exists, encoding='utf-8-sig')
        print(f"Success: {pdf_path} 處理完成 -> {clean_text}")
        
    except Exception as e:
        print(f"發生錯誤 {pdf_path}: {e}")

if __name__ == "__main__":
    # 使用範例: python process_pdf.py "C:\path\to\file.pdf" "新北市淡水區XX路" "王大明"
    if len(sys.argv) >= 4:
        pdf_file = sys.argv[1]
        addr = sys.argv[2]
        owner = sys.argv[3]
        process_pdf(pdf_file, addr, owner)
    else:
        print("Usage: python process_pdf.py <pdf_path> <address_dropdown> <owner_name>")
