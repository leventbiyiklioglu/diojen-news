#!/usr/bin/env python3
"""Diojen News ozel bolumleri.
- Sinema-TV Ogrenci Kosesi  : haberler/ogrenci-kosesi.json -> ogrenci-kosesi.html, arsiv: ogrenci-kosesi/arsiv/<YYYY-MM-DD>/
- Gise & Yeni Cikanlar      : haberler/gise.json + haberler/yeni-cikanlar.json -> gise.html
                              arsivler: gise/arsiv/<tarih>/ ve yeni-cikanlar/arsiv/<tarih>/
- Arsiv Dosyasi (Ozel Haber): YALNIZCA yayinlanmis makaleler/*.md (kategori "Arşiv Dosyası") -> arsiv-dosyasi.html,
                              arsiv-dosyasi-arsivi/index.html. taslak/ ve arsiv-dosyasi/ (Kaan'in calisma klasoru) OKUNMAZ.
build.py:  uret(base, makaleler)   yayin.py: arsivle(base); ana_arsiv_index_ekle(base)
Elle: python3 ozel_sayfalar.py arsivle [--zorla]
"""
import os, json, html, datetime, sys, re
e = html.escape
SITE = "https://diojennews.com"
GUNLER = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"]
# Haftalik arsivlenen birimler. gun: 0=pazartesi
SAYFALAR = {
    "ogrenci-kosesi": {"ad": "Sinema-TV Öğrenci Köşesi", "json": "ogrenci-kosesi.json", "gun": 2, "sayfa": "ogrenci-kosesi",
        "title": "Sinema-TV Öğrenci Köşesi", "etiket": ("e-ogrenci", "ÖĞRENCİ KÖŞESİ"),
        "desc": "Sinema ve televizyon bölümü öğrencilerinin yazıları, film eleştirileri ve kısa film notları. Diojen News Kültür & Sanat bölümünde her hafta."},
    "gise": {"ad": "Gişe & Yeni Çıkanlar", "json": "gise.json", "gun": 1, "sayfa": "gise",
        "title": "Gişe & Yeni Çıkanlar", "etiket": ("e-gise", "GİŞE"),
        "desc": "Türkiye ve dünya gişesinde haftanın tabloları ile sinemada ve dijital platformlarda yeni çıkan film ve diziler. Her hafta güncellenir."},
    "yeni-cikanlar": {"ad": "Yeni Çıkanlar", "json": "yeni-cikanlar.json", "gun": 1, "sayfa": "gise",
        "title": "Yeni Çıkanlar: Film ve Dizi", "etiket": ("e-yeni", "YENİ ÇIKANLAR"),
        "desc": "Sinemada ve dijital platformlarda bu hafta başlayan film ve diziler: tür, platform ve kısa özet."},
}
AD_SLUG = "arsiv-dosyasi"
AD = {"ad": "Arşiv Dosyası", "title": "Arşiv Dosyası: Özel Haber", "etiket": ("e-arsivdosyasi", "ARŞİV DOSYASI"),
      "desc": "Diojen News özel haber dizisi Arşiv Dosyası: WikiLeaks arşivinden, görevi bırakmış dünya liderleriyle ilgili belgeler. Haftalık."}

def etiket(sinif, metin): return f'<span class="etiket {sinif}">{e(metin)}</span>'

# ---------------- menu ----------------
def kultur_menu(kok="", kultur_href=None):
    kh = kultur_href if kultur_href is not None else f"{kok}DiojenNews.html#kultur"
    return (f'<details class="nav-acilir"><summary>Kültür &amp; Sanat</summary><div class="alt-menu">'
            f'<a href="{kh}">Kültür &amp; Sanat haberleri</a>'
            f'<a href="{kok}ogrenci-kosesi.html">Sinema-TV Öğrenci Köşesi</a>'
            f'<a href="{kok}gise.html">Gişe &amp; Yeni Çıkanlar</a></div></details>')
