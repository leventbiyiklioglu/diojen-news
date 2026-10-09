#!/usr/bin/env python3
"""Diojen News ozel bolumleri (Seda'nin URL duzeni: bolum/ -> bolum/index.html, icerik bolum/<slug> -> bolum/<slug>.html).

  /kultur-sanat/sinema-ogrenci/          Sinema-TV Ogrenci Kosesi (CollectionPage)   <- haberler/ogrenci-kosesi.json
  /kultur-sanat/sinema-ogrenci/<slug>    yazi (NewsArticle)
  /kultur-sanat/sinema-ogrenci/arsiv/    tum yazilar
  /gise-hasilatlari/                     Gise & Yeni Cikanlar (ItemList + Movie)     <- haberler/gise.json (+ yeni-cikanlar.json)
  /gise-hasilatlari/<YYYY-WW>            haftalik gise (ISO hafta)                    <- haberler/gise-arsiv/<YYYY-WW>.json
  /gise-hasilatlari/arsiv/
  /yeni-cikanlar/                        Yeni Cikanlar (ItemList + Movie/TVSeries)   <- haberler/yeni-cikanlar.json
  /yeni-cikanlar/<YYYY-WW>               haftalik                                     <- haberler/yeni-cikanlar-arsiv/<YYYY-WW>.json
  /yeni-cikanlar/arsiv/
  /arsiv-dosyasi/                        Arsiv Dosyasi (CollectionPage)              <- YALNIZ makaleler/*.md, kategori "Arşiv Dosyası"
  /arsiv-dosyasi/<slug>                  dosya (NewsArticle)
  /arsiv-dosyasi/arsiv/
Kurallar:
- taslak/ ve arsiv-dosyasi/ icindeki calisma dosyalari (konular.md, yayinlananlar.md, kaynaklar/) OKUNMAZ, silinmez, degistirilmez.
  arsiv-dosyasi/ altina yalniz index.html, arsiv/index.html ve <slug>.html yazilir; ayrilmis adlar cakismaz (AYRILMIS).
- Tarihi bugunden sonra olan ogrenci kosesi ve Arsiv Dosyasi yazilari atlanir (tarihi gelince gorunur).
  Yalniz ekran goruntusu icin: DIOJEN_ONIZLEME_ILERI=1 ortam degiskeni ileri tarihlileri "ONIZLEME" bandiyla gosterir (commit edilmez).
- build.py: ozel_sayfalar.uret(base, makaleler, globals())  -> seo_head, jsonld_*, sitemap_ekle, mutlak, kisa_metin ... build.py'den gelir.
- yayin.py: ana_arsiv_index_ekle(base) ve arsiv_kopyasi_linkleri(hedef).
"""
import os, json, html, datetime, re, glob
e = html.escape
H = {}  # build.py yardimcilari

# ---------------- guvenli yardimcilar ----------------
def _s(x): return "" if x is None else str(x)
def es(x): return html.escape(_s(x))
def al(d, k, vars=""):
    v = d.get(k) if isinstance(d, dict) else None
    return vars if v is None else v
URL_RE = re.compile(r"https?://(?:(?!&quot;|&#x27;|&lt;|&gt;)[^\s<>\"'])+")
def linkle(metin):
    """Once escape, sonra http(s) adreslerini guvenli <a> yap."""
    def f(m):
        u = m.group(0); son = ""
        while u and u[-1] in ".,;:!?)]»”’": son = u[-1] + son; u = u[:-1]
        return f'<a href="{u}" target="_blank" rel="noopener">{u}</a>{son}'
    return URL_RE.sub(f, es(metin))
def slugify(x, n=70):
    x = re.sub(r"\s*\(.*?\)\s*", " ", _s(x)).strip()
    x = x.translate(str.maketrans("çğıöşüÇĞİÖŞÜâîûÂÎÛ", "cgiosuCGIOSUaiuAIU")).lower()
    x = re.sub(r"[^a-z0-9]+", "-", x).strip("-")
    return x[:n].rsplit("-", 1)[0] if len(x) > n else x
def _tarih(t):
    m = re.search(r"(\d{2})\.(\d{2})\.(\d{4})", _s(t))
    try: return datetime.date(int(m.group(3)), int(m.group(2)), int(m.group(1))) if m else None
    except ValueError: return None
def _iso(t): d = _tarih(t); return d.isoformat() if d else ""
ILERI = os.environ.get("DIOJEN_ONIZLEME_ILERI") == "1"
def yayinda(tarih_gg_aa_yyyy=None, iso=None):
    """Ileri tarihli icerik yayina cikmaz. Tarihsiz icerik yayinda sayilir."""
    d = _tarih(tarih_gg_aa_yyyy) if tarih_gg_aa_yyyy is not None else (datetime.date.fromisoformat(iso) if iso and iso != "0000-00-00" else None)
    return ILERI or d is None or d <= datetime.date.today()
def ileri_mi(t=None, iso=None):
    d = _tarih(t) if t is not None else (datetime.date.fromisoformat(iso) if iso and iso != "0000-00-00" else None)
    return bool(d and d > datetime.date.today())

# ---------------- adresler ----------------
OK_DIR, GISE_DIR, YC_DIR, AD_DIR = "kultur-sanat/sinema-ogrenci", "gise-hasilatlari", "yeni-cikanlar", "arsiv-dosyasi"
AYRILMIS = {"index", "arsiv", "konular", "yayinlananlar", "kaynaklar"}  # arsiv-dosyasi/ icindeki Kaan dosyalari + kendi adlarimiz
ETIKET = {"ogrenci": ("e-ogrenci", "ÖĞRENCİ KÖŞESİ"), "gise": ("e-gise", "GİŞE"), "yeni": ("e-yeni", "YENİ ÇIKANLAR"),
          "ad": ("e-arsivdosyasi", "ARŞİV DOSYASI"), "ozel": ("e-ozel", "ÖZEL HABER")}
