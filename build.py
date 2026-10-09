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
# ---- SEO yardimcilari (Seda, 09.10.2026) ----
# Canli sitede adresler uzantisiz: /, /kose, /makaleler/<slug>, /arsiv/ . Eski .html adresleri calismaya devam eder
# (dosyalar yine .html olarak yazilir; GitHub Pages uzantisiz istegi .html dosyasina eslestirir).
# PC kopyasi (file://) icin her sayfadaki kucuk betik baglantilara .html ekler; canli sitede ise adres cubugundaki .html'i siler.
# Yeni bolumler bu fonksiyonlari cagirmali: seo_head(...), jsonld_haber/jsonld_koleksiyon/jsonld_eser_listesi(...), sitemap_ekle(...).
# URL plani (yeni bolumler): bolum ana sayfasi /bolum/ (bolum/index.html), icerik /bolum/<slug> (bolum/<slug>.html), arsiv /bolum/arsiv/.
import subprocess
SITE = "https://diojennews.com"
YAYIN_ADI = "Diojen News"
VARSAYILAN_ACIKLAMA = "Diojen News - Dünya, ekonomi, spor, teknoloji ve kültür haberleri"
def mutlak(yol):
    """Site kokune gore yol ('', 'kose', 'makaleler/x', 'gorseller/a.jpg') -> mutlak URL."""
    yol = (yol or "").lstrip("/")
    return SITE + "/" + yol
def _git_tarih(rel):
    try:
        r = subprocess.run(["git", "log", "-1", "--format=%cI", "--", rel], cwd=base, capture_output=True, text=True, timeout=10)
        return r.stdout.strip()
    except Exception: return ""
_takip = None
def yayinda_mi(rel):
    """Sitemap'e yalniz git'te takip edilen (yani canliya cikan) sayfalar girer. git yoksa hepsi sayilir."""
    global _takip
    if _takip is None:
        try:
            r = subprocess.run(["git", "ls-files"], cwd=base, capture_output=True, text=True, timeout=20)
            _takip = set(r.stdout.split("\n")) if r.returncode == 0 else False
        except Exception: _takip = False
    return True if _takip is False else rel in _takip
def degisme_tarihi(rel, yayin_iso):
    """dateModified: kaynak dosyanin son commit zamani (yayin tarihinden once degilse); yoksa yayin tarihi. Tarih uydurulmaz."""
    g = _git_tarih(rel)
    return g if g and yayin_iso and g[:10] >= yayin_iso[:10] else yayin_iso
def kisa_metin(s, n=160):
    s = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", s or "").replace("**", "").replace("*", "")).strip()
    if len(s) <= n: return s
    return s[:n].rsplit(" ", 1)[0].rstrip(",;:—-") + "…"