def arsiv_dosyasi_link(kok=""): return f'<a href="{kok}{AD_SLUG}.html" class="nav-ad">Arşiv Dosyası</a>'
def nav_linkleri(kok=""):
    """Kategori linki olmayan sayfalarin menusune: Kultur & Sanat acilir menusu + Arsiv Dosyasi."""
    return kultur_menu(kok) + arsiv_dosyasi_link(kok)
def yan_alt(kok=""):
    return (f'<ul class="yan-alt"><li><a href="{kok}ogrenci-kosesi.html">↳ Sinema-TV Öğrenci Köşesi</a></li>'
            f'<li><a href="{kok}gise.html">↳ Gişe &amp; Yeni Çıkanlar</a></li></ul>')

def yukle(base, slug):
    try: return json.load(open(os.path.join(base, "haberler", SAYFALAR[slug]["json"]), encoding="utf-8"))
    except Exception: return {}

def _bas(base, kok, govde, title, desc, canon, noindex=False, sinif=""):
    dk = f'<a href="{kok}dedekorkut.html">Dede Korkut Günlüğü</a>' if os.path.exists(os.path.join(base, "dedekorkut.html")) else ""
    nav = (f'<a href="{kok}DiojenNews.html">Ana Sayfa</a>{kultur_menu(kok)}<a href="{kok}kose.html">Köşe Yazıları</a>{dk}'
           f'{arsiv_dosyasi_link(kok)}<a href="{kok}arsiv/index.html" class="arsiv-link">📚 Arşiv</a>')
    robots = '\n<meta name="robots" content="noindex, follow">' if noindex else ""
    return f'''<!DOCTYPE html>
<html lang="tr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{e(title)} - Diojen News</title>
<meta name="description" content="{e(desc)}">
<link rel="canonical" href="{canon}">{robots}
<meta property="og:type" content="website">
<meta property="og:site_name" content="Diojen News">
<meta property="og:locale" content="tr_TR">
<meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(desc)}">
<meta property="og:url" content="{canon}">
<meta name="twitter:card" content="summary">
<meta name="twitter:title" content="{e(title)}">
<meta name="twitter:description" content="{e(desc)}">
<link rel="stylesheet" href="{kok}styles.css">
</head>
<body>
<div class="container">
<header class="header"><h1>Diojen <span>News</span></h1><div class="logo">D</div></header>
<nav class="navbar">{nav}</nav>
<div class="kose-sayfa ozel-sayfa {sinif}"><section class="bolum">{govde}</section></div>
<footer class="footer"><p>&copy; {datetime.date.today().year} Diojen News. Tüm hakları saklıdır.</p></footer>
</div>
</body>
</html>'''

def _tarih_anahtar(t):
    m = re.search(r"(\d{2})\.(\d{2})\.(\d{4})", t or "")
    return (m.group(3), m.group(2), m.group(1)) if m else ("0000", "00", "00")

def _ark_link(kok, slug, metin): return f'<a href="{kok}{slug}/arsiv/index.html">📚 {e(metin)}</a>'

# ---------------- Ogrenci Kosesi ----------------
def ogrenci_yazilar(v, ornek_dahil=True):
    y = [x for x in v.get("yazilar", []) if ornek_dahil or not x.get("ornek")]
    return sorted(y, key=lambda x: _tarih_anahtar(x.get("tarih")), reverse=True)

