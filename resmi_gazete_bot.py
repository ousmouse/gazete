import requests
from bs4 import BeautifulSoup
import datetime
import json
import os
import io # EKLENDİ: Hafızadaki PDF'i okumak için gerekli
import PyPDF2 # EKLENDİ: PDF okuyucu
import google.generativeai as genai # EKLENDİ: Gemini yapay zeka aracı

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY") 
if not GEMINI_API_KEY:
    print("HATA: GEMINI_API_KEY bulunamadı!")
    exit(1)

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

def get_today_date_strings():
    today = datetime.datetime.now()
    year = today.strftime("%Y")
    month = today.strftime("%m")
    day_str = today.strftime("%Y%m%d")
    
    base_url = "https://www.resmigazete.gov.tr/eskiler/"
    today_pdf_url = f"{base_url}{year}/{month}/{day_str}.pdf"
    
    return today_pdf_url, day_str, today.strftime("%d %B %Y")

def extract_text_from_pdf(url):
    print(f"[{datetime.datetime.now()}] PDF İndiriliyor: {url}")
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status() 
        
        print("PDF başarıyla indirildi. Metin çıkarılıyor...")
        pdf_file = io.BytesIO(response.content)
        reader = PyPDF2.PdfReader(pdf_file)
        
        full_text = ""
        max_pages = min(10, len(reader.pages))
        for i in range(max_pages):
            page = reader.pages[i]
            full_text += page.extract_text() + "\n"
            
        return full_text
    except requests.exceptions.RequestException as e:
        print(f"Hata: PDF indirilemedi. Belki bugünün gazetesi henüz yayınlanmadı. Hata detayı: {e}")
        return None
    except Exception as e:
        print(f"PDF okunurken hata oluştu: {e}")
        return None

def summarize_with_gemini(text, date_str):
    print("Metin Gemini'ye gönderiliyor. Bu işlem biraz sürebilir...")
    
    prompt = f"""
    Aşağıda Türkiye Cumhuriyeti Resmi Gazetesi'nin {date_str} tarihli sayısının metin dökümü bulunmaktadır. 
    Lütfen bu metni analiz et ve içindeki en önemli kararları (Kanun, Cumhurbaşkanı Kararı, Atama, Yönetmelik vb.) bul.
    
    Bulduğun her bir önemli karar için bana tam olarak şu JSON formatında bir liste dön (başka hiçbir metin ekleme, sadece geçerli bir JSON array dön):
    
    [
      {{
        "id": "Karar Sayısı veya benzersiz bir ID",
        "category": "Kategori (örn: 'Cumhurbaşkanı Kararı', 'Yönetmelik', 'Atama', 'Tebliğ', 'Kanun')",
        "title": "Kararın anlaşılır, kısa ve net başlığı",
        "summary": "Bu karar tam olarak ne anlama geliyor? Sıradan bir vatandaşın anlayacağı şekilde 2-3 cümlelik çok net bir özet. Teknik jargon kullanma.",
        "impact": "Bu karardan en çok kimler etkilenir? (Örn: 'Tüm Öğrenciler', 'İthalatçılar', 'Kamu Personeli')",
        "pdfLink": "Şimdilik buraya '#' koy",
        "color": "Kategoriye uygun bir renk. Şu değerlerden birini seç: 'rose', 'emerald', 'violet', 'amber', 'blue', 'default'",
        "emoji": "Kategoriye uygun bir emoji (örn: ⚖️, 👤, 🏢)"
      }}
    ]
    
    Resmi Gazete Metni (İlk sayfalar):
    {text[:30000]}
    """
    
    try:
        response = model.generate_content(prompt)
        response_text = response.text
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].strip()
            
        print("Gemini'den yanıt alındı!")
        return response_text
    except Exception as e:
        print(f"Gemini API Hatası: {e}")
        return None

def main():
    print("--- Resmi Gazete Günlük Özet Botu Başlıyor ---")
    
    pdf_url, file_name, display_date = get_today_date_strings()
    
    extracted_text = extract_text_from_pdf(pdf_url)
    
    if extracted_text:
        summarized_json_string = summarize_with_gemini(extracted_text, display_date)
        
        if summarized_json_string:
            try:
                parsed_json = json.loads(summarized_json_string)
                output_file = "data.js"
                
                js_content = f"// Otomatik Oluşturuldu: {display_date}\nconst mockData = {json.dumps(parsed_json, indent=4, ensure_ascii=False)};"
                
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(js_content)
                    
                print(f"BAŞARILI: Bugünkü ({display_date}) özetler {output_file} dosyasına kaydedildi.")
                
            except json.JSONDecodeError as e:
                print(f"HATA: Gemini geçerli bir JSON döndürmedi. Yanıt formatı bozuk: {e}")
        else:
            print("Özetleme yapılamadı.")
    else:
         print("Sistem sonlandırıldı. Tekrar denenecek.")

if __name__ == "__main__":
    main()
