#!/usr/bin/env python3
"""Diojen News: haberler/*.json dosyalarindan DiojenNews.html uretir."""
import re, json, html, os, glob, datetime
KAT = [("dunya","Dünya"),("ekonomi","Ekonomi"),("spor","Spor"),("teknoloji","Teknoloji"),("kultur","Kültür & Sanat"),("projectsyndicate","Project Syndicate"),("kimnedi","Kim Ne Dedi"),("sirket","Şirket Haberleri"),("bist30","BIST 30 Şirketleri")]
base = os.path.dirname(os.path.abspath(__file__))
def yukle(slug):
    p = os.path.join(base,"haberler",slug+".json")
    if not os.path.exists(p): return {"yazar":"","haberler":[]}
    try: return json.load(open(p,encoding="utf-8"))
    except Exception: return {"yazar":"","haberler":[]}
e = html.escape
KONU = [("askeri",["uçak gemisi","donanma","askeri","savaş gemisi","füze","husi","saldırı","savaş"]),("petrol",["petrol","dizel","varil","akaryakıt","brent","doğalgaz"]),
("yapayzeka",["yapay zek","openai","anthropic","gemini","chatgpt","ajan platformu","modeli","parametre"]),("uzay",["uzay","uydu","veri merkezi","nasa","spacex"]),
("bilgisayar",["apple","macos","windows","yazılım","siber","iphone","android","telefon","teknoloji"]),
("tiyatro",["tiyatro","sahne","opera","bale"]),("film",["film","sinema","dizi","yönetmen","oscar"]),("muzik",["müzik","konser","orkestra","senfoni","albüm","şarkı","iş sanat"]),
("arkeoloji",["arkeolo","kazı","tümülüs","antik","sardes"]),("basketbol",["basketbol","euroleague","nba"]),("madalya",["madalya","olimpiyat","asya oyunları","şampiyon"]),
("futbol",["futbol","maç","süper lig","galatasaray","fenerbahçe","beşiktaş","trabzonspor","real madrid","barcelona","gol ","portekiz","milli takım"]),
("banka",["merkez banka","faiz","ppk","fed ","rezerv"]),("enflasyon",["enflasyon","tüfe","fiyat artış"]),("borsa",["borsa","bist","hisse","endeks"]),
("altin",["altın","dolar","döviz"]),("ucak",["uçak","havayolu","flydubai","havalimanı"]),("diplomasi",["diplomatik","büyükelçi","zirve","müzakere","ateşkes","anlaşma","g7","nato","ilişkiler"])]
KONU_VARSAYILAN = {"dunya":"diplomasi","ekonomi":"borsa","spor":"futbol","teknoloji":"bilgisayar","kultur":"tiyatro","projectsyndicate":"diplomasi","kimnedi":"diplomasi","sirket":"banka","bist30":"borsa"}
def konu_resmi(slug, h):
    for alan in (h.get("baslik",""), h.get("ozet","")):
        t = alan.lower().replace("i̇","i")
        for ad,anahtarlar in KONU:
            if any(k in t for k in anahtarlar) and os.path.exists(os.path.join(base,"gorseller","konu",ad+".jpg")): return ad
    return KONU_VARSAYILAN.get(slug)