def ogrenci_govde(base, v, kok, arsiv_linki=True):
    yaz = ogrenci_yazilar(v)
    kart = []
    for y in yaz:
        ogr = y.get("ogrenci") or y.get("yazar") or ""
        meta = " · ".join(x for x in (e(ogr), e(y.get("okul", "")), e(y.get("tarih", ""))) if x)
        img = ""
        if y.get("gorsel"):
            src = y["gorsel"] if re.match(r"^https?://", y["gorsel"]) else kok + y["gorsel"]
            img = f'<img class="ok-gorsel" src="{e(src)}" alt="{e(y.get("baslik",""))}" loading="lazy">'
        metin = "".join(f"<p>{e(p.strip())}</p>" for p in (y.get("metin") or "").split("\n") if p.strip())
        link = f'<a class="makale-oku" href="{e(y["link"])}" target="_blank" rel="noopener">Yazının tamamı →</a>' if y.get("link") else ""
        et = '<span class="ornek-etiket">ÖRNEK</span> ' if y.get("ornek") else ""
        kart.append(f'<article class="card ok-kart{" ornek" if y.get("ornek") else ""}">{img}<div class="meta">{et}{meta}</div><h3>{e(y.get("baslik",""))}</h3>'
                    f'<p class="ok-ozet">{e(y.get("ozet",""))}</p>{metin}{link}</article>')
    if not ogrenci_yazilar(v, False):
        kart.insert(0, '<div class="bos-durum"><p class="bos-baslik">İlk yazılar yakında</p><p>Sinema ve televizyon bölümü öğrencilerinin film eleştirileri, kısa film notları ve set günlükleri bu köşede her hafta yayımlanacak.</p></div>')
    ark = f'<p class="ozel-arsiv-link">{_ark_link(kok, "ogrenci-kosesi", "Öğrenci Köşesi arşivi")}</p>' if arsiv_linki else ""
    yazar = f'<span class="yazar">Editör: {e(v["yazar"])}</span>' if v.get("yazar") else ""
    return (f'{etiket(*SAYFALAR["ogrenci-kosesi"]["etiket"])}<h2>Sinema-TV Öğrenci Köşesi {yazar}</h2>'
            f'<p class="dk-giris">Kültür &amp; Sanat · Haftalık köşe (çarşamba). Sinema ve televizyon öğrencilerinin kaleminden.</p>{"".join(kart)}{ark}')

# ---------------- Gise ----------------
def _para(n, para):
    if n is None or n == "": return "—"
    return ("₺" if para == "TRY" else "$") + f"{int(n):,}".replace(",", ".")
def _sayi(n):
    if n is None or n == "": return "—"
    return f"{int(n):,}".replace(",", ".")

def gise_tablolari(v):
    bl = []
    for t in v.get("tablolar", []):
        p = t.get("para", ""); sat = t.get("satirlar") or []
        kay = f'<a href="{e(t["kaynak_url"])}" target="_blank" rel="noopener">{e(t.get("kaynak",""))}</a>' if t.get("kaynak_url") else e(t.get("kaynak", ""))
        ust = f'<div class="meta">Dönem: {e(t.get("donem","—"))} · Kaynak: {kay}</div>'
        if not sat:
            bl.append(f'<article class="gise-tablo"><h3>{e(t.get("baslik",""))}</h3>{ust}<p class="bos">Veri alınamadı.</p></article>'); continue
        kol = [("sira", "Sıra"), ("film", "Film"), ("hafta_sonu", "Hafta sonu hasılatı"), ("toplam", "Toplam hasılat"), ("hafta", "Hafta"), ("seyirci_hafta_sonu", "Hafta sonu seyirci"), ("seyirci_toplam", "Toplam seyirci")]
        kol = [(k, a) for k, a in kol if any(r.get(k) not in (None, "") for r in sat)]
        def hucre(k, r):
            x = r.get(k)
            if k in ("hafta_sonu", "toplam"): return f'<td class="sayi">{_para(x, p)}</td>'
            if k.startswith("seyirci"): return f'<td class="sayi">{_sayi(x)}</td>'
            if k == "film": return f'<td class="film">{e(str(x or ""))}</td>'
            return f'<td class="sayi">{e(str(x if x is not None else "—"))}</td>'
        th = "".join(f"<th>{a}</th>" for _, a in kol)
        tr = "".join("<tr>" + "".join(hucre(k, r) for k, _ in kol) + "</tr>" for r in sat)
        notu = f'<p class="gise-not">{e(t["not"])}</p>' if t.get("not") else ""
        bl.append(f'<article class="gise-tablo" id="tablo-{e(t.get("id",""))}"><h3>{e(t.get("baslik",""))}</h3>{ust}<div class="tablo-kap"><table><thead><tr>{th}</tr></thead><tbody>{tr}</tbody></table></div>{notu}</article>')
    return "".join(bl) or '<p class="bos">Veri alınamadı.</p>'

