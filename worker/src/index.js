/* Diojen News - canlı hisse verisi (Yahoo Finance chart uç noktası, ~15 dk gecikmeli).
   GET /hisse            -> sabit liste (BIST 30 + ABD 15)
   GET /?s=THYAO.IS,AAPL -> verilen semboller (en çok 50; ücretsiz katman istek başına 50 alt istek sınırı)
   Yanıt: {"uretildi":<unix>,"veri":{"THYAO.IS":{"fiyat":..,"deg":..,"zaman":<unix>,"acik":true|false}}}
   Önbellek: 60 sn (Cache API) -> Yahoo ve ücretsiz günlük 100k istek sınırı korunur. Salt-okunur genel veri. */
const BIST30 = ["AEFES","AKBNK","ASELS","ASTOR","BIMAS","EKGYO","ENKAI","EREGL","FROTO","GARAN","GUBRF","ISCTR","KCHOL","KRDMD","MGROS","PETKM","PGSUS","SAHOL","SASA","SISE","TAVHL","TCELL","THYAO","TOASO","TRALT","TRMET","TTKOM","TUPRS","VAKBN","YKBNK"];
const ABD = ["AAPL","MSFT","NVDA","AMZN","GOOGL","META","TSLA","JPM","V","NFLX","AMD","BRK-B","AVGO","WMT","COST"];
const SABIT = BIST30.map(s => s + ".IS").concat(ABD);
const MAX_SEMBOL = 50;
const SEMBOL_RE = /^[A-Z0-9][A-Z0-9.\-]{0,14}$/;
const TTL = 60;
const IZINLI_ORIGIN = "https://leventbiyiklioglu.github.io";

function corsBasliklari(istek) {
  const o = istek.headers.get("Origin");
  const h = { "Vary": "Origin", "Access-Control-Allow-Methods": "GET, OPTIONS", "Access-Control-Allow-Headers": "Content-Type", "Access-Control-Max-Age": "86400" };
  if (o === IZINLI_ORIGIN) h["Access-Control-Allow-Origin"] = o;
  else if (o === "null" || o === null) h["Access-Control-Allow-Origin"] = "*"; // file:// (yerel kopya) veya Origin'siz istek
  return h;
}
function json(govde, istek, durum = 200, ek = {}) {
  return new Response(JSON.stringify(govde), { status: durum, headers: { "Content-Type": "application/json; charset=utf-8", "Cache-Control": `public, max-age=${TTL}`, ...ek, ...corsBasliklari(istek) } });
}

async function yahoo(sembol) {
  const url = "https://query2.finance.yahoo.com/v8/finance/chart/" + encodeURIComponent(sembol) + "?interval=1d&range=5d";
  for (let deneme = 0; deneme < 2; deneme++) {
    try {
      const r = await fetch(url, { headers: { "User-Agent": "Mozilla/5.0 (compatible; DiojenNews/1.0)", "Accept": "application/json" }, cf: { cacheTtl: TTL, cacheEverything: true } });
      if (!r.ok) continue;
      const d = (await r.json()).chart.result[0];
      const m = d.meta;
      const fiyat = m.regularMarketPrice, zaman = m.regularMarketTime;
      const kap = ((d.indicators.quote[0] || {}).close || []).filter(c => typeof c === "number");
      const onceki = kap.length >= 2 ? kap[kap.length - 2] : null;
      const deg = onceki > 0 ? (fiyat / onceki - 1) * 100 : m.regularMarketChangePercent;
      if (typeof fiyat !== "number" || !(fiyat > 0) || typeof deg !== "number" || !zaman) return null;
      const p = m.currentTradingPeriod && m.currentTradingPeriod.regular, simdi = Math.floor(Date.now() / 1000);
      const acik = !!(p && simdi >= p.start && simdi < p.end && simdi - zaman < 1800);
      return { fiyat, deg: Math.round(deg * 10000) / 10000, zaman, acik };
    } catch (e) { /* yeniden dene */ }
  }
  return null;
}

export default {
  async fetch(istek, env, ctx) {
    if (istek.method === "OPTIONS") return new Response(null, { status: 204, headers: corsBasliklari(istek) });
    if (istek.method !== "GET" && istek.method !== "HEAD") return json({ hata: "yalnızca GET" }, istek, 405, { "Cache-Control": "no-store" });
    const u = new URL(istek.url);
    let semboller;
    if (u.pathname === "/hisse") semboller = SABIT;
    else if (u.pathname === "/" && u.searchParams.has("s")) {
      semboller = [...new Set(u.searchParams.get("s").toUpperCase().split(",").map(x => x.trim()).filter(Boolean))];
      if (!semboller.length) return json({ hata: "sembol yok" }, istek, 400, { "Cache-Control": "no-store" });
      if (semboller.length > MAX_SEMBOL) return json({ hata: `en çok ${MAX_SEMBOL} sembol` }, istek, 400, { "Cache-Control": "no-store" });
      if (!semboller.every(s => SEMBOL_RE.test(s))) return json({ hata: "geçersiz sembol" }, istek, 400, { "Cache-Control": "no-store" });
      semboller.sort();
    } else return json({ hata: "kullanım: /hisse veya /?s=THYAO.IS,AAPL" }, istek, 404, { "Cache-Control": "no-store" });

    // Önbellek anahtarı: normalize sembol listesi (Origin/başlıklardan bağımsız)
    const anahtar = new Request("https://onbellek.diojen/hisse?s=" + semboller.join(","));
    const onbellek = caches.default;
    let yanit = await onbellek.match(anahtar);
    if (!yanit) {
      const sonuc = await Promise.all(semboller.map(yahoo));
      const veri = {};
      semboller.forEach((s, i) => { if (sonuc[i]) veri[s] = sonuc[i]; });
      const gecerli = Object.keys(veri).length > 0;
      yanit = new Response(JSON.stringify({ uretildi: Math.floor(Date.now() / 1000), veri }), { status: gecerli ? 200 : 502, headers: { "Content-Type": "application/json; charset=utf-8", "Cache-Control": gecerli ? `public, max-age=${TTL}` : "no-store" } });
      if (gecerli) ctx.waitUntil(onbellek.put(anahtar, yanit.clone()));
    }
    const h = new Headers(yanit.headers);
    for (const [k, v] of Object.entries(corsBasliklari(istek))) h.set(k, v);
    return new Response(istek.method === "HEAD" ? null : yanit.body, { status: yanit.status, headers: h });
  }
};
