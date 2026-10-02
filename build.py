#!/usr/bin/env python3
"""Diojen News: haberler/*.json dosyalarindan DiojenNews.html uretir."""
import re, json, html, os, glob, datetime
KAT = [("dunya","Dünya"),("ekonomi","Ekonomi"),("spor","Spor"),("teknoloji","Teknoloji"),("kultur","Kültür & Sanat")]
base = os.path.dirname(os.path.abspath(__file__))
def yukle(slug):
    p = os.path.join(base,"haberler",slug+".json")
    if not os.path.exists(p): return {"yazar":"","haberler":[]}
    try: return json.load(open(p,encoding="utf-8"))
    except Exception: return {"yazar":"","haberler":[]}
e = html.escape
kose_dosyalar = sorted(glob.glob(os.path.join(base,"koseyazilari","*.md")), reverse=True)
KAT_NAV = KAT + ([("kose","Köşe Yazıları")] if kose_dosyalar else [])
nav = '<a href="#ust">Ana Sayfa</a>' + "".join(f'<a href="{"kose.html" if s=="kose" else "#"+s}">{e(a)}</a>' for s,a in KAT_NAV) + '<a href="arsiv/index.html" class="arsiv-link">📚 Arşiv</a>'
yan = "".join(f'<li><a href="{"kose.html" if s=="kose" else "#"+s}">{e(a)}</a></li>' for s,a in KAT_NAV) + '<li><a href="arsiv/index.html">📚 Arşiv (eski sayılar)</a></li>'
bol = []
manset = []
for s,ad in KAT:
    d = yukle(s); hab = d.get("haberler",[])[:6]
    kart = []
    for i,h in enumerate(hab):
        kaynak = ""
        if h.get("kaynak"):
            kaynak = f'<span class="kaynak">Kaynak: {e(h["kaynak"])}</span>'
            if h.get("kaynak_url"): kaynak = f'<a class="kaynak" href="{e(h["kaynak_url"])}" target="_blank" rel="noopener">Kaynak: {e(h["kaynak"])}</a>'
        kart.append(f'<article class="card"><div class="meta">{e(h.get("tarih",""))}</div><h3>{e(h.get("baslik",""))}</h3><p>{e(h.get("ozet",""))}</p>{kaynak}</article>')
        if i==0: manset.append((ad,h))
    if not kart: kart = ['<p class="bos">Bu bölümün yazarı henüz haber girmedi.</p>']
    yaz = f'<span class="yazar">Yazar: {e(d["yazar"])}</span>' if d.get("yazar") else ""
    bol.append(f'<section class="bolum" id="{s}"><h2>{e(ad)} {yaz}</h2>{"".join(kart)}</section>')
kose_html = ""
def kose_oku(p):
    try: satirlar = [l.strip() for l in open(p,encoding="utf-8").read().split("\n") if l.strip()]
    except Exception: return None
    if not satirlar: return None
    meta = satirlar[1].replace("**","") if len(satirlar)>1 else ""
    m = re.search(r"(\d{2})\.(\d{2})\.(\d{4})", meta)
    tarih = f"{m.group(3)}-{m.group(2)}-{m.group(1)}" if m else "0000-00-00"
    return {"slug":os.path.splitext(os.path.basename(p))[0], "baslik":satirlar[0].lstrip("# ").strip(), "meta":meta, "tarih":tarih,
            "govde":"".join(f'<p>{e(l.replace("**",""))}</p>' for l in satirlar[2:])}
