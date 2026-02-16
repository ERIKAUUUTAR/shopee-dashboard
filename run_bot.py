import time
import os
import threading
import json
from datetime import datetime
from flask import Flask, jsonify
from flask_cors import CORS
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

# ================= K O N F I G U R A S I =================
app = Flask(__name__)
CORS(app)  # Wajib: Agar file HTML bisa baca data dari Python

# Path Chrome Laptop DELL
user_data_dir = r"C:\Users\DELL\AppData\Local\Google\Chrome\User Data"
profile_directory = "Profile 1" 

# Variabel Global (Penampung Data Sementara)
live_database = {
    "status": "Menunggu...",
    "last_update": "-",
    "items": []
}
# =========================================================

def setup_driver():
    options = Options()
    options.add_argument(f"user-data-dir={user_data_dir}")
    options.add_argument(f"profile-directory={profile_directory}")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-infobars")
    options.add_argument("--start-maximized")
    options.add_experimental_option('excludeSwitches', ['enable-logging'])
    # Headless mode opsional (kalau mau chrome tidak muncul, hilangkan komen di bawah)
    # options.add_argument("--headless=new") 
    
    driver = webdriver.Chrome(options=options)
    return driver

# --- LOGIKA ROBOT (Berjalan di Background) ---
def start_scraping_loop():
    global live_database
    
    while True:
        print("\n🔄 [SYSTEM] Memulai siklus pencarian baru...")
        live_database["status"] = "Sedang Memindai Shopee..."
        
        # Tutup Chrome biar tidak crash profile
        os.system("taskkill /im chrome.exe /f >nul 2>&1")
        time.sleep(2)

        try:
            driver = setup_driver()
            found_items = []
            
            # Kata kunci pencarian
            keywords = ["aksesoris hp", "barang unik", "flash sale 1000", "peralatan dapur"]
            estimasi_voucher = 10000 

            for keyword in keywords:
                print(f"   🔎 Mencari: {keyword}...")
                
                # URL Filter Termurah
                url = f"https://shopee.co.id/search?keyword={keyword}&order=asc&sortBy=price"
                driver.get(url)
                
                # Scroll
                driver.execute_script("window.scrollTo(0, 1000);")
                time.sleep(3) 
                
                items = driver.find_elements(By.CSS_SELECTOR, ".shopee-search-item-result__item")
                
                # Ambil 5 barang teratas per keyword
                for item in items[:5]: 
                    try:
                        text = item.text
                        price = 0
                        sold = 0
                        
                        # Parsing Harga & Terjual
                        if "Rp" in text:
                            # Ambil angka pertama yg ditemukan
                            parts = text.split('\n')
                            for p in parts:
                                if "Rp" in p and "Min" not in p:
                                    clean = p.replace("Rp", "").replace(".", "").strip()
                                    if clean.isdigit():
                                        price = int(clean)
                                        break
                        
                        if "Terjual" in text:
                            parts = text.split('\n')
                            for p in parts:
                                if "Terjual" in p:
                                    if "RB" in p:
                                        sold = float(p.replace("RB", "").replace("+","").replace("Terjual","").replace(",",".").strip()) * 1000
                                    else:
                                        sold = int(p.replace("Terjual", "").replace("+","").strip())
                                    break

                        # Logika Diskon
                        final_price = price - estimasi_voucher
                        if final_price < 0: final_price = 0
                        
                        note = ""
                        valid = False

                        # Skenario 1: Murah banget (< 2000)
                        if 0 < price <= 2000:
                            valid = True
                            note = "FLASH SALE 🔥"
                            final_price = price 
                        
                        # Skenario 2: Bisa Gratis Ongkir/Voucher
                        elif 2000 < price <= estimasi_voucher:
                            valid = True
                            note = "GRATIS (Voucher) 🎫"
                            final_price = 0

                        if valid and sold >= 50: # Min terjual 50 biar aman
                            try:
                                link = item.find_element(By.TAG_NAME, "a").get_attribute("href")
                                img = item.find_element(By.TAG_NAME, "img").get_attribute("src")
                                title = item.find_element(By.TAG_NAME, "img").get_attribute("alt")
                                
                                found_items.append({
                                    "title": title,
                                    "price_ori": price,
                                    "price_final": final_price,
                                    "sold": sold,
                                    "note": note,
                                    "link": link,
                                    "image": img
                                })
                            except: pass
                            
                    except: continue

            driver.quit()
            
            # Update Database
            live_database["items"] = found_items
            live_database["last_update"] = datetime.now().strftime("%H:%M:%S")
            live_database["status"] = "Menunggu jadwal berikutnya..."
            
            print(f"✅ [SUKSES] Data terupdate! Ditemukan {len(found_items)} barang.")
            
        except Exception as e:
            print(f"❌ [ERROR] {e}")
            live_database["status"] = "Error pada Server"

        # Tunggu 5 menit sebelum scan lagi
        time.sleep(300) 

# --- ENDPOINT API (Jembatan ke HTML) ---
@app.route('/data')
def get_data():
    return jsonify(live_database)

if __name__ == "__main__":
    # Jalankan Robot di Thread terpisah
    t = threading.Thread(target=start_scraping_loop)
    t.daemon = True
    t.start()
    
    print("\n" + "="*50)
    print("🚀 SERVER AKTIF DI: http://localhost:5000")
    print("👉 Buka file 'index.html' sekarang untuk memantau.")
    print("="*50 + "\n")
    
    # Jalankan Server Flask
    app.run(host='0.0.0.0', port=5000)
