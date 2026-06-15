import customtkinter as ctk
import sqlite3
from datetime import datetime
import matplotlib.pyplot as plt
import pandas as pd  # Excel işlemleri için ekledik

# --- 1. Veritabanı Kurulumu ---
def veritabani_kur():
    baglanti = sqlite3.connect("finans.db")
    islem = baglanti.cursor()
    islem.execute("""
        CREATE TABLE IF NOT EXISTS hesap_hareketleri (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            islem_turu TEXT,
            kategori TEXT,
            tutar REAL,
            tarih TEXT
        )
    """)
    baglanti.commit()
    baglanti.close()

# --- 2. Arayüz (GUI) Kurulumu ---
def ana_ekrani_baslat():
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")

    pencere = ctk.CTk()
    pencere.title("Kişisel Finans Asistanı PRO")
    pencere.geometry("850x600") # Ekranı yanlamasına genişlettik

    # --- ANA ÇERÇEVELER (Ekranı İkiye Bölüyoruz) ---
    sol_cerceve = ctk.CTkFrame(pencere, width=400)
    sol_cerceve.pack(side="left", fill="y", padx=10, pady=20)

    sag_cerceve = ctk.CTkFrame(pencere, width=400)
    sag_cerceve.pack(side="right", fill="both", expand=True, padx=10, pady=20)

    # ================= SOL PANO (GİRİŞ VE GRAFİKLER) =================
    baslik = ctk.CTkLabel(sol_cerceve, text="Yeni İşlem Ekle", font=("Arial", 20, "bold"))
    baslik.pack(pady=15)

    tur_secimi = ctk.CTkComboBox(sol_cerceve, values=["Gelir", "Gider"])
    tur_secimi.pack(pady=10)

    kategori_giris = ctk.CTkEntry(sol_cerceve, placeholder_text="Kategori (Maaş, Market vb.)", width=200)
    kategori_giris.pack(pady=10)

    tutar_giris = ctk.CTkEntry(sol_cerceve, placeholder_text="Tutar (Örn: 150)", width=200)
    tutar_giris.pack(pady=10)

    def kaydet_tiklandi():
        tur = tur_secimi.get()
        kategori = kategori_giris.get()
        tutar = tutar_giris.get()
        tarih = datetime.now().strftime("%Y-%m-%d %H:%M")

        if kategori == "" or tutar == "":
            return

        try:
            tutar_sayi = float(tutar)
            baglanti = sqlite3.connect("finans.db")
            islem = baglanti.cursor()
            islem.execute("INSERT INTO hesap_hareketleri (islem_turu, kategori, tutar, tarih) VALUES (?, ?, ?, ?)", 
                          (tur, kategori, tutar_sayi, tarih))
            baglanti.commit()
            baglanti.close()
            
            kategori_giris.delete(0, ctk.END)
            tutar_giris.delete(0, ctk.END)
            
            # Kayıt başarılı olunca sağdaki panoyu anında güncelle!
            gecmisi_guncelle() 
        except ValueError:
            pass

    kaydet_butonu = ctk.CTkButton(sol_cerceve, text="İşlemi Kaydet", command=kaydet_tiklandi)
    kaydet_butonu.pack(pady=15)

    ayirici = ctk.CTkLabel(sol_cerceve, text="--- Raporlar ve Grafikler ---", text_color="gray")
    ayirici.pack(pady=10)

    # Pasta Grafik
    def gider_grafik_goster():
        baglanti = sqlite3.connect("finans.db")
        islem = baglanti.cursor()
        islem.execute("SELECT kategori, SUM(tutar) FROM hesap_hareketleri WHERE islem_turu='Gider' GROUP BY kategori")
        veriler = islem.fetchall()
        baglanti.close()
        if veriler:
            kategoriler = [satir[0] for satir in veriler]
            tutarlar = [satir[1] for satir in veriler]
            plt.figure(figsize=(6, 6))
            plt.pie(tutarlar, labels=kategoriler, autopct='%1.1f%%', startangle=140)
            plt.title("Gider Dağılım Grafiği")
            plt.show()

    gider_butonu = ctk.CTkButton(sol_cerceve, text="Gider Dağılımı (Pasta)", command=gider_grafik_goster, fg_color="green", hover_color="darkgreen")
    gider_butonu.pack(pady=5)

    # Çubuk Grafik
    def gelir_gider_grafik_goster():
        baglanti = sqlite3.connect("finans.db")
        islem = baglanti.cursor()
        islem.execute("SELECT islem_turu, SUM(tutar) FROM hesap_hareketleri GROUP BY islem_turu")
        veriler = islem.fetchall()
        baglanti.close()
        if veriler:
            turler = [satir[0] for satir in veriler]
            tutarlar = [satir[1] for satir in veriler]
            plt.figure(figsize=(6, 5))
            renkler = ['green' if tur == 'Gelir' else 'red' for tur in turler]
            plt.bar(turler, tutarlar, color=renkler)
            plt.title("Toplam Gelir ve Toplam Gider")
            for i, tutar in enumerate(tutarlar):
                plt.text(i, tutar, f"{tutar} TL", ha='center', va='bottom', fontweight='bold')
            plt.show()

    gelir_gider_butonu = ctk.CTkButton(sol_cerceve, text="Gelir/Gider (Çubuk)", command=gelir_gider_grafik_goster, fg_color="purple", hover_color="indigo")
    gelir_gider_butonu.pack(pady=5)


    # ================= SAĞ PANO (GEÇMİŞ VE EXCEL) =================
    gecmis_baslik = ctk.CTkLabel(sag_cerceve, text="Canlı İşlem Geçmişi", font=("Arial", 20, "bold"))
    gecmis_baslik.pack(pady=15)

    # Geçmişin listeleneceği dijital kutu
    gecmis_kutusu = ctk.CTkTextbox(sag_cerceve, width=350, height=350, font=("Consolas", 14))
    gecmis_kutusu.pack(pady=5, fill="both", expand=True)

    def gecmisi_guncelle():
        gecmis_kutusu.configure(state="normal") # Yazmaya izin ver
        gecmis_kutusu.delete("1.0", ctk.END)    # Ekranı temizle
        
        baglanti = sqlite3.connect("finans.db")
        islem = baglanti.cursor()
        islem.execute("SELECT islem_turu, kategori, tutar, tarih FROM hesap_hareketleri ORDER BY id DESC")
        veriler = islem.fetchall()
        baglanti.close()

        for veri in veriler:
            tur, kategori, tutar, tarih = veri
            ikon = "🟢" if tur == "Gelir" else "🔴"
            satir = f"{ikon} [{tarih[:10]}] {kategori}: {tutar} TL\n"
            gecmis_kutusu.insert(ctk.END, satir)
        
        gecmis_kutusu.configure(state="disabled") # Kullanıcının elle silmesini engelle

    # Program açıldığında tabloyu otomatik doldur
    gecmisi_guncelle()

    def excele_aktar():
        baglanti = sqlite3.connect("finans.db")
        # Pandas ile veritabanındaki her şeyi tek satırda okuyup tablo yapıyoruz
        tablo = pd.read_sql_query("SELECT * FROM hesap_hareketleri", baglanti)
        baglanti.close()
        
        # O anki tarih ve saatle benzersiz bir Excel dosyası oluştur
        dosya_adi = f"Finans_Raporu_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
        tablo.to_excel(dosya_adi, index=False)
        
        # Ekrana başarı mesajı bas
        gecmis_kutusu.configure(state="normal")
        gecmis_kutusu.insert("1.0", f"✅ BAŞARILI: Veriler '{dosya_adi}' olarak kaydedildi!\n\n")
        gecmis_kutusu.configure(state="disabled")

    # Excel yeşili renginde aktarım butonu
    excel_butonu = ctk.CTkButton(sag_cerceve, text="Tüm Verileri Excel'e Aktar", command=excele_aktar, fg_color="#107C41", hover_color="#0B5A2F")
    excel_butonu.pack(pady=15)

    pencere.mainloop()

if __name__ == "__main__":
    veritabani_kur()
    ana_ekrani_baslat()