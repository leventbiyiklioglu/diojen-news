#!/usr/bin/env python3
"""Diojen News ozel sayfalari: Sinema ve TV Ogrencileri Kosesi + Gise Hasilatlari.
build.py:  uret(base)  -> ogrenci-kosesi.html, gise.html
yayin.py:  arsivle(base) -> ogrenci-kosesi/arsiv/<YYYY-MM-DD>/ ve gise/arsiv/<YYYY-MM-DD>/ (ana arsiv/ ile karismaz)
Elle: python3 ozel_sayfalar.py arsivle [--zorla]
"""
import os, json, html, shutil, datetime, hashlib, sys, re
e = html.escape
SITE = "https://diojennews.com"
# slug, menu adi, json, haftalik gun (0=pazartesi), title, description
SAYFALAR = {
    "ogrenci-kosesi": {"ad": "Öğrenci Köşesi", "json": "ogrenci-kosesi.json", "gun": 2,
        "title": "Sinema ve Televizyon Öğrencileri Köşesi",
        "desc": "Sinema ve televizyon bölümü öğrencilerinin yazıları, film eleştirileri ve kısa film notları. Diojen News Kültür & Sanat bölümünde her hafta."},
    "gise": {"ad": "Gişe Hasılatları", "json": "gise.json", "gun": 1,
        "title": "Gişe Hasılatları: Türkiye ve Dünya",
        "desc": "Türkiye ve dünya sinema gişesinde haftanın tabloları: sıra, film, hafta sonu ve toplam hasılat, seyirci sayıları. Her hafta güncellenir."},
}
GUNLER = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"]

def nav_linkleri(kok=""):
    """Diger sayfalarin menusune eklenecek iki link."""
    return "".join(f'<a href="{kok}{s}.html">{e(v["ad"])}</a>' for s, v in SAYFALAR.items())

def yukle(base, slug):
    try: return json.load(open(os.path.join(base, "haberler", SAYFALAR[slug]["json"]), encoding="utf-8"))
    except Exception: return {}

def _bas(base, slug, kok, govde, arsiv_tarih=None):
    s = SAYFALAR[slug]
    canon = f"{SITE}/{slug}" + (f"/arsiv/{arsiv_tarih}/{slug}" if arsiv_tarih else "")
    dk = f'<a href="{kok}dedekorkut.html">Dede Korkut Günlüğü</a>' if os.path.exists(os.path.join(base, "dedekorkut.html")) else ""
    nav = (f'<a href="{kok}DiojenNews.html">Ana Sayfa</a><a href="{kok}DiojenNews.html#kultur">Kültür &amp; Sanat</a><a href="{kok}kose.html">Köşe Yazıları</a>{dk}'
           + nav_linkleri(kok) + f'<a href="{kok}arsiv/index.html" class="arsiv-link">📚 Arşiv</a>')
    baslik = s["title"] + (f" ({arsiv_tarih} arşivi)" if arsiv_tarih else "")
    robots = '<meta name="robots" content="noindex, follow">' if arsiv_tarih else ""
    return f'''<!DOCTYPE html>
<html lang="tr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{e(baslik)} - Diojen News</title>
<meta name="description" content="{e(s["desc"])}">
<link rel="canonical" href="{canon}">{robots}
<meta property="og:type" content="website">
<meta property="og:site_name" content="Diojen News">
<meta property="og:locale" content="tr_TR">
<meta property="og:title" content="{e(baslik)}">
<meta property="og:description" content="{e(s["desc"])}">
<meta property="og:url" content="{canon}">
<meta name="twitter:card" content="summary">
<meta name="twitter:title" content="{e(baslik)}">
<meta name="twitter:description" content="{e(s["desc"])}">
<link rel="stylesheet" href="{kok}styles.css">
</head>
<body>
<div class="container">
<header class="header"><h1>Diojen <span>News</span></h1><div class="logo">D</div></header>
<nav class="navbar">{nav}</nav>
<div class="kose-sayfa ozel-sayfa ozel-{slug}"><section class="bolum">{govde}</section></div>
<footer class="footer"><p>&copy; {datetime.date.today().year} Diojen News. Tüm hakları saklıdır.</p></footer>
</div>
</body>
</html>'''

def _tarih_anahtar(t):
    m = re.search(r"(\d{2})\.(\d{2})\.(\d{4})", t or "")
    return (m.group(3), m.group(2), m.group(1)) if m else ("0000", "00", "00")

