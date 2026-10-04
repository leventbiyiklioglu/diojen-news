/* Diojen News - hisse şeritlerini canlı günceller (Cloudflare Worker -> Yahoo Finance, ~15 dk gecikmeli).
   Worker adresi burada DEĞİL, build.py içindeki HISSE_API sabitinde tek yerde tanımlıdır ve
   .seritlar öğesinin data-api özniteliği olarak gömülür. Hata olursa build zamanı gömülü değerler kalır (sessiz yedek). */
(function (root) {
  "use strict";
  var ARALIK_MS = 60000, ZAMAN_ASIMI_MS = 12000;

  function pad(n) { return (n < 10 ? "0" : "") + n; }
  function parcalar(d) {
    var o = {};
    new Intl.DateTimeFormat("tr-TR", { timeZone: "Europe/Istanbul", day: "2-digit", month: "2-digit", year: "numeric", hour: "2-digit", minute: "2-digit", hour12: false })
      .formatToParts(d).forEach(function (p) { o[p.type] = p.value; });
    return { g: o.day, a: o.month, y: o.year, sa: o.hour === "24" ? "00" : o.hour, dk: o.minute };
  }
  function zamanEtiketi(d, simdi) { // bugünse "HH:MM", değilse "dd.mm.yyyy HH:MM" (TSİ)
    var p = parcalar(d), b = parcalar(simdi);
    var saat = p.sa + ":" + p.dk;
    return (p.g === b.g && p.a === b.a && p.y === b.y) ? saat : p.g + "." + p.a + "." + p.y + " " + saat;
  }
  function sayiTr(v, o) { return v.toLocaleString("tr-TR", { minimumFractionDigits: o, maximumFractionDigits: o }); }
  function gecerli(r) { return r && typeof r.fiyat === "number" && isFinite(r.fiyat) && r.fiyat > 0 && typeof r.deg === "number" && isFinite(r.deg) && typeof r.zaman === "number"; }

  function oge(li, r) { // li.si öğesini yeni veriyle günceller
    var d = r.deg, yuvarla = Math.round(d * 100) / 100, sinif, isaret = "";
    if (yuvarla > 0) { sinif = "ar"; isaret = "+"; } else if (yuvarla < 0) { sinif = "az"; isaret = "\u2212"; } else sinif = "sb";
    li.className = "si " + sinif;
    var sf = li.querySelector(".sf"), sd = li.querySelector(".sd");
    var birim = li.getAttribute("data-b") || "";
    if (sf) sf.textContent = birim + sayiTr(r.fiyat, 2);
    if (sd) sd.textContent = isaret + "%" + sayiTr(Math.abs(d), 2);
  }

  function grupNotu(etiket, veriler, simdi) { // veriler: [{zaman, acik}]
    if (!veriler.length) return null;
    var acik = veriler.filter(function (x) { return x.acik; }).length * 2 > veriler.length;
    var z = Math.max.apply(null, veriler.map(function (x) { return x.zaman; }));
    return etiket + ": " + (acik ? "canlı" : "kapanış") + " " + zamanEtiketi(new Date(z * 1000), simdi);
  }

  function guncelle(doc, veri, simdi) {
    var kok = doc.querySelector(".seritlar");
    if (!kok) return 0;
    var grup = {}, sayi = 0;
    [].forEach.call(kok.querySelectorAll("li.si[data-s]"), function (li) {
      var r = veri[li.getAttribute("data-s")];
      if (!gecerli(r)) return;
      oge(li, r); sayi++;
      var s = li.closest ? li.closest(".serit") : null, k = s ? s.id : "";
      (grup[k] = grup[k] || {})[li.getAttribute("data-s")] = r;
    });
    var notlar = [];
    [["serit-bist30", "BIST 30"], ["serit-abd", "ABD"]].forEach(function (g) {
      if (!grup[g[0]]) return;
      var n = grupNotu(g[1], Object.keys(grup[g[0]]).map(function (k) { return grup[g[0]][k]; }), simdi);
      if (n) notlar.push(n);
    });
    var not = kok.querySelector(".serit-not");
    if (not && notlar.length) not.textContent = "Gecikmeli veri (~15 dk), yatırım tavsiyesi değildir \u00b7 Yahoo Finance \u00b7 " + notlar.join(" \u00b7 ") + " (TSİ) \u00b7 günlük değişim önceki kapanışa göredir \u00b7 her 60 sn'de yenilenir";
    return sayi;
  }

  function cek(url, fetchFn) {
    var ac = (typeof AbortController !== "undefined") ? new AbortController() : null;
    var t = ac ? setTimeout(function () { ac.abort(); }, ZAMAN_ASIMI_MS) : null;
    return fetchFn(url, { signal: ac ? ac.signal : undefined }).then(function (r) {
      if (!r.ok) throw new Error("HTTP " + r.status);
      return r.json();
    }).then(function (j) { clearTimeout(t); return j; }, function (e) { clearTimeout(t); throw e; });
  }

  function baslat(doc, fetchFn) {
    var kok = doc.querySelector(".seritlar");
    var api = kok && kok.getAttribute("data-api");
    if (!api) return;
    var semboller = [], goruldu = {};
    [].forEach.call(kok.querySelectorAll("li.si[data-s]"), function (li) { var s = li.getAttribute("data-s"); if (!goruldu[s]) { goruldu[s] = 1; semboller.push(s); } });
    if (!semboller.length) return;
    var url = api.replace(/\/+$/, "") + "/?s=" + encodeURIComponent(semboller.slice().sort().join(","));
    var calisiyor = false;
    function tur() {
      if (calisiyor) return;
      calisiyor = true;
      cek(url, fetchFn).then(function (j) { if (j && j.veri) guncelle(doc, j.veri, new Date()); }, function () { /* sessiz: gömülü değerler kalır */ })
        .then(function () { calisiyor = false; });
    }
    tur();
    setInterval(function () { if (!doc.hidden) tur(); }, ARALIK_MS);
    doc.addEventListener("visibilitychange", function () { if (!doc.hidden) tur(); });
  }

  var api = { guncelle: guncelle, grupNotu: grupNotu, zamanEtiketi: zamanEtiketi, baslat: baslat };
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  else if (typeof document !== "undefined" && typeof fetch === "function") {
    if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", function () { baslat(document, fetch.bind(root)); });
    else baslat(document, fetch.bind(root));
  }
})(typeof window !== "undefined" ? window : globalThis);
