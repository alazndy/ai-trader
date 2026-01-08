# ☁️ Google Cloud & Firestore Kurulum Rehberi

Botun "Hafızası" (Bakiyesi, Geçmiş İşlemleri) Google Firestore veritabanında saklanır.
Bu veritabanını **1 kereye mahsus** aktif etmeniz gerekmektedir.

## 1. Google Cloud Projesi Oluşturma

1.  [Google Cloud Console](https://console.cloud.google.com/) adresine gidin.
2.  Sol üstten proje seçme menüsüne tıklayın ve **"New Project"** deyin.
3.  Proje Adı: `ai-trader-bot` (veya istediğiniz bir isim).
4.  **Create** butonuna basın.

## 2. Firestore Veritabanını Açma (Kritik Adım) ⚠️

1.  Soldaki menüden **"Firestore"** seçeneğini bulun (veya arama çubuğuna yazın).
2.  **"Create Database"** butonuna basın.
3.  **Mode:** `Native Mode` (Varsayılan) seçin.
4.  **Location:** Size en yakın konumu (`europe-west1` veya `us-central1`) seçin.
5.  **Create** diyerek işlemi tamamlayın.

## 3. GitHub Bağlantısı (Cloud Run)

1.  Soldaki menüden **"Cloud Run"** seçeneğine gidin.
2.  **"Create Service"** butonuna tıklayın.
3.  **Deploy one revision from an existing container image** değil, **"Continuously deploy from a repository"** seçeneğini işaretleyin.
4.  **"Set up with Cloud Build"** butonuna tıklayın.
5.  GitHub hesabınızı bağlayın ve `ai-trader` reponuzu seçin.
6.  **Build Type:** `Dockerfile` seçin.
7.  **Save** deyin.
8.  **Authentication:** "Allow unauthenticated invocations" (Böylece Dashboard'a şifresiz girebilirsiniz, veya şifreli isterseniz "Require authentication" seçin).
9.  **Create** butonuna basın.

✅ **Tebrikler!** Yaklaşık 2-3 dakika sonra size bir URL verecek (Örn: `https://ai-trader-bot-xyz.a.run.app`).
Bu linke tıkladığınızda Dashboard açılacak ve Bot arka planda çalışmaya başlayacaktır.
