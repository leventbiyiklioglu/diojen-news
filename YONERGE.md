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
- PC: machineId 881e391c-228c-48a2-940d-aa481d1f197f, hedef C:\Users\leven\DiojenNews\ (DiojenNews.html, styles.css).