kose_dosyalar = sorted(glob.glob(os.path.join(base,"koseyazilari","*.md")), reverse=True)
KAT_NAV = KAT + ([("kose","Köşe Yazıları")] if kose_dosyalar else [])
nav = '<a href="#ust">Ana Sayfa</a>' + "".join(f'<a href="{"kose.html" if s=="kose" else "#"+s}">{e(a)}</a>' for s,a in KAT_NAV) + '<a href="arsiv/index.html" class="arsiv-link">📚 Arşiv</a>'
yan = "".join(f'<li><a href="{"kose.html" if s=="kose" else "#"+s}">{e(a)}</a></li>' for s,a in KAT_NAV) + '<li><a href="arsiv/index.html">📚 Arşiv (eski sayılar)</a></li>'
bol = []
manset = []
for s,ad in KAT:
    d = yukle(s); hab = d.get("haberler",[])[:(30 if s=="bist30" else 6)]
    kart = []
    for i,h in enumerate(hab):
        kaynak = ""
        if h.get("kaynak"):
            kaynak = f'<span class="kaynak">Kaynak: {e(h["kaynak"])}</span>'
            if h.get("kaynak_url"): kaynak = f'<a class="kaynak" href="{e(h["kaynak_url"])}" target="_blank" rel="noopener">Kaynak: {e(h["kaynak"])}</a>'
        kr = konu_resmi(s,h); resim = f'<img class="haber-resim" src="gorseller/konu/{kr}.jpg" alt="" loading="lazy">' if kr else ""
        kart.append(f'<article class="card{" resimli" if resim else ""}">{resim}<div class="meta">{e(h.get("tarih",""))}</div><h3>{e(h.get("baslik",""))}</h3><p>{e(h.get("ozet",""))}</p>{kaynak}</article>')
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
    def kose_kart(y, kok):
        img = f'<img class="kose-resim" src="{kok}gorseller/{y["slug"]}.jpg" alt="{e(y["baslik"])}">' if os.path.exists(os.path.join(base,"gorseller",y["slug"]+".jpg")) else ""
        return f'<article class="card kose"><div class="kose-metin"><div class="meta">{e(y["meta"])}</div><h3>{e(y["baslik"])}</h3>{y["govde"]}</div>{img}</article>'
    def sayfa_kose(baslik, icerik, kok):
        return f'''<!DOCTYPE html><html lang="tr"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>{e(baslik)} - Diojen News</title><link rel="stylesheet" href="{kok}styles.css"></head><body><div class="container"><header class="header"><h1>Diojen <span>News</span></h1><div class="logo">D</div></header><nav class="navbar"><a href="{kok}DiojenNews.html">Ana Sayfa</a><a href="{kok}kose.html">Köşe Yazıları</a><a href="{kok}arsiv/index.html" class="arsiv-link">📚 Arşiv</a></nav><div class="kose-sayfa"><section class="bolum">{icerik}</section></div></div></body></html>'''
    os.makedirs(os.path.join(base,"kose"), exist_ok=True)
    for f in glob.glob(os.path.join(base,"kose","*.html")): os.remove(f)
    for y in yazilar:
        ic = f'<p><a href="../kose.html">← Tüm köşe yazıları</a></p>' + kose_kart(y, "../")
        open(os.path.join(base,"kose",y["slug"]+".html"),"w",encoding="utf-8").write(sayfa_kose(y["baslik"], ic, "../"))
    kartlar = "".join(kose_kart(y, "") for y in guncel)
    liste = "".join(f'<li><a href="kose/{e(y["slug"])}.html">{e(y["baslik"])}</a> <span class="meta">{e(y["meta"])}</span></li>' for y in eski)
    onceki = f'<h2>Önceki Köşe Yazıları</h2><ul class="kose-liste">{liste}</ul>' if eski else ""
    open(os.path.join(base,"kose.html"),"w",encoding="utf-8").write(sayfa_kose("Köşe Yazıları", f'<h2>Köşe Yazıları</h2>{kartlar}{onceki}', ""))
man = ""
if manset:
    man = '<section class="manset"><h2>Manşet</h2>' + "".join(f'<div class="mkart"><div class="meta">{e(a)} · {e(h.get("tarih",""))}</div><h3>{e(h.get("baslik",""))}</h3><p>{e(h.get("ozet",""))}</p></div>' for a,h in manset[:3]) + '</section>'
PIYASA = [("usdtry","USD/TRY"),("eurtry","EUR/TRY"),("gbptry","GBP/TRY"),("chftry","CHF/TRY"),("audtry","AUD/TRY"),("gram","Gram Altın"),("ons","Ons Altın"),("bist","BIST 100"),("brent","Brent Petrol"),("btc","Bitcoin")]
piyasa_html = '<section class="piyasa" id="piyasa" aria-label="Piyasalar"><h2>Piyasalar <span class="canli">● canlı</span></h2><div class="pz-liste">' + "".join(f'<div class="pz" id="pz-{i}"><div class="pz-ad">{e(a)}</div><div class="pz-deger">…</div><div class="pz-deg"></div><div class="pz-kaynak">yükleniyor</div></div>' for i,a in PIYASA) + '</div><p class="piyasa-not" id="piyasa-son">Veriler tarayıcıda canlı çekilir; JavaScript kapalıysa görüntülenemez.</p><noscript><p class="piyasa-not">Canlı piyasa verisi için JavaScript gerekir.</p></noscript></section>'
try: piyasa_js = open(os.path.join(base,"piyasa.js"),encoding="utf-8").read().replace("</script","<\\/script")
except Exception: piyasa_js = ""

