#!/usr/bin/env python3
"""Yeni sayi cikarir: build.py ile gazeteyi uretir, arsiv/<tarih_saat>/ altina kopyalar, arsiv/index.html'i gunceller."""
import os, shutil, subprocess, datetime, json, glob, html, sys
base = os.path.dirname(os.path.abspath(__file__))
subprocess.run([sys.executable, os.path.join(base, "build.py")], check=True)
sayi = datetime.datetime.now().strftime("%Y-%m-%d_%H%M")
hedef = os.path.join(base, "arsiv", sayi)
os.makedirs(os.path.join(hedef, "haberler"), exist_ok=True)
for d in ("DiojenNews.html", "styles.css", "kose.html"):
    if os.path.exists(os.path.join(base, d)): shutil.copy(os.path.join(base, d), hedef)
if os.path.isdir(os.path.join(base, "kose")): shutil.copytree(os.path.join(base, "kose"), os.path.join(hedef, "kose"), dirs_exist_ok=True)
for f in glob.glob(os.path.join(base, "haberler", "*.json")):
    shutil.copy(f, os.path.join(hedef, "haberler"))
ap = os.path.join(hedef, "DiojenNews.html")
t = open(ap, encoding="utf-8").read().replace('href="arsiv/index.html"', 'href="../index.html"')
open(ap, "w", encoding="utf-8").write(t)
kose = os.path.join(base, "koseyazilari")
if os.path.isdir(kose):
    shutil.copytree(kose, os.path.join(hedef, "koseyazilari"), dirs_exist_ok=True)
sayilar = sorted([d for d in os.listdir(os.path.join(base, "arsiv")) if os.path.isdir(os.path.join(base, "arsiv", d))], reverse=True)
satir = "".join(
    f'<li><a href="{html.escape(s)}/DiojenNews.html">{s[8:10]}.{s[5:7]}.{s[0:4]} {s[11:13]}:{s[13:15]} sayısı</a></li>'
    for s in sayilar)
open(os.path.join(base, "arsiv", "index.html"), "w", encoding="utf-8").write(
    f'<!DOCTYPE html><html lang="tr"><head><meta charset="UTF-8"><title>Diojen News Arşiv</title>'
    f'<link rel="stylesheet" href="../styles.css"></head><body><div class="container"><header class="header"><h1>Diojen <span>News</span> Arşiv</h1></header>'
    f'<main class="main-content"><p>Toplam {len(sayilar)} sayı. <a href="../DiojenNews.html">Güncel sayıya dön</a></p><ul>{satir}</ul></main></div></body></html>')
print("yeni sayi:", sayi)