def yeni_kartlar(v):
    og = v.get("ogeler", [])
    if not og: return '<p class="bos">Bu hafta için veri alınamadı.</p>'
    grup = []
    for tur, ad in (("film", "Sinemada"), ("dizi", "Dizi ve dijital platformlar")):
        k = []
        for o in [x for x in og if x.get("tur_ad") == tur]:
            kay = f'<a class="kaynak" href="{e(o["kaynak_url"])}" target="_blank" rel="noopener">Kaynak: {e(o.get("kaynak",""))}</a>' if o.get("kaynak_url") else ""
            k.append(f'<article class="yc-kart"><div class="yc-ust"><span class="yc-tur">{"🎬 Film" if tur=="film" else "📺 Dizi"}</span> <span class="yc-platform">{e(o.get("platform",""))}</span></div>'
                     f'<h4>{e(o.get("baslik",""))}</h4><div class="meta">{e(o.get("tur",""))} · {e(o.get("tarih",""))}</div><p>{e(o.get("ozet",""))}</p>{kay}</article>')
        if k: grup.append(f'<h3 class="yc-grup">{ad}</h3><div class="yc-izgara">{"".join(k)}</div>')
    return "".join(grup)

def gise_govde(base, v, yc, kok, arsiv_linki=True, yalniz=None):
    """yalniz: None=tam sayfa, 'gise' ya da 'yeni-cikanlar' (arsiv kopyalari icin)"""
    parca = []
    if yalniz in (None, "gise"):
        gun = f' Son güncelleme: {e(v["guncelleme"])}.' if v.get("guncelleme") else ""
        parca.append(f'{etiket(*SAYFALAR["gise"]["etiket"])}<h2>Gişe Hasılatları</h2><p class="dk-giris">Türkiye ve dünya gişesi, haftalık (salı).{gun} Tablolar mobilde yana kaydırılabilir.</p>{gise_tablolari(v)}')
    if yalniz in (None, "yeni-cikanlar"):
        don = f' {e(yc["donem"])}.' if yc.get("donem") else ""
        parca.append(f'<div class="yc-bolum" id="yeni-cikanlar">{etiket(*SAYFALAR["yeni-cikanlar"]["etiket"])}<h2>Yeni Çıkanlar</h2><p class="dk-giris">Bu hafta sinemada ve platformlarda başlayanlar.{don}</p>{yeni_kartlar(yc)}</div>')
    if arsiv_linki:
        parca.append(f'<p class="ozel-arsiv-link">{_ark_link(kok, "gise", "Gişe arşivi (hafta hafta)")} · {_ark_link(kok, "yeni-cikanlar", "Yeni Çıkanlar arşivi")}</p>')
    return "".join(parca)

# ---------------- Arsiv Dosyasi (yalnizca yayinlanmis makaleler) ----------------
def arsiv_dosyasi_mi(m):
    return "arşiv dosyası" in (m.get("kategori", "") or "").casefold() or "arsiv dosyasi" in (m.get("kategori", "") or "").casefold()
def arsiv_dosyalari(makaleler):
    return [m for m in (makaleler or []) if arsiv_dosyasi_mi(m)]

def ozel_haber_kutusu(m, kok="", ornek=False):
    """Ana sayfa ust kisim. m: makale sozlugu (slug, baslik, spot, yazar, tarih)."""
    et = '<span class="ornek-etiket">ÖRNEK</span> ' if ornek else ""
    href = "#" if ornek else f'{kok}makaleler/{e(m["slug"])}.html'
    by = " · ".join(x for x in (f'Yazar: {e(m.get("yazar",""))}' if m.get("yazar") else "", e(m.get("tarih", ""))) if x)
    return (f'<section class="ozel-haber{" ornek" if ornek else ""}" id="ozel-haber"><div class="oh-ust">{et}{etiket("e-ozel", "ÖZEL HABER")} {etiket(*AD["etiket"])}</div>'
            f'<h2><a href="{href}">{e(m.get("baslik",""))}</a></h2><div class="meta">{by}</div><p>{e(m.get("spot",""))}</p>'
            f'<a class="makale-oku" href="{href}">Dosyayı oku →</a> · <a class="makale-oku" href="{kok}{AD_SLUG}.html">Tüm Arşiv Dosyaları</a></section>')