def ogrenci_govde(base, v, kok, arsiv_linki=True):
    yaz = sorted(v.get("yazilar", []), key=lambda y: _tarih_anahtar(y.get("tarih")), reverse=True)
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
        etiket = '<span class="ornek-etiket">ÖRNEK</span> ' if y.get("ornek") else ""
        kart.append(f'<article class="card ok-kart{" ornek" if y.get("ornek") else ""}">{img}<div class="meta">{etiket}{meta}</div><h3>{e(y.get("baslik",""))}</h3>'
                    f'<p class="ok-ozet">{e(y.get("ozet",""))}</p>{metin}{link}</article>')
    if not [y for y in yaz if not y.get("ornek")]:
        kart.insert(0, '<div class="bos-durum"><p class="bos-baslik">İlk yazılar yakında</p><p>Sinema ve televizyon bölümü öğrencilerinin film eleştirileri, kısa film notları ve set günlükleri bu köşede her hafta yayımlanacak.</p></div>')
    ark = f'<p class="ozel-arsiv-link"><a href="{kok}ogrenci-kosesi/arsiv/index.html">📚 Öğrenci Köşesi arşivi</a></p>' if arsiv_linki else ""
    yazar = f'<span class="yazar">Editör: {e(v["yazar"])}</span>' if v.get("yazar") else ""
    return (f'<h2>Sinema ve Televizyon Öğrencileri Köşesi {yazar}</h2>'
            f'<p class="dk-giris">Kültür &amp; Sanat · Haftalık köşe. Sinema ve televizyon öğrencilerinin kaleminden.</p>{"".join(kart)}{ark}')

def _para(n, para):
    if n is None or n == "": return "—"
    s = f"{int(n):,}"
    return ("₺" if para == "TRY" else "$") + s.replace(",", ".")

def _sayi(n, para):
    if n is None or n == "": return "—"
    s = f"{int(n):,}"
    return s.replace(",", ".")

def gise_govde(base, v, kok, arsiv_linki=True):
    bl = []
    for t in v.get("tablolar", []):
        p = t.get("para", "")
        sat = t.get("satirlar") or []
        kay = f'<a href="{e(t["kaynak_url"])}" target="_blank" rel="noopener">{e(t.get("kaynak",""))}</a>' if t.get("kaynak_url") else e(t.get("kaynak", ""))
        ust = f'<div class="meta">Dönem: {e(t.get("donem","—"))} · Kaynak: {kay}</div>'
        if not sat:
            bl.append(f'<article class="gise-tablo"><h3>{e(t.get("baslik",""))}</h3>{ust}<p class="bos">Veri alınamadı.</p></article>'); continue
        kol = [("sira", "Sıra"), ("film", "Film"), ("hafta_sonu", "Hafta sonu hasılatı"), ("toplam", "Toplam hasılat"), ("hafta", "Hafta"), ("seyirci_hafta_sonu", "Hafta sonu seyirci"), ("seyirci_toplam", "Toplam seyirci")]
        kol = [(k, a) for k, a in kol if any(r.get(k) not in (None, "") for r in sat)]
        def hucre(k, r):
            x = r.get(k)
            if k in ("hafta_sonu", "toplam"): return f'<td class="sayi">{_para(x, p)}</td>'
            if k.startswith("seyirci"): return f'<td class="sayi">{_sayi(x, p)}</td>'
            if k == "film": return f'<td class="film">{e(str(x or ""))}</td>'
            return f'<td class="sayi">{e(str(x if x is not None else "—"))}</td>'
        th = "".join(f"<th>{a}</th>" for _, a in kol)
        tr = "".join("<tr>" + "".join(hucre(k, r) for k, _ in kol) + "</tr>" for r in sat)
        notu = f'<p class="gise-not">{e(t["not"])}</p>' if t.get("not") else ""
        bl.append(f'<article class="gise-tablo"><h3>{e(t.get("baslik",""))}</h3>{ust}<div class="tablo-kap"><table><thead><tr>{th}</tr></thead><tbody>{tr}</tbody></table></div>{notu}</article>')
    if not bl: bl = ['<p class="bos">Veri alınamadı.</p>']
    ark = f'<p class="ozel-arsiv-link"><a href="{kok}gise/arsiv/index.html">📚 Gişe arşivi (önceki haftalar)</a></p>' if arsiv_linki else ""
    gun = f' Son güncelleme: {e(v["guncelleme"])}.' if v.get("guncelleme") else ""
    return f'<h2>Gişe Hasılatları</h2><p class="dk-giris">Türkiye ve dünya gişesi, haftalık.{gun}</p>{"".join(bl)}{ark}'

