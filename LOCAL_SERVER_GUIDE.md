# 🏠 Ev Sunucusu Kurulum Rehberi (Laptop Modu)

Eski laptopunuzu veya mevcut bilgisayarınızı **"Para Basan Makineye"** dönüştürmek için yapmanız gerekenler:

## 1. Hazırlık (Eski Laptop İçin)

Bilgisayarınızda Python yüklü olduğundan emin olun.

1.  [Python İndir (3.9 veya üstü)](https://www.python.org/downloads/)
2.  Kurarken **"Add Python to PATH"** kutucuğunu MUTLAKA işaretleyin.

## 2. Kodu Yükleme

Mevcut bilgisayardaysanız bu adım tamamdır. Başka bilgisayara geçiyorsanız:

1.  Git kurun.
2.  Masaüstünde bir klasör açıp sağ tık -> "Open Git Bash" deyin.
3.  `git clone https://github.com/alazndy/ai-trader.git` yazın.

## 3. Kurulum (Tek Seferlik)

Komut satırını (CMD) açın ve sırasıyla şunu yazın:

```cmd
cd Desktop\ai-trader
pip install -r requirements.txt
```

## 4. Botları Başlatma 🚀

Masaüstündeki **`Run_Server_Mode.bat`** dosyasına Çift Tıklayın.

Ekrana 5 tane siyah pencere açılacak:

1.  **Dashboard:** Grafikleri gösterir.
2.  **Kripto Botu:** Dakikada bir çalışır.
3.  **BIST Botu:** Saatte bir çalışır.
4.  **Global Botu:** Saatte bir çalışır.
5.  **Cip Botu:** Saatte bir çalışır.

## ⚠️ ÇOK ÖNEMLİ: Kapanmasın!

Bilgisayar uyku moduna girerse botlar durur.

1.  Başlat > Ayarlar > Sistem > Güç ve Uyku
2.  **"Prize takılıyken bilgisayar uyku moduna geçsin"** -> **HİÇBİR ZAMAN**

Artık bilgisayarın kapağını (ayarını yaptıysanız) kapatıp köşeye koyabilirsiniz. 7/24 çalışacaktır.