def etiket(sinif, metin): return f'<span class="etiket {sinif}">{es(metin)}</span>'
def hafta_etiketi(kod):
    """'2026-40' -> '2026 · 40. hafta (28.09–04.10.2026)'"""
    try:
        y, w = (int(x) for x in _s(kod).split("-"))
        a = datetime.date.fromisocalendar(y, w, 1); b = a + datetime.timedelta(days=6)
        return f"{y} · {w}. hafta ({a:%d.%m}–{b:%d.%m.%Y})"
    except Exception: return _s(kod)
def iso_hafta(d=None):
    d = d or datetime.date.today(); y, w, _ = d.isocalendar(); return f"{y}-{w:02d}"

# ---------------- menu ----------------
MOBIL_DUGME = '<input type="checkbox" id="menu-ac" class="menu-ac" aria-label="Menüyü aç"><label for="menu-ac" class="menu-dugme">☰ Menü</label>'
def kultur_menu(kok="", kultur_href="/#kultur"):
    return (f'<details class="nav-acilir"><summary>Kültür &amp; Sanat</summary><div class="alt-menu">'
            f'<a href="{kultur_href}">Kültür &amp; Sanat haberleri</a>'
            f'<a href="{kok}{OK_DIR}/">Sinema-TV Öğrenci Köşesi</a>'
            f'<a href="{kok}{GISE_DIR}/">Gişe &amp; Yeni Çıkanlar</a></div></details>')
def arsiv_dosyasi_link(kok=""): return f'<a href="{kok}{AD_DIR}/" class="nav-ad">Arşiv Dosyası</a>'
def nav_linkleri(kok=""): return kultur_menu(kok) + arsiv_dosyasi_link(kok)
def yan_alt(kok=""):
    return (f'<ul class="yan-alt"><li><a href="{kok}{OK_DIR}/">↳ Sinema-TV Öğrenci Köşesi</a></li>'
            f'<li><a href="{kok}{GISE_DIR}/">↳ Gişe &amp; Yeni Çıkanlar</a></li></ul>')

def yukle(base, ad):
    try: return json.load(open(os.path.join(base, "haberler", ad), encoding="utf-8"))
    except Exception: return {}

# ---------------- sayfa iskeleti ----------------
def _baslik_kisalt(b):
    """<title> en fazla 60 karakter: sonek sigarsa ' - Diojen News' eklenir, sigmazsa kisaltilir (tam_baslik)."""
    b = _s(b)
    if len(b) + len(" - Diojen News") <= 60: return b, False
    return (b if len(b) <= 60 else H["kisa_metin"](b, 58)), True
def yaz_sayfa(base, rel_html, yol, baslik, aciklama, govde, jsonld=None, og_tur="website", resim=None, sinif="", robots=None):
    kok = "../" * rel_html.count("/")
    t, tam = _baslik_kisalt(baslik)
    acik = H["kisa_metin"](aciklama, 154)
    kw = {"tam_baslik": tam}
    if robots: kw["robots"] = robots
    head = H["seo_head"](t, acik, yol, kok, og_tur, resim, jsonld, **kw)
    dk = f'<a href="{kok}dedekorkut">Dede Korkut Günlüğü</a>' if os.path.exists(os.path.join(base, "dedekorkut.html")) else ""
    nav = (f'<a href="/">Ana Sayfa</a>{kultur_menu(kok)}<a href="{kok}kose">Köşe Yazıları</a>{dk}'
           f'{arsiv_dosyasi_link(kok)}<a href="{kok}arsiv/" class="arsiv-link">📚 Arşiv</a>')
    sayfa = f'''<!DOCTYPE html>
<html lang="tr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
{head}
<link rel="stylesheet" href="{kok}styles.css">
</head>
<body>
<div class="container">
<header class="header"><div class="site-adi"><a href="/">Diojen <span>News</span></a></div><div class="logo">D</div></header>
{MOBIL_DUGME}<nav class="navbar">{nav}</nav>
<main class="kose-sayfa ozel-sayfa {sinif}"><section class="bolum">{govde}</section></main>
<footer class="footer"><p>&copy; {datetime.date.today().year} Diojen News. Tüm hakları saklıdır.</p></footer>
</div>
</body>
</html>'''
    p = os.path.join(base, rel_html); os.makedirs(os.path.dirname(p), exist_ok=True)
    open(p, "w", encoding="utf-8").write(sayfa)
def _sm(yol, lastmod, rel, baslik=None, yayin_iso=None):
    H["sitemap_ekle"](yol, lastmod, rel, baslik, yayin_iso)
def _onizleme_bandi(tarih):
    return f'<p class="onizleme-bandi">ÖNİZLEME · Yayın tarihi {es(tarih)}; bu tarihten önce canlıda görünmez.</p>'

# ---------------- Ogrenci Kosesi ----------------
OK_ACIKLAMA = "Sinema ve televizyon öğrencileri için haftalık, öğretici köşe: başvuru takvimleri, film çözümlemeleri, sektöre giriş notları ve ücretsiz kaynaklar."
def ogrenci_yazilar(v, ornek_dahil=True):
    y = [x for x in al(v, "yazilar", []) if isinstance(x, dict) and (ornek_dahil or not x.get("ornek")) and yayinda(al(x, "tarih"))]
    for x in y:
        if not x.get("slug"): x["slug"] = slugify(al(x, "baslik"))
    return sorted(y, key=lambda x: _tarih(al(x, "tarih")) or datetime.date.min, reverse=True)