yazilar = [y for y in (kose_oku(p) for p in kose_dosyalar) if y]
yazilar.sort(key=lambda y:(y["tarih"], os.path.getmtime(os.path.join(base,"koseyazilari",y["slug"]+".md"))), reverse=True)
if yazilar:
    guncel_tarih = yazilar[0]["tarih"]
    guncel = [y for y in yazilar if y["tarih"]==guncel_tarih]
    eski = [y for y in yazilar if y["tarih"]!=guncel_tarih]
    def sayfa_kose(baslik, icerik, kok):
        return f'''<!DOCTYPE html><html lang="tr"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>{e(baslik)} - Diojen News</title><link rel="stylesheet" href="{kok}styles.css"></head><body><div class="container"><header class="header"><h1>Diojen <span>News</span></h1><div class="logo">D</div></header><nav class="navbar"><a href="{kok}DiojenNews.html">Ana Sayfa</a><a href="{kok}kose.html">Köşe Yazıları</a><a href="{kok}arsiv/index.html" class="arsiv-link">📚 Arşiv</a></nav><div class="content"><main class="main-content"><section class="bolum">{icerik}</section></main></div></div></body></html>'''
    os.makedirs(os.path.join(base,"kose"), exist_ok=True)
    for f in glob.glob(os.path.join(base,"kose","*.html")): os.remove(f)
    for y in yazilar:
        ic = f'<p><a href="../kose.html">← Tüm köşe yazıları</a></p><article class="card kose"><div class="meta">{e(y["meta"])}</div><h3>{e(y["baslik"])}</h3>{y["govde"]}</article>'
        open(os.path.join(base,"kose",y["slug"]+".html"),"w",encoding="utf-8").write(sayfa_kose(y["baslik"], ic, "../"))
    kartlar = "".join(f'<article class="card kose"><div class="meta">{e(y["meta"])}</div><h3>{e(y["baslik"])}</h3>{y["govde"]}</article>' for y in guncel)
    liste = "".join(f'<li><a href="kose/{e(y["slug"])}.html">{e(y["baslik"])}</a> <span class="meta">{e(y["meta"])}</span></li>' for y in eski)
    onceki = f'<h2>Önceki Köşe Yazıları</h2><ul class="kose-liste">{liste}</ul>' if eski else ""
    open(os.path.join(base,"kose.html"),"w",encoding="utf-8").write(sayfa_kose("Köşe Yazıları", f'<h2>Köşe Yazıları</h2>{kartlar}{onceki}', ""))
man = ""
if manset:
    man = '<section class="manset"><h2>Manşet</h2>' + "".join(f'<div class="mkart"><div class="meta">{e(a)} · {e(h.get("tarih",""))}</div><h3>{e(h.get("baslik",""))}</h3><p>{e(h.get("ozet",""))}</p></div>' for a,h in manset[:3]) + '</section>'
PIYASA = [("usdtry","USD/TRY"),("eurtry","EUR/TRY"),("gram","Gram Altın"),("ons","Ons Altın"),("bist","BIST 100"),("brent","Brent Petrol"),("btc","Bitcoin")]
piyasa_html = '<section class="piyasa" id="piyasa" aria-label="Piyasalar"><h2>Piyasalar <span class="canli">● canlı</span></h2><div class="pz-liste">' + "".join(f'<div class="pz" id="pz-{i}"><div class="pz-ad">{e(a)}</div><div class="pz-deger">…</div><div class="pz-deg"></div><div class="pz-kaynak">yükleniyor</div></div>' for i,a in PIYASA) + '</div><p class="piyasa-not" id="piyasa-son">Veriler tarayıcıda canlı çekilir; JavaScript kapalıysa görüntülenemez.</p><noscript><p class="piyasa-not">Canlı piyasa verisi için JavaScript gerekir.</p></noscript></section>'
try: piyasa_js = open(os.path.join(base,"piyasa.js"),encoding="utf-8").read().replace("</script","<\\/script")
except Exception: piyasa_js = ""
yil = datetime.date.today().year
sayfa = f'''<!DOCTYPE html>
<html lang="tr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="description" content="Diojen News - Dünya, ekonomi, spor, teknoloji ve kültür haberleri">
<title>Diojen News</title>
<link rel="stylesheet" href="styles.css">
</head>
<body>
<div class="container" id="ust">
<header class="header"><h1>Diojen <span>News</span></h1><div class="logo">D</div></header>
<nav class="navbar">{nav}</nav>
{piyasa_html}
<div class="content">
<aside class="sidebar"><h2>Kategoriler</h2><ul>{yan}</ul></aside>
<main class="main-content">{man}{"".join(bol)}</main>
</div>
<footer class="footer"><p>&copy; {yil} Diojen News. Tüm hakları saklıdır. Son güncelleme: {datetime.datetime.now().strftime("%d.%m.%Y %H:%M")}</p></footer>
</div>
<script>
{piyasa_js}
</script>
</body>
</html>'''
open(os.path.join(base,"DiojenNews.html"),"w",encoding="utf-8").write(sayfa)
print("uretildi")
