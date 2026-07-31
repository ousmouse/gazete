import os
import json
import requests
import PyPDF2
import io
import google.generativeai as genai
from datetime import datetime

# 1. API Ayarı
genai.configure(api_key=os.environ["GEMINI_API_KEY"])

def get_pdf_text(pdf_url):
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/91.0.4472.124 Safari/537.36'}
    try:
        response = requests.get(pdf_url, headers=headers, timeout=60)
        if response.status_code == 200:
            pdf_file = io.BytesIO(response.content)
            reader = PyPDF2.PdfReader(pdf_file)
            text = "".join([page.extract_text() for page in reader.pages if page.extract_text()])
            print(f"PDF okundu, karakter sayısı: {len(text)}")
            return text
        else:
            print(f"Hata: PDF sunucusu {response.status_code} döndürdü.")
    except Exception as e:
        print(f"PDF hatası: {e}")
    return None

def main():
    url = f"https://www.resmigazete.gov.tr/eskiler/{datetime.now().strftime('%Y/%m/%d')}/{datetime.now().strftime('%Y%m%d')}.pdf"
    print(f"Hedef URL: {url}")
    
    text = get_pdf_text(url)
    
    if text:
        model = genai.GenerativeModel('gemini-1.5-flash')
        prompt = "Resmi gazete metnini incele ve en önemli 3 kararı JSON listesi olarak ver. SADECE JSON. Keys: title, category, summary, impact, emoji, color."
        response = model.generate_content(prompt + text[:4000])
        
        # Temizleme işlemini tek satıra aldık
        json_str = response.text.replace("
```json", "").replace("```", "").strip()
        
        output_content = f"const mockData = {json_str};"
        with open("data.js", "w", encoding="utf-8") as f:
            f.write(output_content)
        
        print("data.js başarıyla yazıldı.")
    else:
        print("Bot başarısız: PDF içeriği alınamadı.")

if __name__ == "__main__":
    main()