def _metin_html(metin):
    out = []
    for p in _s(metin).split("\n"):
        p = p.strip()
        if not p: continue
        if re.match(r"^\d{1,2}\.\s+\S", p) and len(p) < 220: out.append(f'<h3 class="ok-ara">{linkle(p)}</h3>')
        else: out.append(f"<p>{linkle(p)}</p>")
    return "".join(out)
def _ok_meta(y):
    yazar = al(y, "yazar")
    konuk = " · ".join(x for x in (es(al(y, "ogrenci")), es(al(y, "okul"))) if x)
    return " · ".join(x for x in (f'Yazar: <b class="ok-yazar">{es(yazar)}</b>' if yazar else "", konuk, es(al(y, "tarih"))) if x)
def _ok_kart(y, kok, h="h2"):
    href = f'{kok}{OK_DIR}/{es(y["slug"])}'
    et = '<span class="ornek-etiket">ÖRNEK</span> ' if al(y, "ornek") else ""
    on = _onizleme_bandi(al(y, "tarih")) if ileri_mi(al(y, "tarih")) else ""
    return (f'<article class="card ok-kart{" ornek" if al(y, "ornek") else ""}">{on}<div class="meta">{et}{_ok_meta(y)}</div>'
            f'<{h}><a href="{href}">{es(al(y, "baslik"))}</a></{h}><p class="ok-ozet">{es(al(y, "ozet"))}</p><a class="makale-oku" href="{href}">Yazıyı oku →</a></article>')
def _bos_ogrenci():
    return '<div class="bos-durum"><p class="bos-baslik">İlk yazı yakında</p><p>Sinema ve televizyon okuyan ya da okumaya hazırlananlar için haftalık, öğretici bir köşe: başvuru takvimleri, film çözümlemeleri, sektöre giriş notları ve ücretsiz kaynaklar.</p></div>'
def uret_ogrenci(base):
    v = yukle(base, "ogrenci-kosesi.json"); yaz = ogrenci_yazilar(v, False); kok1 = "../../"
    son = _iso(al(yaz[0], "tarih")) if yaz else ""
    for y in yaz:
        yol = f'{OK_DIR}/{y["slug"]}'; iso = _iso(al(y, "tarih"))
        gs = _s(al(y, "gorsel")); img = ""
        if gs:
            img = f'<img class="ok-gorsel" src="{es(gs if re.match(r"^https?://", gs) else kok1 + gs)}" alt="{es(al(y, "baslik"))}" loading="lazy">'
        link = f'<p><a class="makale-oku" href="{es(al(y, "link"))}" target="_blank" rel="noopener">Yazının tamamı →</a></p>' if al(y, "link") else ""
        on = _onizleme_bandi(al(y, "tarih")) if ileri_mi(al(y, "tarih")) else ""
        govde = (f'<p class="makale-geri"><a href="./">← Sinema-TV Öğrenci Köşesi</a></p>{on}{etiket(*ETIKET["ogrenci"])}'
                 f'<h1 class="makale-baslik">{es(al(y, "baslik"))}</h1><div class="meta">{_ok_meta(y)}</div><p class="makale-spot">{es(al(y, "ozet"))}</p>'
                 f'<article class="ok-kart ok-tam">{img}<div class="ok-metin">{_metin_html(al(y, "metin"))}</div>{link}</article>'
                 f'<p class="ozel-arsiv-link"><a href="arsiv/">📚 Öğrenci Köşesi arşivi</a></p>')
        deg = H["degisme_tarihi"]("haberler/ogrenci-kosesi.json", iso)
        ld = H["jsonld_haber"](al(y, "baslik"), yol, iso, deg, al(y, "yazar"), H["kisa_metin"](al(y, "ozet"), 200), None, "Sinema-TV Öğrenci Köşesi")
        yaz_sayfa(base, yol + ".html", yol, al(y, "baslik"), al(y, "ozet") or OK_ACIKLAMA, govde, ld, "article", gs if gs and not gs.startswith("http") else None, "ozel-ogrenci")
        if not ileri_mi(al(y, "tarih")): _sm(yol, deg, yol + ".html", al(y, "baslik"), iso)
    kartlar = "".join(_ok_kart(y, kok1) for y in yaz) or _bos_ogrenci()
    govde = (f'{etiket(*ETIKET["ogrenci"])}<h1>Sinema-TV Öğrenci Köşesi</h1>'
             f'<p class="dk-giris">Kültür &amp; Sanat · Her çarşamba. Sinema ve televizyon öğrencileri için haftalık, öğretici bir köşe. Yazar: Selin Arslan.</p>{kartlar}'
             f'<p class="ozel-arsiv-link"><a href="arsiv/">📚 Öğrenci Köşesi arşivi</a></p>')
    yaz_sayfa(base, f"{OK_DIR}/index.html", f"{OK_DIR}/", "Sinema-TV Öğrenci Köşesi", OK_ACIKLAMA, govde,
              H["jsonld_koleksiyon"]("Sinema-TV Öğrenci Köşesi", f"{OK_DIR}/", OK_ACIKLAMA), sinif="ozel-ogrenci")
    _sm(f"{OK_DIR}/", son, f"{OK_DIR}/index.html")
    liste = "".join(f'<li><a href="../{es(y["slug"])}">{es(al(y, "baslik"))}</a> <span class="meta">{es(al(y, "tarih"))}</span></li>' for y in yaz)
    govde = (f'{etiket(*ETIKET["ogrenci"])}<h1>Sinema-TV Öğrenci Köşesi Arşivi</h1><p>{"Toplam " + str(len(yaz)) + " yazı." if yaz else "Henüz yayımlanmış yazı yok."} '
             f'<a href="../">Güncel köşeye dön</a></p><ul class="kose-liste">{liste}</ul>')
    yaz_sayfa(base, f"{OK_DIR}/arsiv/index.html", f"{OK_DIR}/arsiv/", "Sinema-TV Öğrenci Köşesi Arşivi", "Sinema-TV Öğrenci Köşesi'nin tüm yazıları, yeniden eskiye.", govde,
              H["jsonld_koleksiyon"]("Sinema-TV Öğrenci Köşesi Arşivi", f"{OK_DIR}/arsiv/"), sinif="ozel-ogrenci")
    _sm(f"{OK_DIR}/arsiv/", son, f"{OK_DIR}/arsiv/index.html")

