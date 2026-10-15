(function(){
const $ = id => document.getElementById(id);
const TUR = {"muhabir":"Muhabir","kose":"Köşe","is-dunyasi":"İş Dünyası"};
const esc = s => String(s ?? "").replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const kapak = y => (y.kapak_url && /^https:\/\//.test(y.kapak_url)) ? y.kapak_url : `img/${TUR[y.tur] ? y.tur : "muhabir"}.jpg`;
const rozet = t => `<span class="rozet-t t-${esc(t)}">${esc(TUR[t]||t)}</span>`;
const DEMO = (new URLSearchParams(location.search).has("demo") && ["localhost","127.0.0.1"].includes(location.hostname));  // yalnız yerel önizleme: örnek veri
let sb = null, yazilar = [], filtre = "";
function goster(...ids){ ["giris","abone-ol","liste","yazi"].forEach(i => $(i).hidden = !ids.includes(i)); }

async function yukle(){
  if (DEMO) { yazilar = (await (await fetch("demo.json")).json()); $("kim2").textContent = "demo@ornek"; ciz(); rota(); return; }
  const { data: { session } } = await sb.auth.getSession();
  if (!session) { goster("giris"); return; }
  $("kim").textContent = $("kim2").textContent = session.user.email;
  const { data: ab } = await sb.from("aboneler").select("abonelik_aktif,bitis_tarihi").maybeSingle();
  const aktif = ab && ab.abonelik_aktif && (!ab.bitis_tarihi || new Date(ab.bitis_tarihi) > new Date());
  if (!aktif) { goster("abone-ol"); return; }
  const { data, error } = await sb.from("abone_yazilar").select("*").order("yayin_tarihi", { ascending: false });
  if (error) { $("durum").textContent = "Yazılar alınamadı."; return; }
  yazilar = data; ciz(); rota();
}
function ciz(){
  $("filtre").innerHTML = ["", "muhabir", "kose", "is-dunyasi"].map(t =>
    `<button data-t="${t}" class="${t===filtre?"secili":""}">${t?TUR[t]:"Tümü"}</button>`).join("");
  $("yazilar").innerHTML = yazilar.filter(y => !filtre || y.tur === filtre).map(y => `
   <a class="kart" href="#${encodeURIComponent(y.slug)}">
    <div class="kapak" style="background-image:url('${esc(kapak(y))}')">${rozet(y.tur)}</div>
    <div class="kart-ic"><div class="ust-bilgi">${esc(y.kategori)} · ${esc(y.yazar)} · ${esc(y.yayin_tarihi)}</div>
    <h3>${esc(y.baslik)}</h3>
    <div class="ozet">${y.ozet_onayli ? esc(y.ozet) : '<span class="onay">Özet editör onayı bekliyor.</span>'}</div>
    <div class="etiketler">${(y.etiketler||[]).map(e=>`<span>#${esc(e)}</span>`).join("")}</div></div></a>`).join("") || "<p>Henüz yazı yok.</p>";
}
function rota(){
  const s = decodeURIComponent(location.hash.slice(1)); const y = yazilar.find(x => x.slug === s);
  if (!y) { goster("liste"); return; }
  // icerik_html yalnız sunucu tarafında (tasnif.py / word_ekle.py) üretilir.
  $("yazi").innerHTML = `<p><a href="#">← Tüm yazılar</a></p><div class="kapak" style="background-image:url('${esc(kapak(y))}')"></div>
    ${rozet(y.tur)} <span class="ust-bilgi">${esc(y.kategori)}</span><h1>${esc(y.baslik)}</h1>
    <p class="ust-bilgi">${esc(y.yazar)} · ${esc(y.yayin_tarihi)}</p><div class="icerik">${y.icerik_html||""}</div>`;
  goster("yazi"); scrollTo(0,0);
}
$("filtre").addEventListener("click", e => { if (e.target.dataset.t !== undefined) { filtre = e.target.dataset.t; ciz(); }});
window.addEventListener("hashchange", rota);
if (!DEMO) {
  sb = supabase.createClient(ABONE_AYAR.url, ABONE_AYAR.anahtar);
  $("gonder").onclick = async () => {
    const email = $("eposta").value.trim(); if (!email) return;
    const { error } = await sb.auth.signInWithOtp({ email, options: { emailRedirectTo: location.origin + location.pathname } });
    $("giris-mesaj").textContent = error ? "Gönderilemedi: " + error.message : "Bağlantı gönderildi, e-postanı kontrol et.";
  };
  document.querySelectorAll(".cikis").forEach(a => a.onclick = async e => { e.preventDefault(); await sb.auth.signOut(); location.hash=""; yukle(); });
  sb.auth.onAuthStateChange(ev => { if (ev === "SIGNED_IN" || ev === "SIGNED_OUT") yukle(); });
}
yukle();
})();
