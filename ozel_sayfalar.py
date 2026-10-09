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
def _s(x):
    """None/sayi/her sey -> guvenli str (None -> "")."""
    return "" if x is None else str(x)
def es(x):
    """html.escape(None) cokmesin: None -> ''."""
    return html.escape(_s(x))
def al(d, k, vars=""):
    """Sozlukten guvenli okuma: d sozluk degilse ya da deger None ise varsayilan."""
    v = d.get(k) if isinstance(d, dict) else None
    return vars if v is None else v
URL_RE = re.compile(r"https?://(?:(?!&quot;|&#x27;|&lt;|&gt;)[^\s<>\"'])+")
def linkle(metin):
    """Once escape, sonra http(s) adreslerini guvenli <a> yap (target=_blank rel=noopener)."""
    def f(m):
        u = m.group(0); son = ""
        while u and u[-1] in ".,;:!?)]»”’": son = u[-1] + son; u = u[:-1]
        return f'<a href="{u}" target="_blank" rel="noopener">{u}</a>{son}'
    return URL_RE.sub(f, es(metin))
def slugify(x):
    x = re.sub(r"\s*\(.*?\)\s*", " ", _s(x)).strip()
    x = x.translate(str.maketrans("çğıöşüÇĞİÖŞÜâîûÂÎÛ", "cgiosuCGIOSUaiuAIU")).lower()
    return re.sub(r"[^a-z0-9]+", "-", x).strip("-")