# ---------------- Gise ----------------
def _int(n):
    try: return int(str(n).replace(".", "").replace(",", "")) if isinstance(n, str) else int(n)
    except Exception: return None
def _para(n, para):
    i = _int(n)
    if i is None: return "—" if n in (None, "") else es(n)
    return ("₺" if para == "TRY" else "$") + f"{i:,}".replace(",", ".")
def _sayi(n):
    i = _int(n)
    if i is None: return "—" if n in (None, "") else es(n)
    return f"{i:,}".replace(",", ".")
ESKI = {"hafta_sonu": "hasilat_hafta_sonu", "toplam": "hasilat_toplam"}
def _satir(r):
    r = dict(r) if isinstance(r, dict) else {}
    for a, b in ESKI.items():
        if a in r and b not in r: r[b] = r.pop(a)
    return r
KOLONLAR = [("sira", "Sıra"), ("film", "Film"), ("hafta", "Hafta"), ("seyirci_hafta", "Haftalık seyirci"), ("hasilat_hafta", "Haftalık hasılat"),
            ("seyirci_hafta_sonu", "Hafta sonu seyirci"), ("hasilat_hafta_sonu", "Hafta sonu hasılatı"), ("seyirci_toplam", "Toplam seyirci"), ("hasilat_toplam", "Toplam hasılat"), ("yorum", "Not")]
def _yc_slug(o): return _s(al(o, "slug")) or slugify(al(o, "baslik"))
def gise_tablolari(v, yc=None, yc_href=""):
    """yc verilirse film adi #yc-<slug> ozetine baglanir (yc_href: ozetlerin bulundugu sayfa, '' = ayni sayfa)."""
    yc_sluglar = {_yc_slug(o) for o in (al(yc, "ogeler", []) if yc else []) if isinstance(o, dict)}
    bl = []
    for t in al(v, "tablolar", []):
        if not isinstance(t, dict): continue
        p = al(t, "para"); sat = [_satir(r) for r in (al(t, "satirlar", []) or [])]
        kay = f'<a href="{es(al(t, "kaynak_url"))}" target="_blank" rel="noopener">{es(al(t, "kaynak"))}</a>' if al(t, "kaynak_url") else es(al(t, "kaynak"))
        ust = f'<div class="meta">Dönem: {es(al(t, "donem", "—"))} · Kaynak: {kay}</div>'
        if not sat:
            bl.append(f'<article class="gise-tablo"><h2>{es(al(t, "baslik"))}</h2>{ust}<p class="bos">Veri alınamadı.</p></article>'); continue
        kol = [(k, a) for k, a in KOLONLAR if any(r.get(k) not in (None, "") for r in sat)]
        def hucre(k, r):
            x = r.get(k)
            if k.startswith("hasilat"): return f'<td class="sayi">{_para(x, p)}</td>'
            if k.startswith("seyirci"): return f'<td class="sayi">{_sayi(x)}</td>'
            if k == "film":
                hedef = _s(r.get("yeni_cikanlar_id")) or slugify(x)
                if hedef in yc_sluglar: return f'<td class="film"><a href="{yc_href}#yc-{es(hedef)}" title="Yeni Çıkanlar özeti">{es(x)}</a> <span class="yc-isaret">yeni</span></td>'
                return f'<td class="film">{es(x)}</td>'
            if k == "yorum": return f'<td class="yorum">{es(x)}</td>'
            return f'<td class="sayi">{es(x) if x not in (None, "") else "—"}</td>'
        th = "".join(f"<th>{a}</th>" for _, a in kol)
        tr = "".join("<tr>" + "".join(hucre(k, r) for k, _ in kol) + "</tr>" for r in sat)
        notu = f'<p class="gise-not">{es(al(t, "not"))}</p>' if al(t, "not") else ""
        bl.append(f'<article class="gise-tablo" id="tablo-{es(al(t, "id"))}"><h2>{es(al(t, "baslik"))}</h2>{ust}<div class="tablo-kap"><table><thead><tr>{th}</tr></thead><tbody>{tr}</tbody></table></div>{notu}</article>')
    return "".join(bl) or '<p class="bos">Veri alınamadı.</p>'
def yeni_kartlar(v, h="h3"):
    og = [o for o in al(v, "ogeler", []) if isinstance(o, dict)]
    if not og: return '<p class="bos">Bu hafta için veri alınamadı.</p>'
    grup = []
    for tur, ad in (("film", "Sinemada"), ("dizi", "Dizi ve dijital platformlar")):
        k = []
        for o in [x for x in og if al(x, "tur_ad") == tur]:
            kay = f'<a class="kaynak" href="{es(al(o, "kaynak_url"))}" target="_blank" rel="noopener">Kaynak: {es(al(o, "kaynak"))}</a>' if al(o, "kaynak_url") else ""
            k.append(f'<article class="yc-kart" id="yc-{es(_yc_slug(o))}"><div class="yc-ust"><span class="yc-tur">{"🎬 Film" if tur == "film" else "📺 Dizi"}</span> <span class="yc-platform">{es(al(o, "platform"))}</span></div>'
                     f'<{h}>{es(al(o, "baslik"))}</{h}><div class="meta">{es(al(o, "tur"))} · {es(al(o, "tarih"))}</div><p>{es(al(o, "ozet"))}</p>{kay}</article>')
        if k: grup.append(f'<h2 class="yc-grup">{ad}</h2><div class="yc-izgara">{"".join(k)}</div>')
    return "".join(grup)
