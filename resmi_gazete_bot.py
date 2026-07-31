import requests
import datetime
import json
import os
import io
import PyPDF2
import google.generativeai as genai

# API anahtarı ayarı
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)

def get_today_date_strings():
    today = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=3)))
    year = today.strftime("%Y")
    month = today.strftime("%m")
    day_str = today.strftime("%Y%m%d")
    base_url = "https://www.resmigazete.gov.tr/eskiler/"
    today_pdf_url = f"{base_url}{year}/{month}/{day_str}.pdf"
    return today_pdf_url, day_str, today.strftime("%d %B %Y")

def extract_text_from_pdf(url):
    print(f"[{datetime.datetime.now()}] PDF İndiriliyor: {url}")
    # Gerçek bir tarayıcı gibi davranmak için headerlar
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36',
        'Accept-Language': 'tr-TR,tr;q=0.9',
    }
    try:
        response = requests.get(url, headers=headers, timeout=60)
        response.raise_for_status() 
        pdf_file = io.BytesIO(response.content)
        reader = PyPDF2.PdfReader(pdf_file)
        full_text = ""
        max_pages = min(10, len(reader.pages))
        for i in range(max_pages):
            text = reader.pages[i].extract_text()
            if text: full_text += text + "\n"
        return full_text
    except Exception as e:
        print(f"Hata: PDF indirilemedi veya okunamadı: {e}")
        return None

def summarize_with_gemini(text, date_str):
    model = genai.GenerativeModel('gemini-1.5-flash')
    prompt = f"""
    Resmi Gazete'nin {date_str} tarihli metni:
    {text[:20000]}
    
    Önemli kararları bul ve sadece geçerli bir JSON array dön:
    [
      {{"id": "...", "category": "...", "title": "...", "summary": "...", "impact": "...", "color": "blue", "emoji": "⚖️"}}
    ]
    """
    response = model.generate_content(prompt)
    clean_text = response.text.replace("```json", "").replace("```", "").strip()
    return clean_text

def main():
    pdf_url, _, display_date = get_today_date_strings()
    text = extract_text_from_pdf(pdf_url)
    if text:
        json_data = summarize_with_gemini(text, display_date)
        with open("data.js", "w", encoding="utf-8") as f:
            f.write(f"const mockData = {json_data};")
            print("BAŞARILI: data.js güncellendi.")

if __name__ == "__main__":
    main()
