import fitz  # PyMuPDF
import pandas as pd
import sys
import os
import re

# Tesseract OCR 路徑
TESSERACT_CMD = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# OCR 形近字校正字典（Tesseract 繁體中文常見誤判）
OCR_FIXES = {
    "耋": "臺", "喜": "臺", "鬆": "縣", "邾": "鄉", "廓": "廟",
    "彗": "巷", "芸": "巷", "茹": "巷",
    "濃": "鄰", "潤": "鄰", "薪": "鄰",
    "頌": "頂", "淼": "淡", "鄴": "鄉",
    "簡二路": "遠路", "芝": "坑", "坎": "坑",
    "模": "樓", "理": "重", "秋": "秀",
}

# Tesseract 常產生的尾部垃圾字元
OCR_TRASH = ["LLˍ", "LL_", "LL", "Lˍ"]

def ocr_image(img_cv):
    """
    使用 Tesseract OCR 辨識圖片中的繁體中文文字。
    圖片會先放大 3 倍 + 銳化以提高辨識準確度。
    """
    import cv2
    import numpy as np
    import pytesseract
    
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD
    
    # === 圖片預處理：放大 3 倍 + 銳化 ===
    h, w = img_cv.shape[:2]
    img_upscaled = cv2.resize(img_cv, (w * 3, h * 3), interpolation=cv2.INTER_CUBIC)
    
    # 銳化核心
    sharpen_kernel = np.array([[-1, -1, -1],
                               [-1,  9, -1],
                               [-1, -1, -1]])
    img_sharp = cv2.filter2D(img_upscaled, -1, sharpen_kernel)
    
    # 轉灰階 + 二值化，進一步提升辨識率
    img_gray = cv2.cvtColor(img_sharp, cv2.COLOR_BGR2GRAY)
    _, img_bin = cv2.threshold(img_gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    
    # === Tesseract OCR 辨識 ===
    text = pytesseract.image_to_string(img_bin, lang='chi_tra', config='--psm 7')
    return text.strip()

def process_pdf(pdf_path, address_dropdown, owner_name, community_name="output"):
    """
    處理單一 PDF：
    1. PyMuPDF 純文字優先：尋找「建物所有權部」頁面，用 Regex 提取「地址」欄位。
    2. Tesseract OCR 備援：若地址為空（被系統轉為內嵌圖片），提取圖片 → 放大3倍+銳化 → OCR。
    """
    try:
        doc = fitz.open(pdf_path)
        
        # === 第一步：定位「建物所有權部」所在頁面 ===
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
        
        # === 第二步：Regex 提取純文字地址 ===
        match = re.search(r'所有權人.*?地址(.*?)權利範圍', clean_text)
        extracted_address = ""
        
        if match:
            extracted_address = match.group(1).strip()
            
        # === 第三步：純文字為空 → Tesseract OCR 備援 ===
        if not extracted_address:
            try:
                import numpy as np
                import cv2
                
                ocr_results = []
                for img_info in target_page.get_images(full=True):
                    xref = img_info[0]
                    pix = fitz.Pixmap(doc, xref)
                    
                    img_bytes = pix.tobytes("png")
                    img_array = np.frombuffer(img_bytes, dtype=np.uint8)
                    img_cv = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
                    
                    if img_cv is not None:
                        result = ocr_image(img_cv)
                        if result:
                            ocr_results.append(result)
                
                ocr_text = "".join(ocr_results)
                ocr_clean = re.sub(r'\s+', '', ocr_text)
                
                if ocr_clean:
                    # 套用形近字校正
                    for wrong, right in OCR_FIXES.items():
                        ocr_clean = ocr_clean.replace(wrong, right)
                    # 清除尾部垃圾字元
                    for trash in OCR_TRASH:
                        ocr_clean = ocr_clean.replace(trash, "")
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