def _gise_eserler(v):
    tr = next((t for t in al(v, "tablolar", []) if isinstance(t, dict) and al(t, "satirlar")), None)
    return [{"tur": "Movie", "ad": _s(al(r, "film"))} for r in (al(tr, "satirlar", []) if tr else []) if al(r, "film")]
def _yc_eserler(v, yol):
    return [{"tur": "TVSeries" if al(o, "tur_ad") == "dizi" else "Movie", "ad": _s(al(o, "baslik")), "url": H["mutlak"](yol) + "#yc-" + _yc_slug(o),
             "genre": [g.strip() for g in _s(al(o, "tur")).split(",") if g.strip()] or None}
            for o in al(v, "ogeler", []) if isinstance(o, dict) and al(o, "baslik")]
def _anlik_kaydet(base, klasor, v):
    """Haftalik anlik goruntu: haberler/<klasor>/<hafta_kodu>.json (ayni hafta guncellenirse uzerine yazilir)."""
    hk = _s(al(v, "hafta_kodu"))
    if not re.match(r"^\d{4}-\d{2}$", hk): return
    d = os.path.join(base, "haberler", klasor); os.makedirs(d, exist_ok=True)
    p = os.path.join(d, hk + ".json"); yeni = json.dumps(v, ensure_ascii=False, indent=1)
    if not os.path.exists(p) or open(p, encoding="utf-8").read() != yeni: open(p, "w", encoding="utf-8").write(yeni)
def _anliklar(base, klasor):
    out = {}
    for p in sorted(glob.glob(os.path.join(base, "haberler", klasor, "*.json"))):
        try: out[os.path.basename(p)[:-5]] = json.load(open(p, encoding="utf-8"))
        except Exception: pass
    return out