# ---- Makaleler: makaleler/*.md -> makaleler/<slug>.html ----
def satir_ici(s):
    s = e(s)
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"(?<!\*)\*(?!\s)(.+?)(?<!\s)\*(?!\*)", r"<em>\1</em>", s)
    s = re.sub(r"\[(\d{1,3})\]", lambda m: f'<sup class="atif"><a href="#k{m.group(1)}">[{m.group(1)}]</a></sup>', s)
    return s
def kaynak_satiri(s):
    parcalar = []
    for par in re.split(r"\s+;\s+", s.strip()):
        m = re.match(r"^(.*?):?\s*(https?://\S+)\s*$", par)
        if m:
            url = m.group(2); alan = re.sub(r"^https?://(www\.|mobile\.)?", "", url).split("/")[0]
            parcalar.append(f'{e(m.group(1).strip())} — <a href="{e(url)}" target="_blank" rel="noopener">{e(alan)} ↗</a>')
        else: parcalar.append(e(par))
    return "<br>".join(parcalar)
def makale_oku(p):
    try: satirlar = open(p,encoding="utf-8").read().split("\n")
    except Exception: return None
    baslik = ""; meta = ""; spot = ""; govde = []; kaynaklar = []; mod = "govde"; liste = []; par = []
    def par_bitir():
        if par: govde.append(f'<p>{satir_ici(" ".join(par))}</p>'); par.clear()
    def liste_bitir():
        if liste: govde.append("<ul>" + "".join(f"<li>{satir_ici(x)}</li>" for x in liste) + "</ul>"); liste.clear()
    for ham in satirlar:
        l = ham.strip()
        hm = re.match(r"^(#{1,6})\s+(.*)$", l)
        if hm:
            par_bitir(); liste_bitir()
            ad = hm.group(2).strip().replace("**","")
            cf = ad.casefold()
            if cf.startswith("doğrulanamayan") or cf.startswith("dogrulanamayan"): mod = "dur"
            elif cf == "kaynaklar": mod = "kaynak"
            elif len(hm.group(1)) == 1 and not baslik: baslik = ad
            elif mod != "dur":
                mod = "govde"; govde.append(f'<h2>{e(ad)}</h2>')
            continue
        if mod == "dur" or not l: 
            if mod == "govde": par_bitir(); liste_bitir()
            continue
        if mod == "kaynak":
            km = re.match(r"^(\d+)[.)]\s+(.*)$", l)
            if km: kaynaklar.append((km.group(1), km.group(2)))
            elif kaynaklar: kaynaklar[-1] = (kaynaklar[-1][0], kaynaklar[-1][1] + " " + l)
            continue
        if not meta and l.startswith("**") and l.endswith("**") and "|" in l:
            meta = l.strip("*").strip(); continue
        if not spot and not govde and re.match(r"^\*[^*].*[^*]\*$", l):
            spot = l[1:-1].strip(); continue
        if re.match(r"^[-*]\s+", l): par_bitir(); liste.append(re.sub(r"^[-*]\s+","",l)); continue
        liste_bitir(); par.append(l)
    par_bitir(); liste_bitir()
    if not baslik: return None
    m = re.search(r"(\d{2})\.(\d{2})\.(\d{4})", meta)
    tarih = m.group(0) if m else ""
    sirala = f"{m.group(3)}-{m.group(2)}-{m.group(1)}" if m else "0000-00-00"
    parts = [x.strip() for x in meta.split("|")]
    yazar = re.sub(r"^Yazar:\s*", "", parts[0]) if parts and parts[0] else ""
    kat = parts[1] if len(parts) > 2 else ""
    slug = os.path.splitext(os.path.basename(p))[0]
    return {"slug":slug,"baslik":baslik,"yazar":yazar,"kategori":kat,"tarih":tarih,"sirala":sirala,"spot":spot,"govde":"".join(govde),"kaynaklar":kaynaklar,
            "resim_var":os.path.exists(os.path.join(base,"gorseller",slug+".jpg")),"resim900_var":os.path.exists(os.path.join(base,"gorseller",slug+"-900.jpg"))}
