import os
import requests
import json
from datetime import datetime
import google.generativeai as genai

# API Anahtarını al
api_key = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=api_key)

def get_today_data():
    today = datetime.now().strftime("%Y%m%d")
    url = f"https://www.resmigazete.gov.tr/eskiler/{today[:4]}/{today[4:6]}/{today}.pdf"
    
    print(f"--- Resmi Gazete Günlük Özet Botu Başlıyor ---")
    print(f"Denenen URL: {url}")
    
    # Gerçek tarayıcı gibi davranması için headers
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    try:
        response = requests.get(url, headers=headers, timeout=60)
        if response.status_code != 200:
            print(f"Hata: PDF bulunamadı (Status: {response.status_code}).")
            return None
        
        # Basit bir metin simülasyonu (PDF okuma karmaşık olduğu için)
        # Örnek veri döndürüyoruz, buraya kendi PDF okuma mantığınızı ekleyebilirsiniz
        return [
            {
                "title": "Örnek Resmi Gazete Kararı",
                "category": "Yönetmelik",
                "summary": "Bu otomatik oluşturulmuş bir test özetidir.",
                "impact": "Tüm vatandaşlar",
                "emoji": "📜",
                "color": "blue"
            }
        ]
    except Exception as e:
        print(f"Hata detayı: {e}")
        return None

def update_data_js(data):
    # data.js dosyasını tamamen yenile
    content = f"const mockData = {json.dumps(data, ensure_ascii=False, indent=4)};"
    with open("data.js", "w", encoding="utf-8") as f:
        f.write(content)
    print("data.js dosyası başarıyla güncellendi.")

if __name__ == "__main__":
    data = get_today_data()
    if data:
        update_data_js(data)
    else:
        # Hata olsa bile dosya boş kalmasın diye test verisi yaz
        print("PDF okunamadı, boş veri yazılıyor.")
        update_data_js([])
```

### Neden bu çözüm?
1.  **JSON Yazma Garantisi:** `json.dumps` komutu, Python listesini tam olarak JavaScript'in anlayacağı `[...]` formatına çevirir.
2.  **Dosya Güncelleme:** `open("data.js", "w")` modu, dosya ne durumda olursa olsun onu silip en güncel veriyle yeniden oluşturur.
3.  **Hata Yönetimi:** PDF'i okuyamasa bile `update_data_js([])` ile boş bir liste yazdıracağız, böylece botun çalıştığını kesin olarak göreceğiz.

**Bunu GitHub'a yükleyip tekrar çalıştırın.** Eğer bu sefer `data.js` içinde `const mockData = [...];` ibaresini görürseniz, artık botun PDF okuma kısmını (PDF kütüphanesini) detaylandırabiliriz. Şu an önemli olan **verinin GitHub'a gitmesini sağlamak!**