SITE = "https://diojennews.com"
GUNLER = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"]
# Haftalik arsivlenen birimler. gun: 0=pazartesi
SAYFALAR = {
    "ogrenci-kosesi": {"ad": "Sinema-TV Öğrenci Köşesi", "json": "ogrenci-kosesi.json", "gun": 2, "sayfa": "ogrenci-kosesi",
        "title": "Sinema-TV Öğrenci Köşesi", "etiket": ("e-ogrenci", "ÖĞRENCİ KÖŞESİ"),
        "desc": "Sinema ve televizyon öğrencileri için haftalık, öğretici köşe: festival ve burs başvuru takvimleri, film çözümlemeleri, sektöre giriş notları ve ücretsiz kaynaklar."},
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

def etiket(sinif, metin): return f'<span class="etiket {sinif}">{es(metin)}</span>'

# ---------------- menu ----------------
def kultur_menu(kok="", kultur_href=None):
    kh = kultur_href if kultur_href is not None else f"{kok}DiojenNews.html#kultur"
    return (f'<details class="nav-acilir"><summary>Kültür &amp; Sanat</summary><div class="alt-menu">'
            f'<a href="{kh}">Kültür &amp; Sanat haberleri</a>'
            f'<a href="{kok}ogrenci-kosesi.html">Sinema-TV Öğrenci Köşesi</a>'
            f'<a href="{kok}gise.html">Gişe &amp; Yeni Çıkanlar</a></div></details>')
MOBIL_DUGME = '<input type="checkbox" id="menu-ac" class="menu-ac" aria-label="Menüyü aç"><label for="menu-ac" class="menu-dugme">☰ Menü</label>'
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
<title>{es(title)} - Diojen News</title>
<meta name="description" content="{es(desc)}">
<link rel="canonical" href="{canon}">{robots}
<meta property="og:type" content="website">
<meta property="og:site_name" content="Diojen News">
<meta property="og:locale" content="tr_TR">
<meta property="og:title" content="{es(title)}">
<meta property="og:description" content="{es(desc)}">
<meta property="og:url" content="{canon}">
<meta name="twitter:card" content="summary">
<meta name="twitter:title" content="{es(title)}">
<meta name="twitter:description" content="{es(desc)}">
<link rel="stylesheet" href="{kok}styles.css">
</head>
<body>
<div class="container">
<header class="header"><h1>Diojen <span>News</span></h1><div class="logo">D</div></header>
{MOBIL_DUGME}<nav class="navbar">{nav}</nav>
<div class="kose-sayfa ozel-sayfa {sinif}"><section class="bolum">{govde}</section></div>
<footer class="footer"><p>&copy; {datetime.date.today().year} Diojen News. Tüm hakları saklıdır.</p></footer>
</div>
</body>
</html>'''

def _tarih_anahtar(t):
    m = re.search(r"(\d{2})\.(\d{2})\.(\d{4})", t or "")
    return (m.group(3), m.group(2), m.group(1)) if m else ("0000", "00", "00")

def _ark_link(kok, slug, metin): return f'<a href="{kok}{slug}/arsiv/index.html">📚 {es(metin)}</a>'

# ---------------- Ogrenci Kosesi ----------------
def ogrenci_yazilar(v, ornek_dahil=True):
    y = [x for x in al(v, "yazilar", []) if isinstance(x, dict) and (ornek_dahil or not x.get("ornek"))]
    return sorted(y, key=lambda x: _tarih_anahtar(x.get("tarih")), reverse=True)

def _metin_html(metin):
    out = []
    for p in _s(metin).split("\n"):
        p = p.strip()
        if not p: continue
        if re.match(r"^\d{1,2}\.\s+\S", p) and len(p) < 220: out.append(f'<h4 class="ok-ara">{linkle(p)}</h4>')
        else: out.append(f"<p>{linkle(p)}</p>")
    return "".join(out)

def ogrenci_govde(base, v, kok, arsiv_linki=True):
    yaz = ogrenci_yazilar(v)
    kart = []
    for y in yaz:
        yazar = al(y, "yazar")
        konuk = " · ".join(x for x in (es(al(y, "ogrenci")), es(al(y, "okul"))) if x)
        meta = " · ".join(x for x in (f'Yazar: <b class="ok-yazar">{es(yazar)}</b>' if yazar else "", konuk, es(al(y, "tarih"))) if x)
        img = ""
        gs = _s(al(y, "gorsel"))
        if gs:
            src = gs if re.match(r"^https?://", gs) else kok + gs
            img = f'<img class="ok-gorsel" src="{es(src)}" alt="{es(al(y, "baslik"))}" loading="lazy">'
        link = f'<a class="makale-oku" href="{es(al(y, "link"))}" target="_blank" rel="noopener">Yazının tamamı →</a>' if al(y, "link") else ""
        et = '<span class="ornek-etiket">ÖRNEK</span> ' if al(y, "ornek") else ""
        kart.append(f'<article class="card ok-kart{" ornek" if al(y, "ornek") else ""}">{img}<div class="meta">{et}{meta}</div><h3>{es(al(y, "baslik"))}</h3>'
                    f'<p class="ok-ozet">{es(al(y, "ozet"))}</p><div class="ok-metin">{_metin_html(al(y, "metin"))}</div>{link}</article>')
    if not ogrenci_yazilar(v, False):
        kart.insert(0, '<div class="bos-durum"><p class="bos-baslik">İlk yazı yakında</p><p>Sinema ve televizyon okuyan ya da okumaya hazırlananlar için haftalık, öğretici bir köşe: başvuru takvimleri, film çözümlemeleri, sektöre giriş notları ve ücretsiz kaynaklar.</p></div>')
    ark = f'<p class="ozel-arsiv-link">{_ark_link(kok, "ogrenci-kosesi", "Öğrenci Köşesi arşivi")}</p>' if arsiv_linki else ""
    return (f'{etiket(*SAYFALAR["ogrenci-kosesi"]["etiket"])}<h2>Sinema-TV Öğrenci Köşesi</h2>'
            f'<p class="dk-giris">Kültür &amp; Sanat · Her çarşamba. Sinema ve televizyon öğrencileri için haftalık, öğretici bir köşe: başvuru takvimleri, film çözümlemeleri, sektöre giriş notları.</p>{"".join(kart)}{ark}')

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
# Eski alan adlari (geriye uyum): hafta_sonu -> hasilat_hafta_sonu, toplam -> hasilat_toplam
ESKI = {"hafta_sonu": "hasilat_hafta_sonu", "toplam": "hasilat_toplam"}
def _satir(r):
    r = dict(r) if isinstance(r, dict) else {}
    for a, b in ESKI.items():
        if a in r and b not in r: r[b] = r.pop(a)
    return r
KOLONLAR = [("sira", "Sıra"), ("film", "Film"), ("hafta", "Hafta"), ("seyirci_hafta", "Haftalık seyirci"), ("hasilat_hafta", "Haftalık hasılat"),
            ("seyirci_hafta_sonu", "Hafta sonu seyirci"), ("hasilat_hafta_sonu", "Hafta sonu hasılatı"), ("seyirci_toplam", "Toplam seyirci"), ("hasilat_toplam", "Toplam hasılat"), ("yorum", "Not")]

def gise_tablolari(v, yc=None):
    """yc: yeni-cikanlar verisi; varsa film adi ayni sayfadaki #yc-<slug> ozetine baglanir."""
    yc_sluglar = {_s(al(o, "slug")) or slugify(al(o, "baslik")) for o in (al(yc, "ogeler", []) if yc else [])}
    bl = []
    for t in al(v, "tablolar", []):
        p = al(t, "para"); sat = [_satir(r) for r in (al(t, "satirlar", []) or [])]
        kay = f'<a href="{es(al(t, "kaynak_url"))}" target="_blank" rel="noopener">{es(al(t, "kaynak"))}</a>' if al(t, "kaynak_url") else es(al(t, "kaynak"))
        ust = f'<div class="meta">Dönem: {es(al(t, "donem", "—"))} · Kaynak: {kay}</div>'
        if not sat:
            bl.append(f'<article class="gise-tablo"><h3>{es(al(t, "baslik"))}</h3>{ust}<p class="bos">Veri alınamadı.</p></article>'); continue
        kol = [(k, a) for k, a in KOLONLAR if any(r.get(k) not in (None, "") for r in sat)]
        def hucre(k, r):
            x = r.get(k)
            if k.startswith("hasilat"): return f'<td class="sayi">{_para(x, p)}</td>'
            if k.startswith("seyirci"): return f'<td class="sayi">{_sayi(x)}</td>'
            if k == "film":
                hedef = _s(r.get("yeni_cikanlar_id")) or slugify(x)
                if hedef in yc_sluglar: return f'<td class="film"><a href="#yc-{es(hedef)}" title="Yeni Çıkanlar özeti">{es(x)}</a> <span class="yc-isaret">yeni</span></td>'
                return f'<td class="film">{es(x)}</td>'
            if k == "yorum": return f'<td class="yorum">{es(x)}</td>'
            return f'<td class="sayi">{es(x) if x not in (None, "") else "—"}</td>'
        th = "".join(f"<th>{a}</th>" for _, a in kol)
        tr = "".join("<tr>" + "".join(hucre(k, r) for k, _ in kol) + "</tr>" for r in sat)
        notu = f'<p class="gise-not">{es(al(t, "not"))}</p>' if al(t, "not") else ""
        bl.append(f'<article class="gise-tablo" id="tablo-{es(al(t, "id"))}"><h3>{es(al(t, "baslik"))}</h3>{ust}<div class="tablo-kap"><table><thead><tr>{th}</tr></thead><tbody>{tr}</tbody></table></div>{notu}</article>')
    return "".join(bl) or '<p class="bos">Veri alınamadı.</p>'

def yeni_kartlar(v):
    og = [o for o in al(v, "ogeler", []) if isinstance(o, dict)]
    if not og: return '<p class="bos">Bu hafta için veri alınamadı.</p>'
    grup = []
    for tur, ad in (("film", "Sinemada"), ("dizi", "Dizi ve dijital platformlar")):
        k = []
        for o in [x for x in og if x.get("tur_ad") == tur]:
            kay = f'<a class="kaynak" href="{es(o["kaynak_url"])}" target="_blank" rel="noopener">Kaynak: {es(o.get("kaynak",""))}</a>' if o.get("kaynak_url") else ""
            sl = _s(al(o, "slug")) or slugify(al(o, "baslik"))
            k.append(f'<article class="yc-kart" id="yc-{es(sl)}"><div class="yc-ust"><span class="yc-tur">{"🎬 Film" if tur=="film" else "📺 Dizi"}</span> <span class="yc-platform">{es(o.get("platform",""))}</span></div>'
                     f'<h4>{es(o.get("baslik",""))}</h4><div class="meta">{es(o.get("tur",""))} · {es(o.get("tarih",""))}</div><p>{es(o.get("ozet",""))}</p>{kay}</article>')
        if k: grup.append(f'<h3 class="yc-grup">{ad}</h3><div class="yc-izgara">{"".join(k)}</div>')
    return "".join(grup)

def gise_govde(base, v, yc, kok, arsiv_linki=True, yalniz=None):
    """yalniz: None=tam sayfa, 'gise' ya da 'yeni-cikanlar' (arsiv kopyalari icin)"""
    parca = []
    if yalniz in (None, "gise"):
        gun = f' Son güncelleme: {es(v["guncelleme"])}.' if v.get("guncelleme") else ""
        parca.append(f'{etiket(*SAYFALAR["gise"]["etiket"])}<h2>Gişe Hasılatları</h2><p class="dk-giris">Türkiye ve dünya gişesi, haftalık (salı).{gun} Tablolar mobilde yana kaydırılabilir.</p>{gise_tablolari(v, yc)}')
    if yalniz in (None, "yeni-cikanlar"):
        don = f' {es(yc["donem"])}.' if yc.get("donem") else ""
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
    href = "#" if ornek else f'{kok}makaleler/{es(m["slug"])}.html'
    by = " · ".join(x for x in (f'Yazar: {es(m.get("yazar",""))}' if m.get("yazar") else "", es(m.get("tarih", ""))) if x)
    return (f'<section class="ozel-haber{" ornek" if ornek else ""}" id="ozel-haber"><div class="oh-ust">{et}{etiket("e-ozel", "ÖZEL HABER")} {etiket(*AD["etiket"])}</div>'
            f'<h2><a href="{href}">{es(m.get("baslik",""))}</a></h2><div class="meta">{by}</div><p>{es(m.get("spot",""))}</p>'
            f'<a class="makale-oku" href="{href}">Dosyayı oku →</a> · <a class="makale-oku" href="{kok}{AD_SLUG}.html">Tüm Arşiv Dosyaları</a></section>')

def _ad_liste(ler, kok):
    return "".join(f'<li><a href="{kok}makaleler/{es(m["slug"])}.html">{es(m["baslik"])}</a> <span class="meta">{es(m.get("tarih",""))}</span></li>' for m in ler)

def arsiv_dosyasi_govde(ler, kok):
    if not ler:
        ic = '<div class="bos-durum"><p class="bos-baslik">İlk dosya yakında</p><p>Arşiv Dosyası, WikiLeaks arşivindeki belgelerden yola çıkan haftalık özel haber dizisidir. Her dosya editör onayından sonra pazar sabahı yayımlanır.</p></div>'
    else:
        ic = "".join(f'<article class="card"><div class="meta">{es(m.get("yazar",""))} · {es(m.get("tarih",""))}</div><h3><a href="{kok}makaleler/{es(m["slug"])}.html">{es(m["baslik"])}</a></h3><p>{es(m.get("spot",""))}</p></article>' for m in ler[:3])
    return (f'{etiket(*AD["etiket"])}<h2>Arşiv Dosyası</h2><p class="dk-giris">Özel haber · Haftalık (pazar). Kaynak: WikiLeaks arşivi.</p>{ic}'
            f'<p class="ozel-arsiv-link"><a href="{kok}arsiv-dosyasi-arsivi/index.html">📚 Arşiv Dosyası arşivi (tüm dosyalar)</a></p>')

# ---------------- Ana sayfa Kultur & Sanat ozeti ----------------
def kultur_ozet_html(base, kok=""):
    v = yukle(base, "ogrenci-kosesi"); g = yukle(base, "gise")
    yaz = ogrenci_yazilar(v, False)
    if yaz:
        y = yaz[0]
        ok = (f'<div class="meta">Yazar: {es(al(y, "yazar"))} · {es(al(y, "tarih"))}</div>'
              f'<h4><a href="{kok}ogrenci-kosesi.html">{es(al(y, "baslik"))}</a></h4><p>{es(al(y, "ozet"))}</p>')
    else:
        ok = '<p class="ko-bos">İlk yazı yakında. Sinema ve televizyon öğrencileri için haftalık köşe her çarşamba burada.</p>'
    tr = next((t for t in g.get("tablolar", []) if t.get("id") == "turkiye"), None)
    if tr and tr.get("satirlar"):
        def _oz(r):
            r = _satir(r)
            if r.get("seyirci_hafta") not in (None, ""): return f'{_sayi(r.get("seyirci_hafta"))} seyirci · {_para(r.get("hasilat_hafta"), al(tr, "para"))} (hafta)'
            return f'{_sayi(r.get("seyirci_hafta_sonu"))} seyirci · {_para(r.get("hasilat_hafta_sonu"), al(tr, "para"))} (hafta sonu)'
        li = "".join(f'<li><b>{es(al(r, "sira"))}.</b> {es(al(r, "film"))} <span class="meta">{_oz(r)}</span></li>' for r in tr["satirlar"][:3])
        gs = f'<div class="meta">Türkiye · {es(tr.get("donem",""))}</div><ol class="ko-gise">{li}</ol>'
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
    ic = (f'{etiket(*s["etiket"])}<h2>{es(s["ad"])} · Arşiv</h2><p>{say} Haftalık güncelleme günü: {GUNLER[s["gun"]]}. '
          f'<a href="../../{s["sayfa"]}.html">Güncel sayfaya dön</a></p><ul class="kose-liste">{satir}</ul>')
    open(os.path.join(kok_ark, "index.html"), "w", encoding="utf-8").write(
        _bas(base, "../../", ic, f'{s["ad"]} Arşivi', s["desc"], f"{SITE}/{slug}/arsiv/"))

def _arsiv_sayfasi(base, slug, v, tarih):
    s = SAYFALAR[slug]; kok = "../../../"
    if slug == "ogrenci-kosesi": g = ogrenci_govde(base, v, kok, arsiv_linki=False)
    elif slug == "gise": g = gise_govde(base, v, {}, kok, arsiv_linki=False, yalniz="gise")
    else: g = gise_govde(base, {}, v, kok, arsiv_linki=False, yalniz="yeni-cikanlar")
    geri = f'<p class="makale-geri"><a href="../index.html">← {es(s["ad"])} arşivi</a> · <a href="{kok}{s["sayfa"]}.html">Güncel sayfa</a></p>'
    t = f'{s["title"]} ({tarih[8:10]}.{tarih[5:7]}.{tarih[0:4]} arşivi)'
    return _bas(base, kok, geri + g, t, s["desc"], f"{SITE}/{slug}/arsiv/{tarih}/{slug}", noindex=True)

def arsivle(base, zorla=False, bugun=None, sadece=None):
    """JSON degistiyse ya da haftalik gunse (ve bugun arsivlenmediyse) <slug>/arsiv/<tarih>/ altina kopyalar. ORNEK kayitlar arsive girmez."""
    bugun = bugun or datetime.date.today(); tarih = bugun.strftime("%Y-%m-%d"); sonuc = []
    for slug, s in SAYFALAR.items():
        if sadece and slug not in sadece: continue
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
