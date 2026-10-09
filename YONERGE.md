# Diojen News yonergesi
Dosyalar /workspace/diojen/ altindadir. Gazete, haberler/<kategori>.json dosyalarindan build.py ile uretilir.
Kategori dosyalari: dunya.json, ekonomi.json, spor.json, teknoloji.json, kultur.json
Format:
{"yazar":"Yazar Adi","haberler":[{"baslik":"...","ozet":"2-4 cumle, KENDI CUMLELERINLE","kaynak":"Yayin adi","kaynak_url":"https://...","tarih":"02.10.2026"}]}
Kurallar:
- Haberleri sadece WebSearch/WebFetch ile bulunan GERCEK ve guncel kaynaklardan al. Asla haber, rakam, alinti uydurma.
- Ozeti kendi cumlelerinle yaz, kaynaktan kopyalama. Kaynak ve kaynak_url zorunlu.
- En yeni haber en uste. Dosyada en fazla 6 haber tut, eskileri at.
- Dilin Turkce, gazete uslubu, tarafsiz.
- Yazarlar HTML'e dokunmaz, sadece kendi JSON'unu gunceller. Editor build.py calistirip PC'ye gonderir.
- PC: Levent'in bilgisayarı (kimlik bilgisi Grok Bot'ta), hedef klasör: DiojenNews (DiojenNews.html, styles.css).
- Yayin duzeni: Gazete 6 saatte bir (06:07, 12:07, 18:07, 00:07) yeni sayi cikar. Yazarlar :07'de kendi JSON'unu gunceller, editor :37'de `python3 yayin.py` calistirir (build + arsiv/<tarih_saat>/ kopyasi + arsiv/index.html), sonra git commit/push yapar ve PC'ye gonderir.
- Arsiv: /workspace/diojen/arsiv/ ; GitHub: https://github.com/leventbiyiklioglu/diojen-news
Ekip (ek):
- Gazete | Arsiv Arastirmacisi Kaan: kaynak yalnizca WikiLeaks arsivi; artik gorevde olmayan dunya liderlerinin skandallari. Bolum adi 'Arsiv Dosyasi' (haftalik, Levent onaylarsa pazar 06:00). Taslaklar taslak/arsiv-dosyasi/ altinda; Levent onaylamadan yayin yok.
- Gazete | SEO Uzmani Seda: SEO, temiz URL'ler (.html'siz adresler, canonical, sitemap).
