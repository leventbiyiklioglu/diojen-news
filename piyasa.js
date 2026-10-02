/* Diojen News - canlı piyasa şeridi (istemci tarafı, anahtarsız, CORS'a açık kaynaklar).
   Hiçbir değer sabit yazılmaz; veri alınamazsa "veri alınamadı" gösterilir. */
(function (root) {
  "use strict";
  var ARALIK_MS = 60000, ZAMAN_ASIMI_MS = 10000, ESKI_DK = 30;
  var URL = {
    tg4: "https://finans.truncgil.com/v4/today.json",
    tg3: "https://finans.truncgil.com/today.json",
    er: "https://open.er-api.com/v6/latest/USD",
    gold: "https://api.gold-api.com/price/XAU",
    cb: "https://api.coinbase.com/v2/prices/BTC-USD/spot",
    bn: "https://data-api.binance.vision/api/v3/ticker/price?symbol=BTCUSDT",
    cp: "https://api.coinpaprika.com/v1/tickers/btc-bitcoin"
  };
  var OUNCE_GRAM = 31.1034768;

  function trSayi(s) { // "6.550,33" | "$4.146,56" | "%-0,74" -> sayı
    if (typeof s === "number") return s;
    if (typeof s !== "string") return NaN;
    var t = s.replace(/[^0-9,.\-]/g, "");
    if (t.indexOf(",") >= 0) t = t.replace(/\./g, "").replace(",", ".");
    return parseFloat(t);
  }
  function gecerli(x) { return typeof x === "number" && isFinite(x) && x > 0; }
  function sayiVeya(x) { return typeof x === "number" && isFinite(x) ? x : null; }

  function pad(n) { return (n < 10 ? "0" : "") + n; }
  function istanbulParcalar(d) { // Date -> {g,a,y,sa,dk}
    var f = new Intl.DateTimeFormat("tr-TR", { timeZone: "Europe/Istanbul", day: "2-digit", month: "2-digit", year: "numeric", hour: "2-digit", minute: "2-digit", hour12: false });
    var o = {};
    f.formatToParts(d).forEach(function (p) { o[p.type] = p.value; });
    return { g: o.day, a: o.month, y: o.year, sa: o.hour === "24" ? "00" : o.hour, dk: o.minute };
  }
  function zamanEtiketi(d, simdi) { // bugünse "HH:MM", değilse "dd.mm HH:MM" (TSİ)
    var p = istanbulParcalar(d), b = istanbulParcalar(simdi || new Date());
    var saat = p.sa + ":" + p.dk;
    return (p.g === b.g && p.a === b.a && p.y === b.y) ? saat : p.g + "." + p.a + " " + saat;
  }
  function trYerelZaman(s) { // "2026-10-02 22:12:01" (İstanbul saati, UTC+3) -> Date
    var m = /^(\d{4})-(\d{2})-(\d{2})[ T](\d{2}):(\d{2}):(\d{2})/.exec(s || "");
    if (!m) return null;
    return new Date(Date.UTC(+m[1], +m[2] - 1, +m[3], +m[4] - 3, +m[5], +m[6]));
  }

  // Her sağlayıcı: async (get) => {deger, degisim|null, zaman:Date|null, kaynak}
  var tg4 = function (anahtar, kaynakAdi) {
    return function (get) {
      return get(URL.tg4).then(function (d) {
        var o = d && d[anahtar], v = o && sayiVeya(o.Selling);
        if (!gecerli(v)) throw new Error("tg4 " + anahtar + " yok/0");
        return { deger: v, degisim: sayiVeya(o.Change), zaman: trYerelZaman(d.Update_Date), kaynak: "Truncgil Finans" };
      });
    };
  };
  var tg3 = function (anahtar, kaynakAdi) {
    return function (get) {
      return get(URL.tg3).then(function (d) {
        var o = d && d[anahtar], v = o && trSayi(o["Satış"]);
        if (!gecerli(v)) throw new Error("tg3 " + anahtar + " yok/0");
        return { deger: v, degisim: sayiVeya(trSayi(o["Değişim"])), zaman: trYerelZaman(d.Update_Date), kaynak: "Truncgil Finans (yedek uç nokta)" };
      });
    };
  };
  function erRates(get) {
    return get(URL.er).then(function (d) {
      if (!d || d.result !== "success" || !d.rates) throw new Error("er-api");
      return d;
    });
  }
  var erUsd = function (get) {
    return erRates(get).then(function (d) {
      if (!gecerli(d.rates.TRY)) throw new Error("er TRY");
      return { deger: d.rates.TRY, degisim: null, zaman: new Date(d.time_last_update_unix * 1000), kaynak: "ExchangeRate-API (open.er-api.com)" };
    });
  };
  var erEur = function (get) {
    return erRates(get).then(function (d) {
      if (!gecerli(d.rates.TRY) || !gecerli(d.rates.EUR)) throw new Error("er EUR");
      return { deger: d.rates.TRY / d.rates.EUR, degisim: null, zaman: new Date(d.time_last_update_unix * 1000), kaynak: "ExchangeRate-API (open.er-api.com)" };
    });
  };
  var goldOns = function (get) {
    return get(URL.gold).then(function (d) {
      if (!d || !gecerli(d.price)) throw new Error("gold-api");
      return { deger: d.price, degisim: null, zaman: d.updatedAt ? new Date(d.updatedAt) : null, kaynak: "gold-api.com" };
    });
  };
  var gramHesap = function (get) { // ons (USD) x USD/TRY / 31,1035 -- hesaplanan değer, son çare
    return Promise.all([goldOns(get), erUsd(get)]).then(function (r) {
      var z = [r[0].zaman, r[1].zaman].filter(Boolean).sort(function (a, b) { return a - b; })[0] || null;
      return { deger: r[0].deger * r[1].deger / OUNCE_GRAM, degisim: null, zaman: z, kaynak: "gold-api.com × ExchangeRate-API (hesaplanan)" };
    });
  };
  var btcCoinbase = function (get) {
    return get(URL.cb).then(function (d) {
      var v = d && d.data && parseFloat(d.data.amount);
      if (!gecerli(v)) throw new Error("coinbase");
      return { deger: v, degisim: null, zaman: null, kaynak: "Coinbase" };
    });
  };
  var btcBinance = function (get) {
    return get(URL.bn).then(function (d) {
      var v = d && parseFloat(d.price);
      if (!gecerli(v)) throw new Error("binance");
      return { deger: v, degisim: null, zaman: null, kaynak: "Binance (BTC/USDT)" };
    });
  };
  var btcPaprika = function (get) {
    return get(URL.cp).then(function (d) {
      var q = d && d.quotes && d.quotes.USD, v = q && q.price;
      if (!gecerli(v)) throw new Error("coinpaprika");
      return { deger: v, degisim: sayiVeya(q.percent_change_24h), zaman: d.last_updated ? new Date(d.last_updated) : null, kaynak: "CoinPaprika" };
    });
  };

  var ENSTRUMANLAR = [
    { id: "usdtry", ad: "USD/TRY", birim: "₺", kaynaklar: [tg4("USD"), tg3("USD"), erUsd], ondalik: 4 },
    { id: "eurtry", ad: "EUR/TRY", birim: "₺", kaynaklar: [tg4("EUR"), tg3("EUR"), erEur], ondalik: 4 },
    { id: "gram", ad: "Gram Altın", birim: "₺", kaynaklar: [tg4("GRA"), tg3("gram-altin"), gramHesap], ondalik: 2 },
    { id: "ons", ad: "Ons Altın", birim: "$", kaynaklar: [goldOns, tg3("ons")], ondalik: 2 },
    { id: "bist", ad: "BIST 100", birim: "", kaynaklar: [tg4("XU100")], ondalik: 2 },
    { id: "brent", ad: "Brent Petrol", birim: "$", kaynaklar: [tg4("BRENT")], ondalik: 2 },
    { id: "btc", ad: "Bitcoin", birim: "$", kaynaklar: [btcCoinbase, btcBinance, btcPaprika], ondalik: 0 }
  ];

  function fetchTek(url, fetchFn) {
    var ac = (typeof AbortController !== "undefined") ? new AbortController() : null;
    var t = ac ? setTimeout(function () { ac.abort(); }, ZAMAN_ASIMI_MS) : null;
    return fetchFn(url, { cache: "no-store", signal: ac ? ac.signal : undefined }).then(function (r) {
      if (!r.ok) throw new Error("HTTP " + r.status);
      return r.json();
    }).then(function (j) { clearTimeout(t); return j; }, function (e) { clearTimeout(t); throw e; });
  }
  // Kaynak dosyası dakika başında yeniden yazılırken boş/yarım dönebiliyor: bir kez yeniden dene.
  function fetchJSON(url, fetchFn) {
    return fetchTek(url, fetchFn).then(null, function () {
      return new Promise(function (ok) { setTimeout(ok, 1500); }).then(function () { return fetchTek(url, fetchFn); });
    });
  }

  // Bir enstrüman için kaynakları sırayla dener (yedekli); ilk geçerli sonucu döndürür.
  function coz(ens, get) {
    var i = 0;
    function dene() {
      if (i >= ens.kaynaklar.length) return Promise.resolve(null);
      var k = ens.kaynaklar[i++];
      return k(get).then(function (r) { return r; }, dene);
    }
    return dene();
  }

  function guncelle(fetchFn) {
    var hafiza = {};
    var get = function (url) { return hafiza[url] || (hafiza[url] = fetchJSON(url, fetchFn)); };
    return Promise.all(ENSTRUMANLAR.map(function (e) {
      return coz(e, get).then(function (r) { return { ens: e, sonuc: r }; });
    }));
  }

  function sayiBicim(v, ondalik) {
    return v.toLocaleString("tr-TR", { minimumFractionDigits: ondalik, maximumFractionDigits: ondalik });
  }

  function render(doc, sonuclar, simdi) {
    sonuclar.forEach(function (x) {
      var el = doc.getElementById("pz-" + x.ens.id);
      if (!el) return;
      var v = el.querySelector(".pz-deger"), c = el.querySelector(".pz-deg"), k = el.querySelector(".pz-kaynak");
      var r = x.sonuc;
      el.className = "pz";
      if (!r) {
        v.textContent = "veri alınamadı"; c.textContent = ""; k.textContent = "kaynaklar geçerli veri döndürmedi";
        el.className = "pz yok"; return;
      }
      v.textContent = x.ens.birim === "₺" ? sayiBicim(r.deger, x.ens.ondalik) + " ₺" : (x.ens.birim ? x.ens.birim : "") + sayiBicim(r.deger, x.ens.ondalik);
      if (r.degisim === null) { c.textContent = ""; }
      else {
        var yon = r.degisim > 0 ? "▲" : (r.degisim < 0 ? "▼" : "■");
        c.textContent = yon + " %" + sayiBicim(Math.abs(r.degisim), 2);
        el.className += r.degisim > 0 ? " yukari" : (r.degisim < 0 ? " asagi" : "");
      }
      var z = r.zaman ? zamanEtiketi(r.zaman, simdi) + " TSİ" : "alındı " + zamanEtiketi(simdi, simdi) + " TSİ";
      var eski = r.zaman && (simdi - r.zaman) > ESKI_DK * 60000;
      k.textContent = r.kaynak + " · " + z + (eski ? " (eski veri)" : "");
    });
    var s = doc.getElementById("piyasa-son");
    if (s) {
      var tamam = sonuclar.filter(function (x) { return x.sonuc; }).length;
      var p = istanbulParcalar(simdi);
      s.textContent = "Son kontrol: " + p.sa + ":" + p.dk + " TSİ · " + tamam + "/" + sonuclar.length + " enstrüman alındı · her 60 sn'de yenilenir";
    }
  }

  function baslat(doc, fetchFn) {
    var calisiyor = false;
    function tur() {
      if (calisiyor) return;
      calisiyor = true;
      guncelle(fetchFn).then(function (s) { render(doc, s, new Date()); }, function () { /* sessiz */ })
        .then(function () { calisiyor = false; });
    }
    tur();
    setInterval(function () { if (!doc.hidden) tur(); }, ARALIK_MS);
    doc.addEventListener("visibilitychange", function () { if (!doc.hidden) tur(); });
  }

  var api = { trSayi: trSayi, trYerelZaman: trYerelZaman, zamanEtiketi: zamanEtiketi, guncelle: guncelle, render: render, ENSTRUMANLAR: ENSTRUMANLAR, baslat: baslat };
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  else if (typeof document !== "undefined" && typeof fetch === "function") baslat(document, fetch.bind(root));
})(typeof window !== "undefined" ? window : globalThis);
