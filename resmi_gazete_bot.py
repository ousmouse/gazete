import os
import json
import requests
from bs4 import BeautifulSoup
import PyPDF2
import io
import google.generativeai as genai
from datetime import datetime

# API Ayarları
genai.configure(api_key=os.environ["GEMINI_API_KEY"])

def get_pdf_text(pdf_url):
    """PDF URL'sinden metinleri çeker."""
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
    try:
        response = requests.get(pdf_url, headers=headers, timeout=60)
        if response.status_code == 200:
            pdf_file = io.BytesIO(response.content)
            reader = PyPDF2.PdfReader(pdf_file)
            text = ""
            for page in reader.pages:
                text += page.extract_text() or ""
            return text
    except Exception as e:
        print(f"Hata: {e}")
    return None

def summarize_text(text):
    """Gemini ile metni özetler."""
    model = genai.GenerativeModel('gemini-1.5-flash')
    prompt = f"""
    Aşağıdaki Resmi Gazete metnini incele ve en önemli 3 kararı çıkar.
    Her karar için: title, category, summary, impact (kimi etkiliyor), emoji ve color (rose, emerald, violet, amber, blue) belirle.
    Çıktıyı SADECE geçerli bir JSON listesi formatında ver. Örnek:
    [
        {{"title": "...", "category": "...", "summary": "...", "impact": "...", "emoji": "...", "color": "..."}}
    ]
    Metin: {text[:5000]}
    """
    response = model.generate_content(prompt)
    # JSON kısmını temizleyip alalım
    json_str = response.text.replace("```json", "").replace("```", "").strip()
    return json_str

def main():
    today = datetime.now().strftime("%Y/%m/%d")
    date_str = datetime.now().strftime("%Y%m%d")
    url = f"https://www.resmigazete.gov.tr/eskiler/{today}/{date_str}.pdf"
    
    print(f"--- Bot Başlıyor: {url} ---")
    text = get_pdf_text(url)
    
    if text:
        json_data = summarize_text(text)
        
        # data.js dosyasına formatlı yazma
        final_content = f"const mockData = {json_data};"
        with open("data.js", "w", encoding="utf-8") as f:
            f.write(final_content)
        print("Başarılı: data.js güncellendi.")
    else:
        print("PDF içeriği alınamadı.")

if __name__ == "__main__":
    main()
