import os
import json
import requests
import PyPDF2
import io
import google.generativeai as genai
from datetime import datetime

genai.configure(api_key=os.environ["GEMINI_API_KEY"])

def main():
    today = datetime.now().strftime("%Y/%m/%d")
    date_str = datetime.now().strftime("%Y%m%d")
    url = f"https://www.resmigazete.gov.tr/eskiler/{today}/{date_str}.pdf"
    
    headers = {'User-Agent': 'Mozilla/5.0'}
    response = requests.get(url, headers=headers, timeout=60)
    
    if response.status_code == 200:
        pdf_file = io.BytesIO(response.content)
        reader = PyPDF2.PdfReader(pdf_file)
        text = "".join([p.extract_text() for p in reader.pages if p.extract_text()])
        
        model = genai.GenerativeModel('gemini-1.5-flash')
        prompt = "Resmi gazete metnini incele ve en önemli 3 kararı JSON listesi olarak ver. Keys: title, category, summary, impact, emoji, color."
        res = model.generate_content(prompt + text[:4000])
        
        # Temizleme işlemini en basit haliyle yapıyoruz
        clean_json = res.text.replace("
```json", "").replace("```", "").strip()
        
        with open("data.js", "w", encoding="utf-8") as f:
            f.write("const mockData = " + clean_json + ";")
        print("data.js guncellendi.")
    else:
        print(f"PDF bulunamadi: {response.status_code}")

if __name__ == "__main__":
    main()