def _ld(veri):
    return '<script type="application/ld+json">' + json.dumps(veri, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/") + "</script>"
def jsonld_yayinci():
    return {"@type": "NewsMediaOrganization", "name": YAYIN_ADI, "url": SITE + "/"}
def jsonld_haber(baslik, yol, yayin_iso, degisme_iso, yazar="", aciklama="", resim=None, bolum="", tur="NewsArticle"):
    """Makale/kose/Arsiv Dosyasi icin NewsArticle. resim: site kokune gore yol listesi."""
    v = {"@context": "https://schema.org", "@type": tur, "headline": baslik, "inLanguage": "tr",
         "mainEntityOfPage": {"@type": "WebPage", "@id": mutlak(yol)}, "publisher": jsonld_yayinci()}
    if aciklama: v["description"] = aciklama
    if yayin_iso: v["datePublished"] = yayin_iso
    if degisme_iso: v["dateModified"] = degisme_iso
    if yazar: v["author"] = [{"@type": "Person", "name": yazar}]
    if resim: v["image"] = [mutlak(r) for r in resim]
    if bolum: v["articleSection"] = bolum
    return v
def jsonld_koleksiyon(ad, yol, aciklama=""):
    """Bolum ana sayfasi / bolum arsivi icin CollectionPage."""
    v = {"@context": "https://schema.org", "@type": "CollectionPage", "name": ad, "url": mutlak(yol), "inLanguage": "tr", "isPartOf": {"@type": "WebSite", "name": YAYIN_ADI, "url": SITE + "/"}}
    if aciklama: v["description"] = aciklama
    return v
def jsonld_eser_listesi(ad, yol, eserler):
    """Gise / Yeni Cikanlar tablolari icin ItemList. eserler: [{"tur":"Movie"|"TVSeries","ad":..., "url":opsiyonel, ...ek schema alanlari}].
    Yalniz dogrulanmis alanlari verin; Google'in gise hasilati icin ozel zengin sonucu yoktur, bu isaretleme anlamsal amaclidir."""
    ogeler = []
    for i, x in enumerate(eserler, 1):
        o = {"@type": x.get("tur", "Movie"), "name": x["ad"]}
        if x.get("url"): o["url"] = x["url"]
        for k, d in x.items():
            if k not in ("tur", "ad", "url") and d: o[k] = d
        ogeler.append({"@type": "ListItem", "position": i, "item": o})
    return {"@context": "https://schema.org", "@type": "ItemList", "name": ad, "url": mutlak(yol), "numberOfItems": len(ogeler), "itemListElement": ogeler}
LINK_BETIGI = ('<script>(function(k){var L=location;if(L.protocol==="file:"){document.addEventListener("DOMContentLoaded",function(){'
  'var a=document.querySelectorAll("a[href]");for(var i=0;i<a.length;i++){var h=a[i].getAttribute("href");'
  'if(/^([a-z][a-z0-9+.-]*:|#|\\/\\/)/i.test(h))continue;var j=h.search(/[?#]/),p=j<0?h:h.slice(0,j),r=j<0?"":h.slice(j);'
  'if(p==="/")p=k+"DiojenNews.html";else{if(p.charAt(0)==="/")p=k+p.slice(1);'
  'if(p===""||p.slice(-1)==="/")p+="index.html";else if(!/\\.[a-z0-9]+$/i.test(p.split("/").pop()))p+=".html";}'
  'a[i].setAttribute("href",p+r);}});}else if(/^https?:$/.test(L.protocol)&&/\\.html$/.test(L.pathname)&&history.replaceState){'
  'var p=L.pathname==="/DiojenNews.html"?"/":L.pathname.replace(/\\/index\\.html$/,"/").replace(/\\.html$/,"");'
  'history.replaceState(null,"",p+L.search+L.hash);}})("{KOK}");</script>')
def seo_head(baslik, aciklama, yol, kok="", og_tur="website", resim=None, jsonld=None, robots="index,follow,max-image-preview:large", tam_baslik=False):
    """<head> icine: description, robots, canonical, OG, Twitter, JSON-LD, PC/uzantisiz link betigi.
    yol: uzantisiz kanonik yol ('' ana sayfa). kok: sayfanin site kokune goreli yolu ('', '../'). resim: kok-goreli yol."""
    t = baslik if tam_baslik else f"{baslik} - {YAYIN_ADI}"
    aciklama = kisa_metin(aciklama or VARSAYILAN_ACIKLAMA, 200)
    can = mutlak(yol)
    s = [f'<title>{e(t)}</title>', f'<meta name="description" content="{e(aciklama)}">', f'<meta name="robots" content="{robots}">',
         f'<link rel="canonical" href="{e(can)}">',
         f'<meta property="og:site_name" content="{YAYIN_ADI}">', '<meta property="og:locale" content="tr_TR">',
         f'<meta property="og:type" content="{og_tur}">', f'<meta property="og:title" content="{e(baslik)}">',
         f'<meta property="og:description" content="{e(aciklama)}">', f'<meta property="og:url" content="{e(can)}">']
    if resim:
        s += [f'<meta property="og:image" content="{e(mutlak(resim))}">', '<meta name="twitter:card" content="summary_large_image">',
              f'<meta name="twitter:image" content="{e(mutlak(resim))}">']
    else: s.append('<meta name="twitter:card" content="summary">')
    s += [f'<meta name="twitter:title" content="{e(baslik)}">', f'<meta name="twitter:description" content="{e(aciklama)}">']
    for v in ([jsonld] if isinstance(jsonld, dict) else (jsonld or [])): s.append(_ld(v))
    s.append(LINK_BETIGI.replace("{KOK}", kok))
    return "\n".join(s)
SITEMAP = []   # (yol, lastmod_iso, kaynak_html_rel)
HABERLER_SM = []  # (yol, baslik, yayin_iso)
def sitemap_ekle(yol, lastmod, kaynak_rel, haber_baslik=None, yayin_iso=None):
    if not yayinda_mi(kaynak_rel): print("sitemap: canlida degil, atlandi:", kaynak_rel); return
    SITEMAP.append((yol, lastmod, kaynak_rel))
    if haber_baslik and yayin_iso: HABERLER_SM.append((yol, haber_baslik, yayin_iso))
def iso_tarih(gg_aa_yyyy):
    m = re.search(r"(\d{2})\.(\d{2})\.(\d{4})", gg_aa_yyyy or "")
    return f"{m.group(3)}-{m.group(2)}-{m.group(1)}" if m else ""
def sitemaplari_yaz():
    from xml.sax.saxutils import escape as xe
    u = "".join(f"<url><loc>{xe(mutlak(y))}</loc>" + (f"<lastmod>{xe(l)}</lastmod>" if l else "") + "</url>\n" for y,l,_ in sorted(SITEMAP, key=lambda x:(x[0]!="", x[0].count("/"), x[0])))
    open(os.path.join(base,"sitemap.xml"),"w",encoding="utf-8").write(
        '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + u + "</urlset>\n")
    # Google News: yalniz son 2 gunde yayimlanan haberler (en fazla 1000)
    bugun = datetime.date.today()
    yeni = []
    for y,b,t in HABERLER_SM:
        try: d = datetime.date.fromisoformat(t[:10])
        except ValueError: continue
        if 0 <= (bugun - d).days <= 2: yeni.append((y,b,t))
    n = "".join(f"<url><loc>{xe(mutlak(y))}</loc><news:news><news:publication><news:name>{YAYIN_ADI}</news:name><news:language>tr</news:language>"
                f"</news:publication><news:publication_date>{xe(t)}</news:publication_date><news:title>{xe(b)}</news:title></news:news></url>\n" for y,b,t in yeni[:1000])
    open(os.path.join(base,"news-sitemap.xml"),"w",encoding="utf-8").write(
        '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:news="http://www.google.com/schemas/sitemap-news/0.9">\n' + n + "</urlset>\n")
    open(os.path.join(base,"robots.txt"),"w",encoding="utf-8").write(
        "# build.py tarafindan uretilir\nUser-agent: *\nAllow: /\nDisallow: /taslak/\nDisallow: /onizleme/\nDisallow: /koseyazilari/\nDisallow: /worker/\nDisallow: /YONERGE\n"
        "# arsiv/ engellenmez: arsiv sayfalarinda <meta name=\"robots\" content=\"noindex,follow\"> var, taranabilmeleri gerekir.\n\n"
        f"Sitemap: {SITE}/sitemap.xml\nSitemap: {SITE}/news-sitemap.xml\n")
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
def dk_nav(kok):
    return f'<a href="{kok}dedekorkut">{DK_AD}</a>' if dk_bolumler else ""
def dk_oku():
    try: v = json.load(open(os.path.join(base,"dedekorkut","bolumler.json"),encoding="utf-8"))
    except Exception: return []
    def anahtar(b):
        m = re.search(r"(\d{2})\.(\d{2})\.(\d{4})", b.get("tarih",""))
        return ((m.group(3),m.group(2),m.group(1)) if m else ("0000","00","00"), int(b.get("bolum",0) or 0))
    return sorted([b for b in v if b.get("paneller")], key=anahtar, reverse=True)
dk_bolumler = dk_oku()
DK_AD = "Dede Korkut Günlüğü"
if dk_bolumler: KAT_NAV = KAT_NAV + [("dedekorkut",DK_AD)]
SAYFA = {"kose":"kose","dedekorkut":"dedekorkut"}
nav = '<a href="#ust">Ana Sayfa</a>' + "".join(f'<a href="{SAYFA.get(s,"#"+s)}">{e(a)}</a>' for s,a in KAT_NAV) + '<a href="arsiv/" class="arsiv-link">📚 Arşiv</a>'
yan = "".join(f'<li><a href="{SAYFA.get(s,"#"+s)}">{e(a)}</a></li>' for s,a in KAT_NAV) + '<li><a href="arsiv/">📚 Arşiv (eski sayılar)</a></li>'
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
def sayfa_kose(baslik, icerik, kok, yol="", aciklama="", resim=None, jsonld=None, og_tur="website"):
    return f'''<!DOCTYPE html><html lang="tr"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
{seo_head(baslik, aciklama, yol, kok, og_tur, resim, jsonld)}
<link rel="stylesheet" href="{kok}styles.css"></head><body><div class="container"><header class="header"><h1>Diojen <span>News</span></h1><div class="logo">D</div></header><nav class="navbar"><a href="/">Ana Sayfa</a><a href="{kok}kose">Köşe Yazıları</a>{dk_nav(kok)}<a href="{kok}arsiv/" class="arsiv-link">📚 Arşiv</a></nav><div class="kose-sayfa"><section class="bolum">{icerik}</section></div></div></body></html>'''
def kose_oku(p):
    try: satirlar = [l.strip() for l in open(p,encoding="utf-8").read().split("\n") if l.strip()]
    except Exception: return None
    if not satirlar: return None
    meta = satirlar[1].replace("**","") if len(satirlar)>1 else ""
    m = re.search(r"(\d{2})\.(\d{2})\.(\d{4})", meta)
    tarih = f"{m.group(3)}-{m.group(2)}-{m.group(1)}" if m else "0000-00-00"
    return {"slug":os.path.splitext(os.path.basename(p))[0], "baslik":satirlar[0].lstrip("# ").strip(), "meta":meta, "tarih":tarih,
            "yazar":re.sub(r"^Yazar:\s*", "", meta.split("|")[0].strip()) if "|" in meta else "", "ozet":kisa_metin(satirlar[2] if len(satirlar)>2 else ""),
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
    os.makedirs(os.path.join(base,"kose"), exist_ok=True)
    for f in glob.glob(os.path.join(base,"kose","*.html")): os.remove(f)
    for y in yazilar:
        ic = f'<p><a href="../kose">← Tüm köşe yazıları</a></p>' + kose_kart(y, "../")
        kyol = "kose/" + y["slug"]; kres = f'gorseller/{y["slug"]}.jpg' if os.path.exists(os.path.join(base,"gorseller",y["slug"]+".jpg")) else None
        kiso = y["tarih"] if y["tarih"] != "0000-00-00" else ""
        kdeg = degisme_tarihi(f'koseyazilari/{y["slug"]}.md', kiso)
        kld = jsonld_haber(y["baslik"], kyol, kiso, kdeg, y["yazar"], y["ozet"], [kres] if kres else None, "Köşe Yazısı")
        open(os.path.join(base,"kose",y["slug"]+".html"),"w",encoding="utf-8").write(sayfa_kose(y["baslik"], ic, "../", kyol, y["ozet"], kres, kld, "article"))
        sitemap_ekle(kyol, kdeg, kyol + ".html", y["baslik"], kiso)
    kartlar = "".join(kose_kart(y, "") for y in guncel)
    liste = "".join(f'<li><a href="kose/{e(y["slug"])}">{e(y["baslik"])}</a> <span class="meta">{e(y["meta"])}</span></li>' for y in eski)
    onceki = f'<h2>Önceki Köşe Yazıları</h2><ul class="kose-liste">{liste}</ul>' if eski else ""
    open(os.path.join(base,"kose.html"),"w",encoding="utf-8").write(sayfa_kose("Köşe Yazıları", f'<h2>Köşe Yazıları</h2>{kartlar}{onceki}', "", "kose",
        "Diojen News köşe yazıları. Son yazılar: " + "; ".join(y["baslik"] for y in yazilar[:3])))
    sitemap_ekle("kose", guncel_tarih if guncel_tarih != "0000-00-00" else "", "kose.html")
# ---- Dede Korkut Günlüğü: dedekorkut/bolumler.json -> dedekorkut.html ----
if dk_bolumler:
    bl = []
    for b in dk_bolumler:
        pn = "".join(f'<figure class="dk-panel"><img src="{e(p["resim"])}" alt="{e(p.get("altyazi",""))}" loading="lazy"><figcaption>{e(p.get("altyazi",""))}</figcaption></figure>' for p in b["paneller"])
        bl.append(f'<article class="dk-bolum"><div class="meta">{e(b.get("hikaye",""))} · {e(str(b.get("bolum","")))}. Bölüm · {e(b.get("tarih",""))}</div><h3>{e(b.get("baslik",""))}</h3><div class="dk-izgara">{pn}</div></article>')
    sitemap_ekle("dedekorkut", iso_tarih(dk_bolumler[0].get("tarih","")), "dedekorkut.html")
    open(os.path.join(base,"dedekorkut.html"),"w",encoding="utf-8").write(sayfa_kose(DK_AD, f'<h2>{DK_AD}</h2><p class="dk-giris">Dede Korkut hikâyelerinden resimli, günlük bölümler. Her gün yeni bir bölüm.</p>{"".join(bl)}', "", "dedekorkut",
        "Dede Korkut hikâyelerinden resimli, günlük bölümler. Son bölüm: " + dk_bolumler[0].get("baslik",""),
        dk_bolumler[0]["paneller"][0].get("resim") or None).replace('<div class="kose-sayfa">','<div class="kose-sayfa dk-sayfa">',1))
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
def _lj(renk, metin, sekil=""):
    return f'<span class="lj"><i style="background:{renk}" class="{sekil}"></i>{metin}</span>'
HARITA_LEJANT = ('<div class="lejant"><b>Lejant</b> · '
  + _lj("#f5b7b1", "Borsada işlem gören şirket (hisse kodu)") + _lj("#f8c471", "Aracı kurum, banka, holding")
  + _lj("#f9e79f", "Portföy yönetim şirketi (PYŞ)") + _lj("#abebc6", "Yatırım fonları") + _lj("#d2b4de", "Yurt dışı şirket")
  + _lj("#d5d8dc", "Kamu kurumu / resmi işlem", "sekiz") + _lj("#aed6f1", "Ortak aile (şirket ortaklığı)", "elips")
  + '<br><span class="lj"><i class="cizgi duz"></i>Düz çizgi: resmi kayıt (KAP, SPK, Companies House)</span>'
  + '<span class="lj"><i class="cizgi kesik"></i>Kesikli çizgi: iddia (basın, savcılık dosyası aktarımı)</span>'
  + '<span class="lj">Çizgi rengi: ilgili grubun rengi (Tera kırmızı, Pusula mavi, Hedef ve yurt dışı mor, Destek yeşil)</span>'
  + '<br><em>Bir bağlantı suç ya da sorumluluk anlamına gelmez. Soruşturma sürüyor; kesinleşmiş yargı kararı yok. Haritada kişi yer almaz.</em></div>')
def sekil_html(alt, src):
    # ![açıklama](dosya.svg|jpg|png) -> figure; göreli dosyalar gorseller/dosya/ altından okunur
    if not re.match(r"^(https?:)?//", src) and not src.startswith("../"):
        src = "../gorseller/dosya/" + os.path.basename(src)
    harita = "harita" in src
    return (f'<figure class="sema{" harita" if harita else ""}"><a href="{e(src)}" target="_blank" rel="noopener"><img src="{e(src)}" alt="{e(alt)}" loading="lazy"></a>'
            f'<figcaption>{satir_ici(alt)} <span class="buyut">(Tam boyut için şemaya tıklayın.)</span></figcaption>'
            + (HARITA_LEJANT if harita else "") + '</figure>')
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
                mod = "govde"
                kutu = ad in ("Masumiyet karinesi", "Cevap hakkı", "Yatırım tavsiyesi değildir")
                govde.append(f'<h2{" class=\"not-baslik\"" if kutu else ""}>{e(ad)}</h2>')
            continue
        if mod == "dur" or not l: 
            if mod == "govde": par_bitir(); liste_bitir()
            continue
        if mod == "kaynak":
            km = re.match(r"^(\d+)[.)]\s+(.*)$", l)
            if km: kaynaklar.append((km.group(1), km.group(2)))
            elif kaynaklar: kaynaklar[-1] = (kaynaklar[-1][0], kaynaklar[-1][1] + " " + l)
            continue
        fm = re.match(r"^!\[(.*)\]\((\S+)\)$", l)
        if fm:
            par_bitir(); liste_bitir(); govde.append(sekil_html(fm.group(1), fm.group(2))); continue
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
    return {"dosya":baslik.casefold().startswith("dosya:"),"pdf_var":os.path.exists(os.path.join(base,"makaleler",slug+".pdf")),"slug":slug,"baslik":baslik,"yazar":yazar,"kategori":kat,"tarih":tarih,"sirala":sirala,"spot":spot,"govde":"".join(govde),"kaynaklar":kaynaklar,
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
    pdf = f'<p class="makale-pdf"><a href="{e(y["slug"])}.pdf" download>📄 Dosyayı PDF olarak indir</a></p>' if (y["dosya"] and y["pdf_var"]) else ""
    kay = ""
    if y["kaynaklar"]:
        kay = '<section class="makale-kaynaklar"><h2>Kaynaklar</h2><ol>' + "".join(f'<li id="k{n}" value="{n}">{kaynak_satiri(s)}</li>' for n,s in y["kaynaklar"]) + '</ol></section>'
    nav2 = '<a href="/">Ana Sayfa</a><a href="../kose">Köşe Yazıları</a>' + dk_nav("../") + '<a href="../arsiv/" class="arsiv-link">📚 Arşiv</a>'
    myol = "makaleler/" + y["slug"]; miso = y["sirala"] if y["sirala"] != "0000-00-00" else ""
    mres = ("gorseller/" + y["slug"] + ("-900.jpg" if y["resim900_var"] else ".jpg")) if y["resim_var"] else None
    mld = jsonld_haber(y["baslik"], myol, miso, degisme_tarihi(myol + ".md", miso), y["yazar"], kisa_metin(y["spot"], 200), [mres] if mres else None, y["kategori"])
    return f'''<!DOCTYPE html>
<html lang="tr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
{seo_head(y["baslik"], y["spot"], myol, "../", "article", mres, mld)}
<link rel="stylesheet" href="../styles.css">
</head>
<body>
<div class="container">
<header class="header"><h1>Diojen <span>News</span></h1><div class="logo">D</div></header>
<nav class="navbar">{nav2}</nav>
<article class="makale-sayfa">
<p class="makale-geri"><a href="/">← Ana sayfaya dön</a> · <a href="../arsiv/">📚 Arşiv</a></p>
<div class="meta">{meta}</div>
<h1 class="makale-baslik">{e(y["baslik"])}</h1>
{spot}
{img}
{pdf}<div class="makale-govde">{y["govde"]}</div>
{kay}
<p class="makale-geri alt"><a href="/">← Ana sayfaya dön</a> · <a href="../arsiv/">📚 Arşiv</a></p>
</article>
<footer class="footer"><p>&copy; {datetime.date.today().year} Diojen News. Tüm hakları saklıdır.</p></footer>
</div>
</body>
</html>'''
for y in makaleler:
    open(os.path.join(base,"makaleler",y["slug"]+".html"),"w",encoding="utf-8").write(makale_sayfasi(y))
    _miso = y["sirala"] if y["sirala"] != "0000-00-00" else ""
    sitemap_ekle("makaleler/" + y["slug"], degisme_tarihi("makaleler/" + y["slug"] + ".md", _miso), "makaleler/" + y["slug"] + ".html", y["baslik"], _miso)
makale_html = ""
if makaleler:
    kk = []
    for y in [m for m in makaleler if not m["dosya"]][:3]:
        img = f'<img class="makale-kucuk" src="gorseller/{e(y["slug"])}.jpg" alt="{e(y["baslik"])}">' if y["resim_var"] else ""
        by = f'Yazar: {e(y["yazar"])}' + (f' · {e(y["tarih"])}' if y["tarih"] else "")
        kk.append(f'<article class="makale-kart">{img}<div class="makale-ozet"><div class="meta">{by}</div><h3><a href="makaleler/{e(y["slug"])}">{e(y["baslik"])}</a></h3><p>{e(y["spot"])}</p><a class="makale-oku" href="makaleler/{e(y["slug"])}">Makaleyi oku →</a></div></article>')
    makale_html = '<section class="makale-bolum" id="makale"><h2>Köşe Yazısı / Makale</h2>' + "".join(kk) + '</section>'
dosya_html = ""
dosyalar = [m for m in makaleler if m["dosya"]]
if dosyalar:
    dk = []
    for y in dosyalar[:2]:
        by = f'Yazar: {e(y["yazar"])}' + (f' · {e(y["kategori"])}' if y["kategori"] else "") + (f' · {e(y["tarih"])}' if y["tarih"] else "")
        pdfl = f' · <a class="makale-oku" href="makaleler/{e(y["slug"])}.pdf" download>PDF indir</a>' if y["pdf_var"] else ""
        dk.append(f'<article class="makale-kart dosya-kart"><div class="makale-ozet"><div class="meta"><span class="dosya-etiket">DOSYA HABER</span> {by}</div><h3><a href="makaleler/{e(y["slug"])}">{e(y["baslik"])}</a></h3><p>{e(y["spot"])}</p><a class="makale-oku" href="makaleler/{e(y["slug"])}">Dosyayı oku →</a>{pdfl}</div></article>')
    dosya_html = '<section class="makale-bolum dosya-bolum" id="dosya"><h2>Dosya Haber</h2>' + "".join(dk) + '</section>'
yil = datetime.date.today().year
sayfa = f'''<!DOCTYPE html>
<html lang="tr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
{seo_head("Diojen News - Dünya, ekonomi, spor, teknoloji ve kültür haberleri", VARSAYILAN_ACIKLAMA, "", "", "website", None,
  [dict(jsonld_yayinci(), **{"@context":"https://schema.org"}), {"@context":"https://schema.org","@type":"WebSite","name":YAYIN_ADI,"url":SITE+"/","inLanguage":"tr","publisher":jsonld_yayinci()}], tam_baslik=True)}
<link rel="stylesheet" href="styles.css">
</head>
<body>
<div class="container" id="ust">
<header class="header"><h1>Diojen <span>News</span></h1><div class="logo">D</div></header>
<nav class="navbar">{nav}</nav>
{piyasa_html}
<div class="content">
<aside class="sidebar"><h2>Kategoriler</h2><ul>{yan}</ul></aside>
<main class="main-content">{man}{dosya_html}{makale_html}{"".join(bol)}</main>
</div>
<footer class="footer"><p>&copy; {yil} Diojen News. Tüm hakları saklıdır. Son güncelleme: {datetime.datetime.now().strftime("%d.%m.%Y %H:%M")}</p></footer>
</div>
<script>
{piyasa_js}
</script>
</body>
</html>'''
open(os.path.join(base,"DiojenNews.html"),"w",encoding="utf-8").write(sayfa)
# "/" gercek ana sayfayi sunsun (eskiden meta-refresh idi); DiojenNews.html de calismaya devam eder, ikisinin canonical'i https://diojennews.com/
open(os.path.join(base,"index.html"),"w",encoding="utf-8").write(sayfa)
sitemap_ekle("", datetime.date.today().isoformat(), "DiojenNews.html")
sitemaplari_yaz()
print("uretildi")
