import fitz  # PyMuPDF
import pandas as pd
import sys
import os
import re
import io

# ============================================================
# 全域 OCR Reader（延遲載入，避免多執行緒重複初始化）
# ============================================================
READER = None

def get_ocr_reader():
    """取得共用的 EasyOCR Reader 實例（僅在首次呼叫時初始化）"""
    global READER
    if READER is None:
        import easyocr
        import logging
        logging.getLogger().setLevel(logging.ERROR)
        READER = easyocr.Reader(['ch_tra'], verbose=False)
    return READER

def process_pdf(pdf_path, address_dropdown, owner_name, community_name="output"):
    """
    處理單一 PDF：
    1. PyMuPDF 純文字優先：尋找「建物所有權部」頁面，用 Regex 提取「地址」欄位。
    2. EasyOCR 備援：若地址為空（被系統轉為內嵌圖片），自動提取該頁圖片進行 OCR。
    """
    try:
        doc = fitz.open(pdf_path)
        
        # === 第一步：定位「建物所有權部」所在頁面（通常是第二頁）===
        target_page = None
        for page in doc:
            page_text = page.get_text("text")
            if "建物所有權部" in page_text:
                target_page = page
                break
        if not target_page:
            target_page = doc[1] if len(doc) > 1 else doc[0]
            
        text = target_page.get_text("text")
        clean_text = re.sub(r'\s+', '', text)
        
        # === 第二步：Regex 嘗試從純文字中提取地址 ===
        # 限定在「所有權人...地址...權利範圍」區塊，避免抓到他項權利部的銀行地址
        match = re.search(r'所有權人.*?地址(.*?)權利範圍', clean_text)
        extracted_address = ""
        
        if match:
            extracted_address = match.group(1).strip()
            
        # === 第三步：如果純文字為空 → 啟動 EasyOCR 辨識內嵌圖片 ===
        if not extracted_address:
            try:
                import numpy as np
                import cv2
                
                reader = get_ocr_reader()
                ocr_results = []
                
                for img_info in target_page.get_images(full=True):
                    xref = img_info[0]
                    pix = fitz.Pixmap(doc, xref)
                    
                    # 轉為 OpenCV 可讀的格式
                    img_bytes = pix.tobytes("png")
                    img_array = np.frombuffer(img_bytes, dtype=np.uint8)
                    img_cv = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
                    
                    if img_cv is not None:
                        res = reader.readtext(img_cv, detail=0)
                        ocr_results.extend(res)
                
                ocr_text = "".join(ocr_results)
                ocr_clean = re.sub(r'\s+', '', ocr_text)
                
                if ocr_clean:
                    # OCR 形近字校正字典
                    OCR_FIXES = {
                        "耋": "臺", "鬆": "縣", "邾": "鄉", "廓": "廟",
                        "彗": "巷", "芸": "巷", "鄰": "鄰",
                        "號三": "號", "號五": "號",
                    }
                    for wrong, right in OCR_FIXES.items():
                        ocr_clean = ocr_clean.replace(wrong, right)
                    extracted_address = ocr_clean
                else:
                    extracted_address = "[OCR 無法辨識]"
                    
            except Exception as e:
                print(f"[{pdf_path}] OCR 備援失敗: {e}")
                extracted_address = "[地址提取失敗]"
        
        doc.close()
        
        # === 第四步：寫入 CSV ===
        csv_file = f"{community_name}.csv"
        new_row = pd.DataFrame([{
            "下拉選單地址": address_dropdown,
            "所有權人姓名": owner_name,
            "擷取到的地址文字": extracted_address
        }])
        new_row.to_csv(csv_file, mode='a', index=False, header=False, encoding='utf-8-sig')
        print(f"Success: {pdf_path} -> {extracted_address}")
        
    except Exception as e:
        print(f"發生錯誤 {pdf_path}: {e}")

if __name__ == "__main__":
    if len(sys.argv) >= 4:
        pdf_file = sys.argv[1]
        addr = sys.argv[2]
        owner = sys.argv[3]
        community = sys.argv[4] if len(sys.argv) > 4 else "output"
        process_pdf(pdf_file, addr, owner, community)
    else:
        print("Usage: python process_pdf.py <pdf_path> <address_dropdown> <owner_name> [community_name]")