def _ad_liste(ler, kok):
    return "".join(f'<li><a href="{kok}makaleler/{e(m["slug"])}.html">{e(m["baslik"])}</a> <span class="meta">{e(m.get("tarih",""))}</span></li>' for m in ler)

def arsiv_dosyasi_govde(ler, kok):
    if not ler:
        ic = '<div class="bos-durum"><p class="bos-baslik">İlk dosya yakında</p><p>Arşiv Dosyası, WikiLeaks arşivindeki belgelerden yola çıkan haftalık özel haber dizisidir. Her dosya editör onayından sonra pazar sabahı yayımlanır.</p></div>'
    else:
        ic = "".join(f'<article class="card"><div class="meta">{e(m.get("yazar",""))} · {e(m.get("tarih",""))}</div><h3><a href="{kok}makaleler/{e(m["slug"])}.html">{e(m["baslik"])}</a></h3><p>{e(m.get("spot",""))}</p></article>' for m in ler[:3])
    return (f'{etiket(*AD["etiket"])}<h2>Arşiv Dosyası</h2><p class="dk-giris">Özel haber · Haftalık (pazar). Kaynak: WikiLeaks arşivi.</p>{ic}'
            f'<p class="ozel-arsiv-link"><a href="{kok}arsiv-dosyasi-arsivi/index.html">📚 Arşiv Dosyası arşivi (tüm dosyalar)</a></p>')

# ---------------- Ana sayfa Kultur & Sanat ozeti ----------------
def kultur_ozet_html(base, kok=""):
    v = yukle(base, "ogrenci-kosesi"); g = yukle(base, "gise")
    yaz = ogrenci_yazilar(v, False)
    if yaz:
        y = yaz[0]
        ok = (f'<div class="meta">{e(y.get("ogrenci",""))} · {e(y.get("okul",""))} · {e(y.get("tarih",""))}</div>'
              f'<h4><a href="{kok}ogrenci-kosesi.html">{e(y.get("baslik",""))}</a></h4><p>{e(y.get("ozet",""))}</p>')
    else:
        ok = '<p class="ko-bos">İlk yazılar yakında. Sinema ve televizyon öğrencilerinin yazıları her çarşamba burada.</p>'
    tr = next((t for t in g.get("tablolar", []) if t.get("id") == "turkiye"), None)
    if tr and tr.get("satirlar"):
        li = "".join(f'<li><b>{r["sira"]}.</b> {e(r["film"])} <span class="meta">{_sayi(r.get("seyirci_hafta_sonu"))} seyirci · {_para(r.get("hafta_sonu"), tr.get("para"))}</span></li>' for r in tr["satirlar"][:3])
        gs = f'<div class="meta">Türkiye · {e(tr.get("donem",""))}</div><ol class="ko-gise">{li}</ol>'
    else:
        gs = '<p class="ko-bos">Gişe verisi alınamadı.</p>'
    return (f'<div class="kultur-ozet"><div class="ko-kutu">{etiket(*SAYFALAR["ogrenci-kosesi"]["etiket"])}{ok}<a class="makale-oku" href="{kok}ogrenci-kosesi.html">Öğrenci Köşesi →</a></div>'
            f'<div class="ko-kutu">{etiket(*SAYFALAR["gise"]["etiket"])}<h4>Gişede ilk 3</h4>{gs}<a class="makale-oku" href="{kok}gise.html">Gişe &amp; Yeni Çıkanlar →</a></div></div>')

