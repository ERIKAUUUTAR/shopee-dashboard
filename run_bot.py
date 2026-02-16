import json
import time
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

# ==============================================================================
# KONFIGURASI KHUSUS LAPTOP DELL ANDA
# Path ini diambil dari data chrome://version yang Anda kirimo
# ==============================================================================
user_data_dir = r"C:\Users\DELL\AppData\Local\Google\Chrome\User Data"
profile_directory = "Profile 1" 
# ==============================================================================

def setup_driver():
    options = Options()
    # Mengarahkan ke Folder Data Chrome Utama
    options.add_argument(f"user-data-dir={user_data_dir}")
    
    # Mengarahkan ke Profile 1 (Akun Shopee Anda)
    options.add_argument(f"profile-directory={profile_directory}")
    
    # Opsi tambahan biar lancar
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-infobars")
    options.add_argument("--start-maximized") # Biar window terbuka lebar
    
    # Hapus log error yang tidak perlu di CMD
    options.add_experimental_option('excludeSwitches', ['enable-logging'])
    
    driver = webdriver.Chrome(options=options)
    return driver

def scrape_shopee():
    # 1. MATIKAN CHROME DULU (Wajib agar tidak bentrok file)
    print("⚠️  Menutup paksa Chrome yang sedang terbuka...")
    os.system("taskkill /im chrome.exe /f >nul 2>&1")
    time.sleep(2)

    print("🚀 Memulai Bot Shopee Hunter...")
    driver = setup_driver()
    results = []

    try:
        # 2. LOGIKA PENCARIAN BARANG
        # Anda bisa tambah/ganti kata kunci di sini
        keywords = ["aksesoris hp murah", "flash sale 1000", "barang unik", "peralatan dapur"]
        
        # Simulasi Diskon Voucher (Misal akun Anda punya diskon 10rb)
        estimasi_voucher = 10000 

        for keyword in keywords:
            print(f"\n🔍 Sedang mencari: '{keyword}'...")
            
            # URL Filter: Termurah (Ascending)
            url = f"https://shopee.co.id/search?keyword={keyword}&order=asc&sortBy=price"
            driver.get(url)
            
            # Scroll ke bawah biar produk loading
            driver.execute_script("window.scrollTo(0, 1500);")
            time.sleep(4) 
            
            # Ambil elemen produk
            items = driver.find_elements(By.CSS_SELECTOR, ".shopee-search-item-result__item")
            
            # Cek 8 barang teratas per keyword
            for item in items[:8]: 
                try:
                    # Ambil Teks Data (Cara paling aman anti-error selector)
                    text_full = item.text
                    lines = text_full.split('\n')
                    
                    price = 0
                    sold = 0
                    
                    # --- PARSING HARGA & TERJUAL ---
                    for line in lines:
                        # Cari Harga
                        if "Rp" in line and "Min" not in line:
                            clean_price = line.replace("Rp", "").replace(".", "").strip()
                            if clean_price.isdigit():
                                price = int(clean_price)
                        
                        # Cari Terjual
                        if "Terjual" in line:
                            if "RB" in line: # Misal: 10RB+ Terjual
                                clean_sold = line.replace("RB", "").replace("+", "").replace(",", ".").replace("Terjual", "").strip()
                                sold = float(clean_sold) * 1000
                            else: # Misal: 500 Terjual
                                clean_sold = line.replace("Terjual", "").replace("+", "").strip()
                                sold = int(clean_sold)

                    # --- LOGIKA FILTER (OTAK BOT) ---
                    price_final = price - estimasi_voucher
                    if price_final < 0: price_final = 0
                    
                    note = ""
                    is_match = False

                    # Skenario 1: Memang Flash Sale Murah (< Rp 2000)
                    if price > 0 and price <= 2000:
                        is_match = True
                        note = "FLASH SALE 🔥"
                        price_final = price # Tidak dipotong voucher kalau sudah murah banget

                    # Skenario 2: Gratis kalau pakai Voucher
                    elif price > 2000 and price <= estimasi_voucher:
                        is_match = True
                        note = "GRATIS (Voucher) 🎫"
                        price_final = 0

                    # SYARAT TAMBAHAN: Minimal Terjual 1000 item (Biar tidak scam)
                    if is_match and sold >= 1000:
                        # Ambil Link & Gambar
                        link = item.find_element(By.TAG_NAME, "a").get_attribute("href")
                        img = item.find_element(By.TAG_NAME, "img").get_attribute("src")
                        title = item.find_element(By.TAG_NAME, "img").get_attribute("alt")

                        print(f"   [✅ DAPAT] {title[:30]}... | Rp {price} -> {note}")
                        
                        results.append({
                            "title": title,
                            "price_original": price,
                            "price_final": price_final,
                            "sold": sold,
                            "link": link,
                            "image": img,
                            "note": note
                        })

                except Exception:
                    continue # Skip item jika error, lanjut ke item berikutnya

        driver.quit()

        # 3. SIMPAN DATA KE FILE
        with open("data.json", "w") as f:
            json.dump(results, f)
        
        print("\n" + "="*50)
        print(f"✅ SELESAI! {len(results)} barang ditemukan.")
        print("📁 File 'data.json' berhasil dibuat di folder ini.")
        print("👉 SEKARANG: Upload file 'data.json' ini ke GitHub Anda!")
        print("="*50)

    except Exception as e:
        print(f"❌ TERJADI ERROR: {e}")
        print("Tips: Pastikan Chrome sudah tertutup sebelum menjalankan bot.")

if __name__ == "__main__":
    scrape_shopee()
