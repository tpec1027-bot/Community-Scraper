import fitz  # PyMuPDF
import pandas as pd
import sys
import os
import re

# 如果系統環境沒有將 tesseract 加入 PATH，可能需要指定安裝路徑
# pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def process_pdf(pdf_path, address_dropdown, owner_name, community_name="output"):
    """
    處理單一 PDF，截取第二頁特定區塊進行 OCR。
    預計：擷取『建物所有權部』的地址欄位。
    """
    try:
        # 開啟 PDF
        doc = fitz.open(pdf_path)
        # 取得所有頁面的文字
        all_text = []
        for page in doc:
            all_text.append(page.get_text("text"))
        text = "".join(all_text)
        
        # 清除所有空白與換行以方便正則比對
        clean_text = re.sub(r'\s+', '', text)
        
        # 尋找 "地址" 和 "權利範圍" 之間的字串
        # 如果 PDF 隱藏了地址，權利範圍就會緊連著地址
        match = re.search(r'地址(.*?)權利範圍', clean_text)
        if match:
            extracted_address = match.group(1)
            # 有些文件隱私保護會整塊留空
            if extracted_address == "":
                extracted_address = "[地址未公開]"
        else:
            # 嘗試其它可能出現的格式，或是直接標記無提取
            match_alt = re.search(r'門牌(.*?)建物坐落', clean_text)
            if match_alt:
                 extracted_address = f"[門牌]{match_alt.group(1)}"
            else:
                 extracted_address = "[無法自動提取地址]"
        
        # 寫入 CSV (不寫入 Header，因為由 download_and_ocr統一初始化過)
        csv_file = f"{community_name}.csv"
        
        new_row = pd.DataFrame([{
            "下拉選單地址": address_dropdown,
            "所有權人姓名": owner_name,
            "擷取到的地址文字": extracted_address
        }])
        
        # a=append mode
        new_row.to_csv(csv_file, mode='a', index=False, header=False, encoding='utf-8-sig')
        print(f"Success: {pdf_path} 處理完成 -> {extracted_address}")
        
    except Exception as e:
        print(f"發生錯誤 {pdf_path}: {e}")

if __name__ == "__main__":
    # 使用範例: python process_pdf.py "C:\path\to\file.pdf" "新北市淡水區XX路" "王大明" "Hi-City"
    if len(sys.argv) >= 4:
        pdf_file = sys.argv[1]
        addr = sys.argv[2]
        owner = sys.argv[3]
        community = sys.argv[4] if len(sys.argv) > 4 else "output"
        process_pdf(pdf_file, addr, owner, community)
    else:
        print("Usage: python process_pdf.py <pdf_path> <address_dropdown> <owner_name> [community_name]")
