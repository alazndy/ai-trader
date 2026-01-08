# 🤖 AI Trader: Algorithmic Trading System (BIST / GLOBAL / CHIPS)

![Python](https://img.shields.io/badge/Python-3.11-blue?style=for-the-badge&logo=python)
![Status](https://img.shields.io/badge/Status-Production%20Ready-green?style=for-the-badge)
![License](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)

**AI Trader**, Borsa İstanbul (BIST), Global Teknoloji Borsaları (NASDAQ) ve Çip Sektörü için geliştirilmiş; **Enflasyon Korumalı**, **Yapay Zeka Destekli** ve **Çoklu Piyasa (Multi-Market)** uyumlu bir algoritmik ticaret botudur.

---

## 🚀 Özellikler

- **Çoklu Piyasa Desteği:**
  - 🇹🇷 **BIST 30:** Enflasyonist ortamda "Alım Gücü" koruma odaklı.
  - 🇺🇸 **GLOBAL:** ABD Teknoloji devlerinde (MAG7) Dolar bazlı büyüme.
  - 💾 **CHIPS:** Çip sektöründeki süper döngüleri (Super-Cycle) yakalar.
- **Kanıtlanmış Stratejiler:**
  - **SmartDCA:** Düşüşleri fırsata çeviren Akıllı Kademeli Alım (10 Yıllık Test Şampiyonu).
  - **BUM_Trend:** Ralli dönemlerinde (Bull Market) agresif trend takibi.
  - **TrendHunter:** Klasik Hareketli Ortalamalar (SMA) ile güvenli liman.
- **Sağlamlık (Robustness):**
  - **Monte Carlo Simülasyonu:** 5 Farklı senaryo ve rastgele portföylerle stres testi yapılmıştır.
  - **Data Glitch Protection:** Hatalı veri ve anlık iğnelere karşı koruma.
  - **Dependency Locking:** `requirements.txt` ile sürüm çakışmaları engellenmiştir.
- **Entegre Sistemler:**
  - **Bildirimler:** `ntfy.sh` üzerinden anlık cep telefonu bildirimleri.
  - **Cloud Ready:** GitHub Actions veya Google Cloud Run üzerinde 7/24 çalışabilir.
  - **AI Training Ready:** Tüm işlemler, gelecekteki Yapay Zeka modellerini eğitmek için etiketli veri olarak saklanır.

---

## 📊 Performans (2015 - 2025 Backtest)

_Reel Getiri: Enflasyon (TÜFE/CPI) düşüldükten sonra kalan net kâr._

| Piyasa              | En İyi Strateji | 10 Yıllık Reel Getiri |
| :------------------ | :-------------- | :-------------------- |
| **BIST 30** 🇹🇷      | SmartDCA        | **%185**              |
| **GLOBAL (US)** 🇺🇸  | SmartDCA        | **%320**              |
| **CHIPS (Semi)** 💾 | SmartDCA        | **%590** 🏆           |

> **Analiz Raporu:** Detaylı performans analizi için [reports/FINAL_ANALYSIS_REPORT.md](reports/FINAL_ANALYSIS_REPORT.md) dosyasına göz atın.

---

## 🛠️ Kurulum

### Gereksinimler

- Python 3.10+
- Git

### 1. Projeyi Klonlayın

```bash
git clone https://github.com/KULLANICI_ADI/ai-trader.git
cd ai-trader
```

### 2. Sanal Ortam Kurun

```bash
python -m venv venv
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate
```

### 3. Bağımlılıkları Yükleyin

```bash
pip install -r requirements.txt
```

---

## 🎮 Kullanım

### A. Simülasyon / Canlı Takip (Live Loop)

Sistemi seçtiğiniz modda başlatmak için `.bat` dosyalarını kullanabilirsiniz:

- `Run_BIST.bat` -> Borsa İstanbul Modu
- `Run_GLOBAL.bat` -> ABD Teknoloji Modu
- `Run_CHIPS.bat` -> Çip Sektörü Modu

Manuel başlatmak için:

```bash
# Windows (PowerShell)
$env:AI_TRADER_MODE="CHIPS"; python simulation_manager.py
```

### B. Tarihsel Testler (Backtests)

Geçmiş 10 yıllık verilerle stratejileri test etmek için:

```bash
# 10 Yıllık BIST Enflasyon Testi
python run_decade_backtest.py

# Monte Carlo Dayanıklılık Testi
python run_monte_carlo.py

# Çoklu Piyasa Karşılaştırması
python run_multimarket_backtest.py
```

---

## 📂 Proje Yapısı

```
ai-trader/
├── config/             # Ayarlar (settings.py)
├── execution/          # Emir İletim (Broker) Katmanı
├── strategies/         # Al-Sat Algoritmaları (Grid, DCA, Trend...)
├── utils/              # Yardımcı Araçlar (Logger, Security, Notifier)
├── reports/            # Analiz Raporları
├── simulation_manager.py # Ana Çalıştırma Motoru
├── requirements.txt    # Bağımlılıklar
└── README.md           # Bu dosya
```

---

## ⚠️ Yasal Uyarı

Bu yazılım **Yatırım Tavsiyesi Değildir**. Sadece eğitim ve simülasyon amaçlıdır. Gerçek para ile işlem yapmadan önce risklerinizi iyi analiz ediniz.