GISE_ACIKLAMA = "Türkiye ve dünya gişesinde haftanın tabloları, sinemada ve dijital platformlarda yeni çıkan film ve diziler. Her salı güncellenir."
def uret_gise(base):
    v = yukle(base, "gise.json"); yc = yukle(base, "yeni-cikanlar.json")
    if any(al(t, "satirlar") for t in al(v, "tablolar", []) if isinstance(t, dict)): _anlik_kaydet(base, "gise-arsiv", v)
    if al(yc, "ogeler"): _anlik_kaydet(base, "yeni-cikanlar-arsiv", yc)
    hk = _s(al(v, "hafta_kodu")); yhk = _s(al(yc, "hafta_kodu")); son = H["iso_tarih"](al(v, "guncelleme"))
    gun = f' Son güncelleme: {es(al(v, "guncelleme"))}.' if al(v, "guncelleme") else ""
    kalici = f' <a href="{es(hk)}">Bu haftanın kalıcı sayfası →</a>' if hk else ""
    govde = (f'{etiket(*ETIKET["gise"])}<h1>Gişe &amp; Yeni Çıkanlar</h1><p class="dk-giris">Türkiye ve dünya gişesi, haftalık (salı).{gun} Tablolar mobilde yana kaydırılabilir.{kalici}</p>'
             f'{gise_tablolari(v, yc)}'
             f'<div class="yc-bolum" id="yeni-cikanlar">{etiket(*ETIKET["yeni"])}<h2>Yeni Çıkanlar</h2><p class="dk-giris">Bu hafta sinemada ve platformlarda başlayanlar. {es(al(yc, "donem"))} '
             f'<a href="../{YC_DIR}/">Yeni Çıkanlar sayfası →</a></p>{yeni_kartlar(yc)}</div>'
             f'<p class="ozel-arsiv-link"><a href="arsiv/">📚 Gişe arşivi (hafta hafta)</a> · <a href="../{YC_DIR}/arsiv/">📚 Yeni Çıkanlar arşivi</a></p>')
    ld = [H["jsonld_eser_listesi"]("Türkiye gişesi: haftanın filmleri", f"{GISE_DIR}/", _gise_eserler(v)),
          H["jsonld_eser_listesi"]("Yeni Çıkanlar: film ve dizi", f"{GISE_DIR}/", _yc_eserler(yc, f"{GISE_DIR}/"))]
    yaz_sayfa(base, f"{GISE_DIR}/index.html", f"{GISE_DIR}/", "Gişe & Yeni Çıkanlar", GISE_ACIKLAMA, govde, ld, sinif="ozel-gise")
    _sm(f"{GISE_DIR}/", son, f"{GISE_DIR}/index.html")
    # haftalik gise sayfalari
    anlik = _anliklar(base, "gise-arsiv")
    if hk and hk not in anlik and al(v, "tablolar"): anlik[hk] = v
    for kod, vv in anlik.items():
        yol = f"{GISE_DIR}/{kod}"
        g = (f'<p class="makale-geri"><a href="./">← Güncel gişe</a> · <a href="arsiv/">Gişe arşivi</a></p>{etiket(*ETIKET["gise"])}'
             f'<h1>Gişe Hasılatları: {es(hafta_etiketi(kod))}</h1><p class="dk-giris">Tablolar mobilde yana kaydırılabilir.</p>{gise_tablolari(vv)}')
        yaz_sayfa(base, yol + ".html", yol, f"Gişe Hasılatları {kod.replace('-', ' / ')}. hafta", f"Türkiye ve dünya gişe tabloları, {hafta_etiketi(kod)}. Sıra, film, hasılat ve seyirci.", g,
                  H["jsonld_eser_listesi"](f"Gişe {kod}", yol, _gise_eserler(vv)), sinif="ozel-gise")
        _sm(yol, H["iso_tarih"](al(vv, "guncelleme")), yol + ".html")
    li = "".join(f'<li><a href="../{k}">{es(hafta_etiketi(k))}</a></li>' for k in sorted(anlik, reverse=True))
    g = (f'{etiket(*ETIKET["gise"])}<h1>Gişe Arşivi</h1><p>{"Toplam " + str(len(anlik)) + " hafta." if anlik else "Henüz arşivlenmiş hafta yok."} Haftalık güncelleme günü: salı. '
         f'<a href="../">Güncel gişeye dön</a></p><ul class="kose-liste">{li}</ul>')
    yaz_sayfa(base, f"{GISE_DIR}/arsiv/index.html", f"{GISE_DIR}/arsiv/", "Gişe Arşivi: Hafta Hafta", "Diojen News gişe tabloları arşivi, ISO haftasına göre yeniden eskiye.", g,
              H["jsonld_koleksiyon"]("Gişe Arşivi", f"{GISE_DIR}/arsiv/"), sinif="ozel-gise")
    _sm(f"{GISE_DIR}/arsiv/", son, f"{GISE_DIR}/arsiv/index.html")
    # Yeni Cikanlar
    yson = H["iso_tarih"](al(yc, "guncelleme"))
    g = (f'{etiket(*ETIKET["yeni"])}<h1>Yeni Çıkanlar</h1><p class="dk-giris">Bu hafta sinemada ve dijital platformlarda başlayan film ve diziler. {es(al(yc, "donem"))}'
         + (f' <a href="{es(yhk)}">Bu haftanın kalıcı sayfası →</a>' if yhk else "") + f'</p>{yeni_kartlar(yc, "h2")}'
         f'<p class="ozel-arsiv-link"><a href="arsiv/">📚 Yeni Çıkanlar arşivi</a> · <a href="../{GISE_DIR}/">Gişe tabloları →</a></p>')
    yaz_sayfa(base, f"{YC_DIR}/index.html", f"{YC_DIR}/", "Yeni Çıkanlar: Bu Hafta Film ve Dizi", "Sinemada ve dijital platformlarda bu hafta başlayan film ve diziler: tür, platform ve kısa özet.", g,
              H["jsonld_eser_listesi"]("Yeni Çıkanlar", f"{YC_DIR}/", _yc_eserler(yc, f"{YC_DIR}/")), sinif="ozel-yeni")
    _sm(f"{YC_DIR}/", yson, f"{YC_DIR}/index.html")
    yan = _anliklar(base, "yeni-cikanlar-arsiv")
    if yhk and yhk not in yan and al(yc, "ogeler"): yan[yhk] = yc
    for kod, vv in yan.items():
        yol = f"{YC_DIR}/{kod}"
        g = (f'<p class="makale-geri"><a href="./">← Bu haftanın yeni çıkanları</a> · <a href="arsiv/">Arşiv</a></p>{etiket(*ETIKET["yeni"])}'
             f'<h1>Yeni Çıkanlar: {es(hafta_etiketi(kod))}</h1><p class="dk-giris">{es(al(vv, "donem"))}</p>{yeni_kartlar(vv, "h2")}')
        yaz_sayfa(base, yol + ".html", yol, f"Yeni Çıkanlar {kod.replace('-', ' / ')}. hafta", f"Sinemada ve platformlarda başlayan film ve diziler, {hafta_etiketi(kod)}.", g,
                  H["jsonld_eser_listesi"](f"Yeni Çıkanlar {kod}", yol, _yc_eserler(vv, yol)), sinif="ozel-yeni")
        _sm(yol, H["iso_tarih"](al(vv, "guncelleme")), yol + ".html")
    li = "".join(f'<li><a href="../{k}">{es(hafta_etiketi(k))}</a></li>' for k in sorted(yan, reverse=True))
    g = (f'{etiket(*ETIKET["yeni"])}<h1>Yeni Çıkanlar Arşivi</h1><p>{"Toplam " + str(len(yan)) + " hafta." if yan else "Henüz arşivlenmiş hafta yok."} '
         f'<a href="../">Bu haftaya dön</a></p><ul class="kose-liste">{li}</ul>')
    yaz_sayfa(base, f"{YC_DIR}/arsiv/index.html", f"{YC_DIR}/arsiv/", "Yeni Çıkanlar Arşivi", "Yeni Çıkanlar arşivi: haftalara göre sinema ve platform yenilikleri.", g,
              H["jsonld_koleksiyon"]("Yeni Çıkanlar Arşivi", f"{YC_DIR}/arsiv/"), sinif="ozel-yeni")
    _sm(f"{YC_DIR}/arsiv/", yson, f"{YC_DIR}/arsiv/index.html")

# ---------------- Arsiv Dosyasi (yalniz yayinlanmis makaleler/*.md) ----------------
AD_ACIKLAMA = "Arşiv Dosyası: WikiLeaks arşivindeki belgelerden, görevi bırakmış dünya liderleri üzerine haftalık özel haber dizisi."
def arsiv_dosyasi_mi(m):
    k = _s(al(m, "kategori")).casefold()
    return "arşiv dosyası" in k or "arsiv dosyasi" in k
def ad_slug(m):
    sl = _s(al(m, "slug"))
    return sl + "-dosya" if sl in AYRILMIS else sl
