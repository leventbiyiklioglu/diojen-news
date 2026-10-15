#!/usr/bin/env python3
"""Kalici haber sayfalari (Seda, 15.10.2026).

  /haber/                               tum kategoriler (hub)            -> haber/index.html
  /haber/<kategori>/                    kategori arsivi, en yeni ustte    -> haber/<kategori>/index.html
  /haber/<kategori>/<YYYY-MM-DD>-<slug> tek haber (NewsArticle)         -> haber/<kategori>/<YYYY-MM-DD>-<slug>.html

Kaynak: haberler/<kategori>.json (yazar JSON'lari OKUNUR, asla yazilmaz).
Kayit: haber/index.json (git'te takip edilir). Bir haber bir kez kayda girince JSON'dan dussa bile
sayfasi ve arsiv satiri kalir; hicbir haber sayfasi silinmez. Adres (slug) ilk gorulmede sabitlenir.
Kimlik: (kategori, tarih, baslik). Ozet/kaynak degisirse ayni adreste guncellenir (dateModified).
Sayfalar her build'de kayittan yeniden yazilir ama icerik degismediyse dosyaya dokunulmaz.
Istege bagli "baglam" alani varsa ayri paragraf olarak gosterilir (YONERGE su an baglami ozetin son 1-2 cumlesi olarak istiyor).
"""
import os, json, re, datetime, html
import ozel_sayfalar as O
es = O.es
KOK_DIR = "haber"
H = {}

def _iso(t): return O._iso(t)
def _kayit_yolu(base): return os.path.join(base, KOK_DIR, "index.json")
def _oku_kayit(base):
    try:
        v = json.load(open(_kayit_yolu(base), encoding="utf-8"))
        return v if isinstance(v, list) else []
    except Exception: return []

def kayitlari_guncelle(base, kat_listesi, yukle):
    """JSON'lardaki haberleri kayda ekler/gunceller; {(kat, tarih_iso, baslik): yol} doner."""
    kayit = _oku_kayit(base)
    idx = {(k["kat"], k["tarih"], k["baslik"]): k for k in kayit}
    kullanilan = {k["yol"] for k in kayit}
    bugun = datetime.date.today().isoformat()
    for kat, _ad in kat_listesi:
        for h in yukle(kat).get("haberler", []):
            if not isinstance(h, dict): continue
            baslik = O._s(h.get("baslik")).strip(); iso = _iso(h.get("tarih"))
            if not baslik or not iso or not O._s(h.get("ozet")).strip(): continue
            if iso > bugun: continue  # ileri tarihli haber yayina cikmaz
            alanlar = {"ozet": O._s(h.get("ozet")).strip(), "baglam": O._s(h.get("baglam")).strip(),
                       "kaynak": O._s(h.get("kaynak")).strip(), "kaynak_url": O._s(h.get("kaynak_url")).strip(),
                       "yazar": O._s(_yazar_onbellek(yukle, kat)).strip()}
            k = idx.get((kat, iso, baslik))
            if k is None:
                kok = f"{KOK_DIR}/{kat}/{iso}-{O.slugify(baslik) or 'haber'}"; yol = kok; i = 2
                while yol in kullanilan: yol = f"{kok}-{i}"; i += 1
                k = {"kat": kat, "tarih": iso, "baslik": baslik, "yol": yol, "ilk": bugun, "guncelleme": iso}
                k.update(alanlar); kayit.append(k); idx[(kat, iso, baslik)] = k; kullanilan.add(yol)
            elif any(k.get(a, "") != b for a, b in alanlar.items() if b or a in ("baglam",)):
                for a, b in alanlar.items():
                    if b or a == "baglam": k[a] = b
                k["guncelleme"] = max(bugun, iso)
    for k in kayit:
        if not k.get("baglam"): k.pop("baglam", None)
    kayit.sort(key=lambda k: (k["tarih"], k["yol"]), reverse=True)
    os.makedirs(os.path.join(base, KOK_DIR), exist_ok=True)
    yeni = json.dumps(kayit, ensure_ascii=False, indent=1) + "\n"
    p = _kayit_yolu(base)
    if not os.path.exists(p) or open(p, encoding="utf-8").read() != yeni: open(p, "w", encoding="utf-8").write(yeni)
    H["kayit"] = kayit
    return {(k["kat"], k["tarih"], k["baslik"]): k["yol"] for k in kayit}

_YZ = {}
def _yazar_onbellek(yukle, kat):
    if kat not in _YZ: _YZ[kat] = yukle(kat).get("yazar", "")
    return _YZ[kat]

def haber_yolu(harita, kat, h):
    """Ana sayfa kartlari icin: haberin kalici yolu (yoksa None)."""
    return harita.get((kat, _iso(h.get("tarih")), O._s(h.get("baslik")).strip()))

def _yaz(base, rel_html, yol, baslik, aciklama, govde, jsonld, og_tur="website"):
    """ozel_sayfalar.yaz_sayfa ile ayni iskelet; icerik ayniysa dosyaya dokunmaz (git'te gereksiz fark olmasin)."""
    p = os.path.join(base, rel_html)
    eski = open(p, encoding="utf-8").read() if os.path.exists(p) else None
    O.yaz_sayfa(base, rel_html, yol, baslik, aciklama, govde, jsonld, og_tur, None, "haber-sayfa")
    if eski is not None:
        yeni = open(p, encoding="utf-8").read()
        # yalniz telif yili degistiyse eski dosyayi koru
        if re.sub(r"&copy; \d{4}", "", yeni) == re.sub(r"&copy; \d{4}", "", eski): open(p, "w", encoding="utf-8").write(eski)