# ---------------- uretim ----------------
def uret(base, makaleler=None):
    v = yukle(base, "ogrenci-kosesi"); s = SAYFALAR["ogrenci-kosesi"]
    open(os.path.join(base, "ogrenci-kosesi.html"), "w", encoding="utf-8").write(
        _bas(base, "", ogrenci_govde(base, v, ""), s["title"], s["desc"], f"{SITE}/ogrenci-kosesi", sinif="ozel-ogrenci"))
    s = SAYFALAR["gise"]
    open(os.path.join(base, "gise.html"), "w", encoding="utf-8").write(
        _bas(base, "", gise_govde(base, yukle(base, "gise"), yukle(base, "yeni-cikanlar"), ""), s["title"], s["desc"], f"{SITE}/gise", sinif="ozel-gise"))
    ler = arsiv_dosyalari(makaleler)
    open(os.path.join(base, AD_SLUG + ".html"), "w", encoding="utf-8").write(
        _bas(base, "", arsiv_dosyasi_govde(ler, ""), AD["title"], AD["desc"], f"{SITE}/{AD_SLUG}", sinif="ozel-ad"))
    os.makedirs(os.path.join(base, "arsiv-dosyasi-arsivi"), exist_ok=True)
    ic = (f'{etiket(*AD["etiket"])}<h2>Arşiv Dosyası · Arşiv</h2><p>{"Toplam " + str(len(ler)) + " dosya." if ler else "Henüz yayımlanmış dosya yok."} '
          f'<a href="../{AD_SLUG}.html">Arşiv Dosyası sayfasına dön</a></p><ul class="kose-liste">{_ad_liste(ler, "../")}</ul>')
    open(os.path.join(base, "arsiv-dosyasi-arsivi", "index.html"), "w", encoding="utf-8").write(
        _bas(base, "../", ic, "Arşiv Dosyası Arşivi", AD["desc"], f"{SITE}/arsiv-dosyasi-arsivi/", sinif="ozel-ad"))
    for slug in SAYFALAR:
        if not os.path.exists(os.path.join(base, slug, "arsiv", "index.html")): arsiv_index(base, slug)

def _icerik_var(slug, v):
    if slug == "ogrenci-kosesi": return bool(ogrenci_yazilar(v, False))
    if slug == "yeni-cikanlar": return bool(v.get("ogeler"))
    return any(t.get("satirlar") for t in v.get("tablolar", []))

def arsiv_index(base, slug):
    s = SAYFALAR[slug]
    kok_ark = os.path.join(base, slug, "arsiv"); os.makedirs(kok_ark, exist_ok=True)
    tum = sorted([d for d in os.listdir(kok_ark) if os.path.isdir(os.path.join(kok_ark, d))], reverse=True)
    satir = "".join(f'<li><a href="{d}/{slug}.html">{d[8:10]}.{d[5:7]}.{d[0:4]} haftası</a></li>' for d in tum)
    say = f"Toplam {len(tum)} kayıt." if tum else "Henüz arşivlenmiş kayıt yok."
    ic = (f'{etiket(*s["etiket"])}<h2>{e(s["ad"])} · Arşiv</h2><p>{say} Haftalık güncelleme günü: {GUNLER[s["gun"]]}. '
          f'<a href="../../{s["sayfa"]}.html">Güncel sayfaya dön</a></p><ul class="kose-liste">{satir}</ul>')
    open(os.path.join(kok_ark, "index.html"), "w", encoding="utf-8").write(
        _bas(base, "../../", ic, f'{s["ad"]} Arşivi', s["desc"], f"{SITE}/{slug}/arsiv/"))

def _arsiv_sayfasi(base, slug, v, tarih):
    s = SAYFALAR[slug]; kok = "../../../"
    if slug == "ogrenci-kosesi": g = ogrenci_govde(base, v, kok, arsiv_linki=False)
    elif slug == "gise": g = gise_govde(base, v, {}, kok, arsiv_linki=False, yalniz="gise")
    else: g = gise_govde(base, {}, v, kok, arsiv_linki=False, yalniz="yeni-cikanlar")
    geri = f'<p class="makale-geri"><a href="../index.html">← {e(s["ad"])} arşivi</a> · <a href="{kok}{s["sayfa"]}.html">Güncel sayfa</a></p>'
    t = f'{s["title"]} ({tarih[8:10]}.{tarih[5:7]}.{tarih[0:4]} arşivi)'
    return _bas(base, kok, geri + g, t, s["desc"], f"{SITE}/{slug}/arsiv/{tarih}/{slug}", noindex=True)