def arsiv_dosyalari(makaleler):
    """Yayinlanmis (tarihi gelmis) Arsiv Dosyasi makaleleri, yeniden eskiye."""
    return [m for m in (makaleler or []) if arsiv_dosyasi_mi(m) and yayinda(iso=al(m, "sirala"))]
def ozel_haber_kutusu(m, kok="", ornek=False):
    et = '<span class="ornek-etiket">ÖRNEK</span> ' if ornek else ""
    href = "#" if ornek else f'{kok}{AD_DIR}/{es(ad_slug(m))}'
    by = " · ".join(x for x in (f'Yazar: {es(al(m, "yazar"))}' if al(m, "yazar") else "", es(al(m, "tarih"))) if x)
    return (f'<section class="ozel-haber{" ornek" if ornek else ""}" id="ozel-haber"><div class="oh-ust">{et}{etiket(*ETIKET["ozel"])} {etiket(*ETIKET["ad"])}</div>'
            f'<h2><a href="{href}">{es(al(m, "baslik"))}</a></h2><div class="meta">{by}</div><p>{es(al(m, "spot"))}</p>'
            f'<a class="makale-oku" href="{href}">Dosyayı oku →</a> · <a class="makale-oku" href="{kok}{AD_DIR}/">Tüm Arşiv Dosyaları</a></section>')
def uret_arsiv_dosyasi(base, makaleler):
    ler = arsiv_dosyalari(makaleler); ks = H.get("kaynak_satiri", es)
    for m in ler:
        sl = ad_slug(m); yol = f"{AD_DIR}/{sl}"; iso = al(m, "sirala") if al(m, "sirala") != "0000-00-00" else ""
        kay = ""
        if al(m, "kaynaklar"):
            kay = '<section class="makale-kaynaklar"><h2>Kaynaklar</h2><ol>' + "".join(f'<li id="k{n}" value="{n}">{ks(x)}</li>' for n, x in m["kaynaklar"]) + '</ol></section>'
        res = ("gorseller/" + m["slug"] + ("-900.jpg" if al(m, "resim900_var") else ".jpg")) if al(m, "resim_var") else None
        img = f'<figure class="makale-gorsel"><img src="../{es(res)}" alt="{es(al(m, "baslik"))}"></figure>' if res else ""
        on = _onizleme_bandi(al(m, "tarih")) if ileri_mi(iso=iso) else ""
        govde = (f'<p class="makale-geri"><a href="./">← Arşiv Dosyası</a></p>{on}{etiket(*ETIKET["ozel"])} {etiket(*ETIKET["ad"])}'
                 f'<div class="meta">{"Yazar: " + es(al(m, "yazar")) + " · " if al(m, "yazar") else ""}{es(al(m, "tarih"))}</div>'
                 f'<h1 class="makale-baslik">{es(al(m, "baslik"))}</h1>' + (f'<p class="makale-spot">{es(al(m, "spot"))}</p>' if al(m, "spot") else "")
                 + f'{img}<div class="makale-govde">{al(m, "govde")}</div>{kay}')
        deg = H["degisme_tarihi"](f'makaleler/{m["slug"]}.md', iso)
        ld = H["jsonld_haber"](al(m, "baslik"), yol, iso, deg, al(m, "yazar"), H["kisa_metin"](al(m, "spot"), 200), [res] if res else None, "Arşiv Dosyası")
        yaz_sayfa(base, yol + ".html", yol, al(m, "baslik"), al(m, "spot") or AD_ACIKLAMA, govde, ld, "article", res, "ozel-ad")
        if not ileri_mi(iso=iso): _sm(yol, deg, yol + ".html", al(m, "baslik"), iso)
    if ler:
        ic = "".join(f'<article class="card"><div class="meta">{es(al(m, "yazar"))} · {es(al(m, "tarih"))}</div><h2><a href="{es(ad_slug(m))}">{es(al(m, "baslik"))}</a></h2><p>{es(al(m, "spot"))}</p></article>' for m in ler[:5])
    else:
        ic = '<div class="bos-durum"><p class="bos-baslik">İlk dosya yakında</p><p>Arşiv Dosyası, WikiLeaks arşivindeki belgelerden yola çıkan haftalık özel haber dizisidir. Her dosya editör onayından sonra pazar sabahı yayımlanır.</p></div>'
    son = ler[0]["sirala"] if ler else ""
    govde = (f'{etiket(*ETIKET["ad"])}<h1>Arşiv Dosyası</h1><p class="dk-giris">Özel haber · Haftalık (pazar). Kaynak: WikiLeaks arşivi.</p>{ic}'
             f'<p class="ozel-arsiv-link"><a href="arsiv/">📚 Arşiv Dosyası arşivi (tüm dosyalar)</a></p>')
    yaz_sayfa(base, f"{AD_DIR}/index.html", f"{AD_DIR}/", "Arşiv Dosyası: Özel Haber", AD_ACIKLAMA, govde, H["jsonld_koleksiyon"]("Arşiv Dosyası", f"{AD_DIR}/", AD_ACIKLAMA), sinif="ozel-ad")
    _sm(f"{AD_DIR}/", son, f"{AD_DIR}/index.html")
    li = "".join(f'<li><a href="../{es(ad_slug(m))}">{es(al(m, "baslik"))}</a> <span class="meta">{es(al(m, "tarih"))}</span></li>' for m in ler)
    govde = (f'{etiket(*ETIKET["ad"])}<h1>Arşiv Dosyası Arşivi</h1><p>{"Toplam " + str(len(ler)) + " dosya." if ler else "Henüz yayımlanmış dosya yok."} '
             f'<a href="../">Arşiv Dosyası sayfasına dön</a></p><ul class="kose-liste">{li}</ul>')
    yaz_sayfa(base, f"{AD_DIR}/arsiv/index.html", f"{AD_DIR}/arsiv/", "Arşiv Dosyası Arşivi", "Arşiv Dosyası özel haber dizisinin yayımlanmış tüm dosyaları.", govde,
              H["jsonld_koleksiyon"]("Arşiv Dosyası Arşivi", f"{AD_DIR}/arsiv/"), sinif="ozel-ad")
    _sm(f"{AD_DIR}/arsiv/", son, f"{AD_DIR}/arsiv/index.html")

