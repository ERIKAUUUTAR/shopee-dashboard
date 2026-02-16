import json
import time
import os
import shutil
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# ==================== KONFIGURASI ====================
# Ganti USERNAME_WINDOWS dengan nama user laptop Anda
# Contoh: C:\\Users\\Administrator\\AppData\\Local\\Google\\Chrome\\User Data
user_data_dir = r"C:\Users\NAMA_USER_ANDA\AppData\Local\Google\Chrome\User Datai" 
# =====================================================

def setup_driver():
    options = Options()
    # PENTING: Menggunakan Profile Default (yang sudah Login Shopee)
    options.add_argument(f"user-data-dir={user_data_dir}")
    options.add_argument("profile-directory=Default") 
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-infobars")
    # Headless dimatikan agar session login terbaca & aman dari deteksi bot
    driver = webdriver.Chrome(options=options)
    return driver

def get_max_discount(driver):
    """Mengecek Voucher Wallet untuk melihat potensi diskon terbesar"""
    print("🎫 Mengecek Dompet Voucher Anda...")
    driver.get("https://shopee.co.id/user/voucher-wallet")
    time.sleep(5)
    
    max_discount = 0
    try:
        # Mencari teks angka di dalam kartu voucher (Sangat bergantung struktur HTML Shopee)
        # Kita pakai logika aman: Cari angka 'RB' atau '%' di elemen voucher
        vouchers = driver.find_elements(By.CSS_SELECTOR, ".voucher-card-content")
        
        print(f"   Ditemukan {len(vouchers)} voucher aktif.")
        
        # LOGIKA SIMPEL: Jika ada voucher, anggap kita punya diskon minimal 10rb
        # (Karena parsing teks voucher shopee sangat rumit & sering berubah)
        if len(vouchers) > 0:
            max_discount = 10000 # Asumsi aman diskon 10rb
            # Jika ingin lebih agresif, ubah jadi 20000
            
    except Exception as e:
        print("   Gagal baca detail voucher, menggunakan default.")
    
    print(f"   ✅ Potensi Potongan: Rp {max_discount}")
    return max_discount

def scrape_shopee():
    # TUTUP CHROME SEBELUM MULAI
    os.system("taskkill /im chrome.exe /f")
    time.sleep(2)

    driver = setup_driver()
    results = []

    try:
        # 1. Cek Diskon dari Akun
        discount_value = get_max_discount(driver)

        # 2. Cari Barang
        keywords = ["aksesoris hp", "peralatan dapur", "stationery lucu"]
        print("🔍 Memulai Pencarian Barang...")

        for keyword in keywords:
            url = f"https://shopee.co.id/search?keyword={keyword}&order=asc&sortBy=price"
            driver.get(url)
            time.sleep(4)
            driver.execute_script("window.scrollTo(0, 1000);")
            time.sleep(2)

            items = driver.find_elements(By.CSS_SELECTOR, ".shopee-search-item-result__item")
            
            for item in items[:8]: # Ambil 8 barang termurah per keyword
                try:
                    text = item.text
                    
                    # Parsing Harga
                    price = 0
                    lines = text.split('\n')
                    for line in lines:
                        if "Rp" in line and not "Min" in line: # Hindari 'Min. Belanja'
                            clean = line.replace("Rp", "").replace(".", "").strip()
                            if clean.isdigit():
                                price = int(clean)
                                break
                    
                    # Parsing Terjual
                    sold = 0
                    for line in lines:
                        if "Terjual" in line:
                            if "RB" in line:
                                val = line.replace("RB", "").replace("+", "").replace(",", ".").replace("Terjual", "").strip()
                                sold = float(val) * 1000
                            else:
                                val = line.replace("Terjual", "").strip()
                                sold = int(val)

                    # LOGIKA UTAMA: APAKAH JADI Rp 0?
                    final_price = price - discount_value
                    if final_price < 0: final_price = 0
                    
                    is_candidate = False
                    note = ""

                    # Kriteria 1: Diskon Voucher bikin jadi Rp 0
                    if price <= discount_value and price > 0:
                        is_candidate = True
                        note = "GRATIS (Pakai Voucher)"

                    # Kriteria 2: Memang Rp 1 - 1000 (Flash Sale)
                    elif price <= 1000:
                        is_candidate = True
                        note = "FLASH SALE MURAH"

                    # Filter Terjual & Rating (Asumsi rating bagus jika terjual banyak)
                    if is_candidate and sold >= 1000:
                        img = item.find_element(By.TAG_NAME, "img").get_attribute("src")
                        link = item.find_element(By.TAG_NAME, "a").get_attribute("href")
                        title = item.find_element(By.TAG_NAME, "img").get_attribute("alt")

                        results.append({
                            "title": title,
                            "price_original": price,
                            "price_final": final_price,
                            "sold": sold,
                            "note": note,
                            "image": img,
                            "link": link,
                            "timestamp": time.strftime("%H:%M")
                        })
                        print(f"   [DAPAT] {title} -> {note}")

                except Exception:
                    continue
        
        driver.quit()

        # 3. Simpan & Upload ke GitHub
        with open("data.json", "w") as f:
            json.dump(results, f)
        
        print("☁️ Mengupload data ke GitHub Dashboard...")
        os.system("git add data.json")
        os.system('git commit -m "Update Otomatis Shopee"')
        os.system("git push")
        print("✅ Selesai! Cek website Anda.")

    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    scrape_shopee()
