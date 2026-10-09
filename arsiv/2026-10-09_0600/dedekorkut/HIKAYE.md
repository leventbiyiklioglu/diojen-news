# Dede Korkut Günlüğü – Seri planı

## Seri: Deli Dumrul (5 bölüm)

1. **Köprü ve haraç** — [yayında, 04.10.2026] Dumrul kuru çayın üstüne köprü yaptırır, geçenlerden haraç alır, kuru yataktan geçenleri tehdit eder; böbürlenir, obadan yas sesleri gelir.
2. **Azrail'le karşılaşma ve Dumrul'un meydan okuması** — Yas tutulan obada ölen genci gören Dumrul, canı alanı ("Azrail") bulup onunla savaşmak ister; meydan okur.
3. **Dumrul'un canına kıyılması tehdidi / can pazarlığı** — Azrail Dumrul'un canına kıymak üzere gelir; Dumrul can pazarlığına girişir, korkuyla yalvarmaya başlar.
4. **Allah'a yalvarış ve ana-babadan can istemesi** — Dumrul Allah'a yalvarır; ona "canına karşılık can bul" denir. Dumrul anasına ve babasına gider, ama onlar canlarını vermek istemez.
5. **Dumrul'un karısının canını verme önerisi ve mutlu son / ödül** — Karısı canını vermeyi önerir; Dumrul bunu kabul etmez, ikisi de ölümü göze alınca Allah'ın merhametiyle can bağışlanır, mutlu son ve ödül.

## Biçim kuralları
- Her bölüm tam 6 panel (resim + altyazı). Son bölümün (her bölümün) son panelinde altyazı sonunda `(Devamı yarın)` yazılır; serinin son bölümünde bu not yazılmaz.
- Panellerde ve altyazıda sıra numarası (1., 2. …) KULLANILMAZ.
- Resim stili: sepya, eski gazete gravürü; 16:9; genişlik 1000 px.

## Yeni bölüm ekleme tarifi
1. Görselleri `gorseller/dedekorkut/` altına koy. Ad biçimi: `<hikaye-slug>-<bolum>-<panel>.jpg` (ör. `deli-dumrul-2-1.jpg` … `-2-6.jpg`). Genişlik 1000 px'e indirilir (JPEG, kalite ~85).
2. `dedekorkut/bolumler.json` dosyasına yeni bir kayıt ekle:
   ```json
   {"hikaye": "Deli Dumrul", "bolum": 2, "baslik": "…", "tarih": "05.10.2026",
    "paneller": [{"resim": "gorseller/dedekorkut/deli-dumrul-2-1.jpg", "altyazi": "…"}, … 6 adet]}
   ```
   Sayfada en yeni bölüm (tarih, sonra bölüm no) üstte görünür.
3. Yayın akışı: `python3 yayin.py` (build.py → `dedekorkut.html` üretir, yeni sayı + `arsiv/<tarih_saat>/` kopyası + arşiv dizini) → `git add` (makaleler/ hariç) → commit → `git push` → PC'ye zip ile kopyala (DiojenNews.html, styles.css, kose.html, dedekorkut.html, kose/, gorseller/) ve `Expand-Archive` ile aç.