def arsivle(base, zorla=False, bugun=None):
    """JSON degistiyse ya da haftalik gunse (ve bugun arsivlenmediyse) <slug>/arsiv/<tarih>/ altina kopyalar. ORNEK kayitlar arsive girmez."""
    bugun = bugun or datetime.date.today(); tarih = bugun.strftime("%Y-%m-%d"); sonuc = []
    for slug, s in SAYFALAR.items():
        v = yukle(base, slug)
        if slug == "ogrenci-kosesi": v = dict(v, yazilar=ogrenci_yazilar(v, False))
        if not _icerik_var(slug, v): continue
        kok_ark = os.path.join(base, slug, "arsiv"); os.makedirs(kok_ark, exist_ok=True)
        onceki = sorted([d for d in os.listdir(kok_ark) if os.path.isdir(os.path.join(kok_ark, d))], reverse=True)
        yeni = json.dumps(v, sort_keys=True, ensure_ascii=False); son = ""
        if onceki:
            try: son = json.dumps(json.load(open(os.path.join(kok_ark, onceki[0], s["json"]), encoding="utf-8")), sort_keys=True, ensure_ascii=False)
            except Exception: son = ""
        if not (zorla or yeni != son or (bugun.weekday() == s["gun"] and tarih not in onceki)): continue
        hedef = os.path.join(kok_ark, tarih); os.makedirs(hedef, exist_ok=True)
        json.dump(v, open(os.path.join(hedef, s["json"]), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        open(os.path.join(hedef, slug + ".html"), "w", encoding="utf-8").write(_arsiv_sayfasi(base, slug, v, tarih))
        arsiv_index(base, slug); sonuc.append(f"{slug}/arsiv/{tarih}")
    return sonuc

ISARET = "<!--bolum-arsivleri-->"
def ana_arsiv_index_ekle(base):
    """arsiv/index.html'e bolum arsivlerinin linklerini ekler (sayilar listesine karismaz)."""
    p = os.path.join(base, "arsiv", "index.html")
    if not os.path.exists(p): return
    t = open(p, encoding="utf-8").read()
    if ISARET in t: return
    blok = (f'{ISARET}<section class="bolum-arsivleri"><h2>Bölüm arşivleri</h2><ul class="ba-liste">'
            f'<li>{etiket(*SAYFALAR["ogrenci-kosesi"]["etiket"])} <a href="../ogrenci-kosesi/arsiv/index.html">Sinema-TV Öğrenci Köşesi arşivi</a></li>'
            f'<li>{etiket(*SAYFALAR["gise"]["etiket"])} <a href="../gise/arsiv/index.html">Gişe arşivi (hafta hafta)</a></li>'
            f'<li>{etiket(*SAYFALAR["yeni-cikanlar"]["etiket"])} <a href="../yeni-cikanlar/arsiv/index.html">Yeni Çıkanlar arşivi</a></li>'
            f'<li>{etiket(*AD["etiket"])} <a href="../arsiv-dosyasi-arsivi/index.html">Arşiv Dosyası arşivi</a></li></ul></section><h2 class="sayi-baslik">Gazete sayıları</h2>')
    t = t.replace("<ul>", blok + "<ul>", 1)
    open(p, "w", encoding="utf-8").write(t)

if __name__ == "__main__":
    b = os.path.dirname(os.path.abspath(__file__))
    if len(sys.argv) > 1 and sys.argv[1] == "arsivle": print(arsivle(b, zorla="--zorla" in sys.argv))
    else: uret(b); print("ozel sayfalar uretildi (Arşiv Dosyası listesi için build.py çalıştırın)")