GOVDE = {"ogrenci-kosesi": ogrenci_govde, "gise": gise_govde}

def uret(base):
    for slug in SAYFALAR:
        v = yukle(base, slug)
        open(os.path.join(base, slug + ".html"), "w", encoding="utf-8").write(_bas(base, slug, "", GOVDE[slug](base, v, "")))
        if not os.path.exists(os.path.join(base, slug, "arsiv", "index.html")): arsiv_index(base, slug)

def _icerik_var(slug, v):
    return bool(v.get("yazilar")) if slug == "ogrenci-kosesi" else any(t.get("satirlar") for t in v.get("tablolar", []))

def arsiv_index(base, slug):
    s = SAYFALAR[slug]
    kok_ark = os.path.join(base, slug, "arsiv"); os.makedirs(kok_ark, exist_ok=True)
    tum = sorted([d for d in os.listdir(kok_ark) if os.path.isdir(os.path.join(kok_ark, d))], reverse=True)
    satir = "".join(f'<li><a href="{d}/{slug}.html">{d[8:10]}.{d[5:7]}.{d[0:4]}</a></li>' for d in tum)
    say = f"Toplam {len(tum)} kayıt." if tum else "Henüz arşivlenmiş kayıt yok."
    ic = (f'<h2>{e(s["title"])} · Arşiv</h2><p>{say} Haftalık güncelleme günü: {GUNLER[s["gun"]]}. '
          f'<a href="../../{slug}.html">Güncel sayfaya dön</a></p><ul class="kose-liste">{satir}</ul>')
    open(os.path.join(kok_ark, "index.html"), "w", encoding="utf-8").write(
        _bas(base, slug, "../../", ic, arsiv_tarih=None).replace(f'href="{SITE}/{slug}"', f'href="{SITE}/{slug}/arsiv/"').replace('<meta property="og:url" content="' + SITE + "/" + slug + '">', '<meta property="og:url" content="' + SITE + "/" + slug + '/arsiv/">'))

def arsivle(base, zorla=False, bugun=None):
    """JSON degistiyse ya da haftalik gunse (ve bugun arsivlenmediyse) <slug>/arsiv/<tarih>/ altina kopyalar."""
    bugun = bugun or datetime.date.today()
    tarih = bugun.strftime("%Y-%m-%d")
    sonuc = []
    for slug, s in SAYFALAR.items():
        jp = os.path.join(base, "haberler", s["json"])
        if not os.path.exists(jp): continue
        v = yukle(base, slug)
        if not _icerik_var(slug, v): continue
        # ORNEK kartlar arsive girmez
        if slug == "ogrenci-kosesi": v = dict(v, yazilar=[y for y in v.get("yazilar", []) if not y.get("ornek")])
        if not _icerik_var(slug, v): continue
        kok_ark = os.path.join(base, slug, "arsiv")
        os.makedirs(kok_ark, exist_ok=True)
        onceki = sorted([d for d in os.listdir(kok_ark) if os.path.isdir(os.path.join(kok_ark, d))], reverse=True)
        yeni = json.dumps(v, sort_keys=True, ensure_ascii=False)
        son = ""
        if onceki:
            try: son = json.dumps(json.load(open(os.path.join(kok_ark, onceki[0], s["json"]), encoding="utf-8")), sort_keys=True, ensure_ascii=False)
            except Exception: son = ""
        degisti = yeni != son
        haftalik = bugun.weekday() == s["gun"] and tarih not in onceki
        if not (zorla or degisti or haftalik): continue
        hedef = os.path.join(kok_ark, tarih); os.makedirs(hedef, exist_ok=True)
        json.dump(v, open(os.path.join(hedef, s["json"]), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        kok = "../../../"
        open(os.path.join(hedef, slug + ".html"), "w", encoding="utf-8").write(_bas(base, slug, kok, GOVDE[slug](base, v, kok, arsiv_linki=False)
            .replace("<h2>", f'<p class="makale-geri"><a href="../index.html">← {e(s["ad"])} arşivi</a> · <a href="{kok}{slug}.html">Güncel sayfa</a></p><h2>', 1), arsiv_tarih=tarih))
        arsiv_index(base, slug)
        sonuc.append(f"{slug}/arsiv/{tarih}")
    return sonuc

if __name__ == "__main__":
    b = os.path.dirname(os.path.abspath(__file__))
    if len(sys.argv) > 1 and sys.argv[1] == "arsivle": print(arsivle(b, zorla="--zorla" in sys.argv))
    else: uret(b); print("ozel sayfalar uretildi")