# ---------------- Ana sayfa: Kultur & Sanat ozeti ----------------
def kultur_ozet_html(base, kok=""):
    yaz = ogrenci_yazilar(yukle(base, "ogrenci-kosesi.json"), False); gv = yukle(base, "gise.json")
    if yaz:
        y = yaz[0]
        ok = (f'<div class="meta">Yazar: {es(al(y, "yazar"))} · {es(al(y, "tarih"))}</div>'
              f'<h4><a href="{kok}{OK_DIR}/{es(y["slug"])}">{es(al(y, "baslik"))}</a></h4><p>{es(al(y, "ozet"))}</p>')
    else:
        ok = '<p class="ko-bos">İlk yazı yakında. Sinema ve televizyon öğrencileri için haftalık köşe her çarşamba burada.</p>'
    tr = next((t for t in al(gv, "tablolar", []) if isinstance(t, dict) and al(t, "id") == "turkiye"), None)
    if tr and al(tr, "satirlar"):
        def _oz(r):
            r = _satir(r)
            if r.get("seyirci_hafta") not in (None, ""): return f'{_sayi(r.get("seyirci_hafta"))} seyirci · {_para(r.get("hasilat_hafta"), al(tr, "para"))} (hafta)'
            return f'{_sayi(r.get("seyirci_hafta_sonu"))} seyirci · {_para(r.get("hasilat_hafta_sonu"), al(tr, "para"))} (hafta sonu)'
        li = "".join(f'<li><b>{es(al(r, "sira"))}.</b> {es(al(r, "film"))} <span class="meta">{_oz(r)}</span></li>' for r in tr["satirlar"][:3])
        gs = f'<div class="meta">Türkiye · {es(al(tr, "donem"))}</div><ol class="ko-gise">{li}</ol>'
    else:
        gs = '<p class="ko-bos">Gişe verisi alınamadı.</p>'
    return (f'<div class="kultur-ozet"><div class="ko-kutu">{etiket(*ETIKET["ogrenci"])}{ok}<a class="makale-oku" href="{kok}{OK_DIR}/">Öğrenci Köşesi →</a></div>'
            f'<div class="ko-kutu">{etiket(*ETIKET["gise"])}<h4>Gişede ilk 3</h4>{gs}<a class="makale-oku" href="{kok}{GISE_DIR}/">Gişe &amp; Yeni Çıkanlar →</a></div></div>')

# ---------------- giris noktalari ----------------
def uret(base, makaleler, yardimcilar):
    H.update({k: yardimcilar[k] for k in ("seo_head", "jsonld_haber", "jsonld_koleksiyon", "jsonld_eser_listesi", "sitemap_ekle", "mutlak",
                                          "kisa_metin", "degisme_tarihi", "iso_tarih") })
    if "kaynak_satiri" in yardimcilar: H["kaynak_satiri"] = yardimcilar["kaynak_satiri"]
    uret_ogrenci(base); uret_gise(base); uret_arsiv_dosyasi(base, makaleler)

BOLUM_YOLLARI = (OK_DIR, GISE_DIR, YC_DIR, AD_DIR)
def arsiv_kopyasi_linkleri(hedef):
    """yayin.py: arsiv/<sayi>/ kopyasindaki sayfalarda bolum linkleri canli (guncel) bolume gitsin."""
    for yol in glob.glob(os.path.join(hedef, "*.html")) + glob.glob(os.path.join(hedef, "*", "*.html")):
        kok_ic = os.path.dirname(yol) != hedef
        on, ust = ("../", "../../../") if kok_ic else ("", "../../")
        t = open(yol, encoding="utf-8").read(); y = t
        for b in BOLUM_YOLLARI: y = y.replace(f'href="{on}{b}/', f'href="{ust}{b}/')
        if y != t: open(yol, "w", encoding="utf-8").write(y)
ISARET = "<!--bolum-arsivleri-->"
def ana_arsiv_index_ekle(base):
    """arsiv/index.html'e bolum arsivlerinin linkleri (sayi listesine karismaz)."""
    p = os.path.join(base, "arsiv", "index.html")
    if not os.path.exists(p): return
    t = open(p, encoding="utf-8").read()
    if ISARET in t: return
    blok = (f'{ISARET}<section class="bolum-arsivleri"><h2>Bölüm arşivleri</h2><ul class="ba-liste">'
            f'<li>{etiket(*ETIKET["ogrenci"])} <a href="../{OK_DIR}/arsiv/">Sinema-TV Öğrenci Köşesi arşivi</a></li>'
            f'<li>{etiket(*ETIKET["gise"])} <a href="../{GISE_DIR}/arsiv/">Gişe arşivi (hafta hafta)</a></li>'
            f'<li>{etiket(*ETIKET["yeni"])} <a href="../{YC_DIR}/arsiv/">Yeni Çıkanlar arşivi</a></li>'
            f'<li>{etiket(*ETIKET["ad"])} <a href="../{AD_DIR}/arsiv/">Arşiv Dosyası arşivi</a></li></ul></section><h2 class="sayi-baslik">Gazete sayıları</h2>')
    open(p, "w", encoding="utf-8").write(t.replace("<ul>", blok + "<ul>", 1))
