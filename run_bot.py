import json
import time
import os
import random
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

def scrape_shopee():
    print("🚀 Mencoba menyambung ke Chrome (Port 9222)...")
    
    options = Options()
    # Menyambung ke jendela Chrome yang sudah terbuka di port 9222
    options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
    
    try:
        driver = webdriver.Chrome(options=options)
        results = []
        
        # Kata kunci pencarian
        keywords = ["aksesoris hp murah", "flash sale 1000", "barang unik", "peralatan dapur"]
        estimasi_voucher = 10000 

        for keyword in keywords:
            print(f"\n🔍 Menelusuri: '{keyword}'...")
            url = f"https://shopee.co.id/search?keyword={keyword}&order=asc&sortBy=price"
            
            try:
                driver.get(url)
                time.sleep(3)
                
                # Scroll otomatis agar produk muncul semua
                for _ in range(2):
                    driver.execute_script(f"window.scrollBy(0, {random.randint(600, 1000)});")
                    time.sleep(2)
                
                items = driver.find_elements(By.CSS_SELECTOR, ".shopee-search-item-result__item")
                
                for item in items[:10]: 
                    try:
                        text_full = item.text
                        lines = text_full.split('\n')
                        
                        price = 0
                        sold = 0
                        
                        # Parsing data harga dan jumlah terjual
                        for line in lines:
                            if "Rp" in line and "Min" not in line:
                                clean = line.replace("Rp", "").replace(".", "").strip()
                                if clean.isdigit(): price = int(clean)
                            
                            if "Terjual" in line:
                                val = line.replace("Terjual", "").replace("RB", "000").replace("+", "").replace(",", ".").strip()
                                try: sold = float(val)
                                except: sold = 0

                        # Logika filter Rp 0 dengan voucher pribadi
                        price_final = price - estimasi_voucher
                        if price_final < 0: price_final = 0
                        
                        note = ""
                        is_match = False

                        if 0 < price <= 2000:
                            is_match = True
                            note = "FLASH SALE 🔥"
                            price_final = price 
                        elif 2000 < price <= estimasi_voucher:
                            is_match = True
                            note = "GRATIS (Voucher) 🎫"
                            price_final = 0

                        # Filter minimal terjual 1000 item
                        if is_match and sold >= 1000:
                            link = item.find_element(By.TAG_NAME, "a").get_attribute("href")
                            img = item.find_element(By.TAG_NAME, "img").get_attribute("src")
                            title = item.find_element(By.TAG_NAME, "img").get_attribute("alt")

                            print(f"   [+] {title[:25]}... | Rp {price}")
                            
                            results.append({
                                "title": title,
                                "price_original": price,
                                "price_final": price_final,
                                "sold": sold,
                                "link": link,
                                "image": img,
                                "note": note
                            })
                    except: continue
            except Exception as e:
                print(f"   Gagal memuat halaman: {e}")
                continue

        # Simpan dan Push ke GitHub secara otomatis
        if results:
            print(f"\n💾 Berhasil memanen {len(results)} barang.")
            with open("data.json", "w") as f:
                json.dump(results, f)
            
            print("☁️ Mengirim data terbaru ke GitHub...")
            os.system("git add data.json")
            os.system('git commit -m "Update barang murah otomatis"')
            os.system("git push")
            print("✅ DASHBOARD TERUPDATE!")
        else:
            print("❌ Tidak ada barang yang memenuhi kriteria kali ini.")

    except Exception as e:
        print(f"❌ KONEKSI GAGAL: {e}")
        print("Pastikan Chrome sudah dibuka via CMD dengan port 9222!")

if __name__ == "__main__":
    scrape_shopee()
