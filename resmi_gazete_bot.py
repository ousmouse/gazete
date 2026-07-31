import requests
from bs4 import BeautifulSoup
import datetime
import json
import os
import io
import PyPDF2
# YENİ SDK KULLANIMI: Uyarıyı gidermek için güncellendi
from google import genai
from google.genai import types

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY") 
if not GEMINI_API_KEY:
    print("HATA: GEMINI_API_KEY bulunamadı!")
    exit(1)

# Yeni SDK başlatımı
client = genai.Client(api_key=GEMINI_API_KEY)

def get_today_date_strings():
    # GitHub sunucuları genelde UTC saatindedir. Türkiye saati (UTC+3) için ayarlama:
    # (Eğer bot gece 01:00 UTC'de (TR 04:00) çalışıyorsa, tarih zaten doğrudur, ama garantiye alalım)
    today = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=3)))
    year = today.strftime("%Y")
    month = today.strftime("%m")
    day_str = today.strftime("%Y%m%d")
    
    base_url = "https://www.resmigazete.gov.tr/eskiler/"
    today_pdf_url = f"{base_url}{year}/{month}/{day_str}.pdf"
    
    return today_pdf_url, day_str, today.strftime("%d %B %Y")

def extract_text_from_pdf(url):
    print(f"[{datetime.datetime.now()}] PDF İndiriliyor: {url}")
    
    # EKLENDİ: Devlet sitelerinin botları engellemesini aşmak için sahte tarayıcı başlıkları
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Language': 'tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7',
        'Connection': 'keep-alive',
    }
    
    try:
        # Timeout süresi 30'dan 60'a çıkarıldı
        response = requests.get(url, headers=headers, timeout=60)
        response.raise_for_status() 
        
        print("PDF başarıyla indirildi. Metin çıkarılıyor...")
        pdf_file = io.BytesIO(response.content)
        reader = PyPDF2.PdfReader(pdf_file)
        
        full_text = ""
        max_pages = min(15, len(reader.pages)) # İlk 15 sayfayı oku
        for i in range(max_pages):
            page = reader.pages[i]
            if page.extract_text():
                full_text += page.extract_text() + "\n"
            
        return full_text
    except requests.exceptions.RequestException as e:
        print(f"Hata: PDF indirilemedi. Sunucu bağlantıyı reddetti veya dosya yok. Hata detayı: {e}")
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
        # Yeni SDK'ya göre API çağrısı
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
        )
        response_text = response.text
        
        # JSON'ı temizle
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
            print("Özetleme yapılamadı. Gemini boş yanıt döndü.")
    else:
         print("Sistem sonlandırıldı. Veri çekilemedi.")

if __name__ == "__main__":
    main()
