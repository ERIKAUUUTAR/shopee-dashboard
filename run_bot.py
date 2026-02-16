import json
import time
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

def scrape_shopee():
    print("🚀 Menyambungkan ke Chrome yang sudah Anda buka...")
    
    options = Options()
    # INI KUNCINYA: Kita menyambung ke port 9222 yang sudah Anda buka manual
    options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
    
    try:
        # Driver akan langsung connect ke Chrome yang terbuka
        driver = webdriver.Chrome(options=options)
        results = []
        
        # --- LOGIKA PENCARIAN ---
        keywords = ["aksesoris hp murah", "flash sale", "barang unik"]
        estimasi_voucher = 10000 

        for keyword in keywords:
            print(f"\n🔍 Mencari: '{keyword}'...")
            url = f"https://shopee.co.id/search?keyword={keyword}&order=asc&sortBy=price"
            driver.get(url)
            time.sleep(3) # Tunggu loading
            
            items = driver.find_elements(By.CSS_SELECTOR, ".shopee-search-item-result__item")
            
            for item in items[:5]: 
                try:
                    text_full = item.text
                    lines = text_full.split('\n')
                    price = 0
                    sold = 0
                    
                    for line in lines:
                        if "Rp" in line and "Min" not in line:
                            clean = line.replace("Rp", "").replace(".", "").strip()
                            if clean.isdigit(): price = int(clean)
                        if "Terjual" in line:
                            val = line.replace("Terjual", "").replace("RB", "000").replace("+","").replace(",", ".").strip()
                            try: sold = float(val) 
                            except: sold = 0

                    # Logika Filter
                    price_final = price - estimasi_voucher
                    if price_final < 0: price_final = 0
                    
                    note = ""
                    if price > 0 and price <= 2000: note = "FLASH SALE 🔥"
                    elif price > 2000 and price <= estimasi_voucher: note = "GRATIS (Voucher) 🎫"
                    
                    if note != "":
                        link = item.find_element(By.TAG_NAME, "a").get_attribute("href")
                        img = item.find_element(By.TAG_NAME, "img").get_attribute("src")
                        title = item.find_element(By.TAG_NAME, "img").get_attribute("alt")
                        
                        print(f"   [+] {title[:15]}... | Rp {price}")
                        results.append({
                            "title": title, "price_original": price, "price_final": price_final,
                            "sold": sold, "link": link, "image": img, "note": note
                        })
                except: continue

        # --- SIMPAN & UPLOAD ---
        if len(results) > 0:
            print("\n💾 Menyimpan data...")
            with open("data.json", "w") as f:
                json.dump(results, f)
            
            print("☁️ Mengupload ke GitHub...")
            os.system("git add data.json")
            os.system('git commit -m "Update via Mode Manual"')
            os.system("git push")
            print("✅ SUKSES!")
        else:
            print("❌ Tidak ada barang cocok.")
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        print("Pastikan Anda sudah menjalankan Langkah 2 (Buka Chrome via CMD)!")

if __name__ == "__main__":
    scrape_shopee()