def _tr_tarih(iso): return f"{iso[8:10]}.{iso[5:7]}.{iso[0:4]}"

def uret(base, kat_listesi, yardimcilar):
    H.update({k: yardimcilar[k] for k in ("jsonld_haber", "jsonld_koleksiyon", "sitemap_ekle", "kisa_metin")})
    kayit = H.get("kayit", [])
    adlar = dict(kat_listesi)
    for k in kayit:
        ad = adlar.get(k["kat"], k["kat"]); kok = "../../"
        ozet = "".join(f"<p>{es(p)}</p>" for p in re.split(r"\n\s*\n", k.get("ozet", "")) if p.strip())
        baglam = f'<h2>Bağlam</h2><p>{es(k["baglam"])}</p>' if k.get("baglam") else ""
        kay = ""
        if k.get("kaynak"):
            kay = (f'<a href="{es(k["kaynak_url"])}" target="_blank" rel="noopener">{es(k["kaynak"])} ↗</a>' if k.get("kaynak_url") else es(k["kaynak"]))
            kay = f'<p class="haber-kaynak"><strong>Kaynak:</strong> {kay}</p>'
        meta = " · ".join(x for x in (f'<a href="{kok}{KOK_DIR}/{es(k["kat"])}/">{es(ad)}</a>',
                                      f'Yazar: {es(k["yazar"])}' if k.get("yazar") else "", _tr_tarih(k["tarih"])) if x)
        govde = (f'<p class="makale-geri"><a href="/">← Ana sayfa</a> · <a href="{kok}{KOK_DIR}/{es(k["kat"])}/">{es(ad)} haberleri</a></p>'
                 f'<div class="meta">{meta}</div><h1 class="makale-baslik">{es(k["baslik"])}</h1>'
                 f'<div class="makale-govde">{ozet}{baglam}</div>{kay}'
                 f'<p class="makale-geri alt"><a href="{kok}{KOK_DIR}/{es(k["kat"])}/">← {es(ad)} haber arşivi</a> · <a href="{kok}{KOK_DIR}/">Tüm haberler</a></p>')
        acik = H["kisa_metin"](k.get("ozet", ""), 200)
        ld = H["jsonld_haber"](k["baslik"], k["yol"], k["tarih"], k.get("guncelleme") or k["tarih"], k.get("yazar", ""), acik, None, ad)
        if k.get("kaynak_url"): ld["isBasedOn"] = k["kaynak_url"]
        _yaz(base, k["yol"] + ".html", k["yol"], k["baslik"], acik, govde, ld, "article")
        H["sitemap_ekle"](k["yol"], k.get("guncelleme") or k["tarih"], k["yol"] + ".html", k["baslik"], k["tarih"], zorla=True)
    # kategori arsivleri + hub
    gruplar = {}
    for k in kayit: gruplar.setdefault(k["kat"], []).append(k)
    hub = []
    for kat, ad in kat_listesi:
        ler = gruplar.get(kat)
        if not ler: continue
        yol = f"{KOK_DIR}/{kat}/"
        liste = "".join(f'<li><a href="{es(k["yol"].split("/")[-1])}">{es(k["baslik"])}</a> <span class="meta">{_tr_tarih(k["tarih"])}{" · " + es(k["kaynak"]) if k.get("kaynak") else ""}</span></li>' for k in ler)
        acik = f"Diojen News {ad} haberleri arşivi: {len(ler)} haber, en yenisi üstte."
        govde = f'<p class="makale-geri"><a href="/">← Ana sayfa</a> · <a href="../">Tüm haberler</a></p><h1>{es(ad)} Haberleri</h1><p class="dk-giris">{es(acik)}</p><ul class="kose-liste">{liste}</ul>'
        _yaz(base, f"{KOK_DIR}/{kat}/index.html", yol, f"{ad} Haberleri", acik, govde, H["jsonld_koleksiyon"](f"{ad} Haberleri", yol, acik))
        H["sitemap_ekle"](yol, ler[0].get("guncelleme") or ler[0]["tarih"], f"{KOK_DIR}/{kat}/index.html", zorla=True)
        hub.append(f'<h2><a href="{es(kat)}/">{es(ad)}</a></h2><ul class="kose-liste">' + "".join(
            f'<li><a href="{es(k["yol"][len(KOK_DIR)+1:])}">{es(k["baslik"])}</a> <span class="meta">{_tr_tarih(k["tarih"])}</span></li>' for k in ler[:5])
            + f'</ul><p><a href="{es(kat)}/">Tüm {es(ad)} haberleri ({len(ler)}) →</a></p>')
    if hub:
        acik = "Diojen News haber arşivi: dünya, ekonomi, spor, teknoloji, kültür ve diğer bölümlerin kalıcı haber sayfaları."
        _yaz(base, f"{KOK_DIR}/index.html", f"{KOK_DIR}/", "Haber Arşivi", acik,
             f'<p class="makale-geri"><a href="/">← Ana sayfa</a></p><h1>Haber Arşivi</h1><p class="dk-giris">{es(acik)}</p>{"".join(hub)}',
             H["jsonld_koleksiyon"]("Haber Arşivi", f"{KOK_DIR}/", acik))
        H["sitemap_ekle"](f"{KOK_DIR}/", kayit[0].get("guncelleme") or kayit[0]["tarih"], f"{KOK_DIR}/index.html", zorla=True)
    print(f"haber sayfalari: {len(kayit)} haber, {len(hub)} kategori")
