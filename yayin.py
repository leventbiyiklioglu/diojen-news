#!/usr/bin/env python3
"""Yeni sayi cikarir: build.py ile gazeteyi uretir, arsiv/<tarih_saat>/ altina kopyalar, arsiv/index.html'i gunceller.
Arsivdeki tum HTML sayfalari noindex,follow ve ana surume canonical alir (SEO: kopya icerik olmasin).
python3 yayin.py             -> normal yayin (varsayilan, gozetimsiz calisir)
python3 yayin.py --kopyasiz  -> build + arsiv/index.html + arsiv isaretleme; yeni arsiv kopyasi ALMAZ (test/duzeltme icin)"""
import os, re, shutil, subprocess, datetime, json, glob, html, sys
base = os.path.dirname(os.path.abspath(__file__))
SITE = "https://diojennews.com"
KOPYASIZ = "--kopyasiz" in sys.argv[1:]
subprocess.run([sys.executable, os.path.join(base, "build.py")], check=True)
def oku(p): return open(p, encoding="utf-8").read()
def yaz(p, t): open(p, "w", encoding="utf-8").write(t)
def degistir(yol, eski_yeni):
    if not os.path.exists(yol): return
    t = oku(yol); y = t
    for a, b in eski_yeni: y = y.replace(a, b)
    if y != t: yaz(yol, y)
if not KOPYASIZ:
    sayi = datetime.datetime.now().strftime("%Y-%m-%d_%H%M")
    hedef = os.path.join(base, "arsiv", sayi)
    os.makedirs(os.path.join(hedef, "haberler"), exist_ok=True)
    for d in ("DiojenNews.html", "styles.css", "kose.html", "dedekorkut.html"):
        if os.path.exists(os.path.join(base, d)): shutil.copy(os.path.join(base, d), hedef)
    if os.path.isdir(os.path.join(base, "kose")): shutil.copytree(os.path.join(base, "kose"), os.path.join(hedef, "kose"), dirs_exist_ok=True)
    for f in glob.glob(os.path.join(base, "haberler", "*.json")):
        shutil.copy(f, os.path.join(hedef, "haberler"))
    if os.path.isdir(os.path.join(base, "dedekorkut")): shutil.copytree(os.path.join(base, "dedekorkut"), os.path.join(hedef, "dedekorkut"), dirs_exist_ok=True)
    # arsiv/<sayi>/ icindeki sayfalarin "Arsiv" baglantisi arsiv/index.html'e (bir ust dizine) gitmeli
    for ad in ("kose.html", "dedekorkut.html", "DiojenNews.html"):
        degistir(os.path.join(hedef, ad), [('href="arsiv/index.html"', 'href="../index.html"'), ('href="arsiv/"', 'href="../"')])
    if os.path.isdir(os.path.join(base, "gorseller")): shutil.copytree(os.path.join(base, "gorseller"), os.path.join(hedef, "gorseller"), dirs_exist_ok=True)
    for klasor in ("gorseller", "makaleler"):
        if os.path.isdir(os.path.join(base, klasor)): shutil.copytree(os.path.join(base, klasor), os.path.join(hedef, klasor), dirs_exist_ok=True)
    # alt klasordeki arsivlenmis sayfalarda (makaleler/, kose/) arsiv baglantisi iki ust dizine gitmeli
    for mf in glob.glob(os.path.join(hedef, "makaleler", "*.html")) + glob.glob(os.path.join(hedef, "kose", "*.html")):
        degistir(mf, [('href="../arsiv/index.html"', 'href="../../index.html"'), ('href="../arsiv/"', 'href="../../"')])
    # yeni bolumler (kultur-sanat/sinema-ogrenci/, gise-hasilatlari/, yeni-cikanlar/, arsiv-dosyasi/) arsive kopyalanmaz; linkleri canli bolume gitsin
    try:
        import ozel_sayfalar; ozel_sayfalar.arsiv_kopyasi_linkleri(hedef)
    except Exception as hata: print("ozel bolum linkleri atlandi:", hata)
    kose = os.path.join(base, "koseyazilari")
    if os.path.isdir(kose):
        shutil.copytree(kose, os.path.join(hedef, "koseyazilari"), dirs_exist_ok=True)
# ---- Arsiv sayfalari: noindex,follow + ana surume canonical (idempotent; eski sayilara da uygulanir) ----
ROBOTS = '<meta name="robots" content="noindex,follow">'
def ana_yol(rel):
    """arsiv/<sayi>/ icindeki goreli yol -> canlidaki ana surumun uzantisiz yolu (yoksa None)."""
    if not os.path.exists(os.path.join(base, rel)): return None
    r = rel[:-5] if rel.endswith(".html") else rel
    return "" if r == "DiojenNews" else r
for f in glob.glob(os.path.join(base, "arsiv", "*", "**", "*.html"), recursive=True):
    rel = os.path.relpath(f, os.path.join(base, "arsiv")).replace(os.sep, "/").split("/", 1)[1]
    t = oku(f); y = t
    if re.search(r'<meta name="robots"[^>]*>', y): y = re.sub(r'<meta name="robots"[^>]*>', ROBOTS, y, count=1)
    else:
        ek = ROBOTS
        a = ana_yol(rel)
        if 'rel="canonical"' not in y and a is not None: ek += f'<link rel="canonical" href="{SITE}/{a}">'
        k = re.search(r'<meta charset="UTF-8">', y, re.I) or re.search(r'<head>', y, re.I)
        if k: y = y[:k.end()] + ek + y[k.end():]
    if y != t: yaz(f, y)
# ---- arsiv/index.html ----
m = re.search(r'<script>\(function\(k\)\{.*?\}\)\("[^"]*"\);</script>', oku(os.path.join(base, "DiojenNews.html")), re.S)
link_betigi = m.group(0).rsplit('("', 1)[0] + '("../");</script>' if m else ""
sayilar = sorted([d for d in os.listdir(os.path.join(base, "arsiv")) if os.path.isdir(os.path.join(base, "arsiv", d))], reverse=True)
satir = "".join(
    f'<li><a href="{html.escape(s)}/DiojenNews">{s[8:10]}.{s[5:7]}.{s[0:4]} {s[11:13]}:{s[13:15]} sayısı</a></li>'
    for s in sayilar)
yaz(os.path.join(base, "arsiv", "index.html"),
    f'<!DOCTYPE html><html lang="tr"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>Diojen News Arşiv</title>'
    f'<meta name="description" content="Diojen News&#x27;in önceki sayıları.">{ROBOTS}<link rel="canonical" href="{SITE}/arsiv/">{link_betigi}'
    f'<link rel="stylesheet" href="../styles.css"></head><body><div class="container"><header class="header"><h1>Diojen <span>News</span> Arşiv</h1></header>'
    f'<main class="main-content"><p>Toplam {len(sayilar)} sayı. <a href="/">Güncel sayıya dön</a></p><ul>{satir}</ul></main></div></body></html>')
# arsiv/index.html -> bolum arsivleri linkleri (sayi listesine karismaz)
try:
    import ozel_sayfalar; ozel_sayfalar.ana_arsiv_index_ekle(base)
except Exception as hata: print("bolum arsivleri linki atlandi:", hata)
print("yeni sayi:", "(kopya alinmadi, --kopyasiz)" if KOPYASIZ else sayi)