makale_dosyalar = sorted(glob.glob(os.path.join(base,"makaleler","*.md")))
makaleler = [y for y in (makale_oku(p) for p in makale_dosyalar) if y]
makaleler.sort(key=lambda y:y["sirala"], reverse=True)
def makale_sayfasi(y):
    img = ""
    if y["resim_var"]:
        src = y["slug"] + ("-900.jpg" if y["resim900_var"] else ".jpg")
        img = f'<figure class="makale-gorsel"><img src="../gorseller/{e(src)}" alt="{e(y["baslik"])}"></figure>'
    meta = " · ".join(x for x in (f'Yazar: {e(y["yazar"])}' if y["yazar"] else "", e(y["kategori"]), e(y["tarih"])) if x)
    spot = f'<p class="makale-spot">{satir_ici(y["spot"])}</p>' if y["spot"] else ""
    kay = ""
    if y["kaynaklar"]:
        kay = '<section class="makale-kaynaklar"><h2>Kaynaklar</h2><ol>' + "".join(f'<li id="k{n}" value="{n}">{kaynak_satiri(s)}</li>' for n,s in y["kaynaklar"]) + '</ol></section>'
    nav2 = '<a href="../DiojenNews.html">Ana Sayfa</a><a href="../kose.html">Köşe Yazıları</a><a href="../arsiv/index.html" class="arsiv-link">📚 Arşiv</a>'
    return f'''<!DOCTYPE html>
<html lang="tr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="description" content="{e(y["spot"][:200])}">
<title>{e(y["baslik"])} - Diojen News</title>
<link rel="stylesheet" href="../styles.css">
</head>
<body>
<div class="container">
<header class="header"><h1>Diojen <span>News</span></h1><div class="logo">D</div></header>
<nav class="navbar">{nav2}</nav>
<article class="makale-sayfa">
<p class="makale-geri"><a href="../DiojenNews.html">← Ana sayfaya dön</a> · <a href="../arsiv/index.html">📚 Arşiv</a></p>
<div class="meta">{meta}</div>
<h1 class="makale-baslik">{e(y["baslik"])}</h1>
{spot}
{img}
<div class="makale-govde">{y["govde"]}</div>
{kay}
<p class="makale-geri alt"><a href="../DiojenNews.html">← Ana sayfaya dön</a> · <a href="../arsiv/index.html">📚 Arşiv</a></p>
</article>
<footer class="footer"><p>&copy; {datetime.date.today().year} Diojen News. Tüm hakları saklıdır.</p></footer>
</div>
</body>
</html>'''
for y in makaleler:
    open(os.path.join(base,"makaleler",y["slug"]+".html"),"w",encoding="utf-8").write(makale_sayfasi(y))
makale_html = ""
if makaleler:
    kk = []
    for y in makaleler[:3]:
        img = f'<img class="makale-kucuk" src="gorseller/{e(y["slug"])}.jpg" alt="{e(y["baslik"])}">' if y["resim_var"] else ""
        by = f'Yazar: {e(y["yazar"])}' + (f' · {e(y["tarih"])}' if y["tarih"] else "")
        kk.append(f'<article class="makale-kart">{img}<div class="makale-ozet"><div class="meta">{by}</div><h3><a href="makaleler/{e(y["slug"])}.html">{e(y["baslik"])}</a></h3><p>{e(y["spot"])}</p><a class="makale-oku" href="makaleler/{e(y["slug"])}.html">Makaleyi oku →</a></div></article>')
    makale_html = '<section class="makale-bolum" id="makale"><h2>Köşe Yazısı / Makale</h2>' + "".join(kk) + '</section>'
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
<main class="main-content">{man}{makale_html}{"".join(bol)}</main>
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
