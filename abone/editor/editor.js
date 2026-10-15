(async function(){
const $ = id => document.getElementById(id), {esc, durumRozet, DEMO, sb} = DN;
const u = await DN.oturum("editor", $);
if (u === null) { $("giris").hidden = false; DN.girisBagla($); return; }
if (!u) return;
$("panel").hidden = false;
let rows = [], secili = null, filtre = "editor_bekliyor";
const TUR = {"muhabir":"Muhabir","kose":"Köşe","is-dunyasi":"İş Dünyası"};
async function yukle(){
  rows = DEMO ? await (await fetch("../demo-panel.json")).json()
    : (await sb.from("abone_yazilar").select("*").order("guncelleme",{ascending:false})).data || [];
  ciz();
}
function ciz(){
  $("filtre").innerHTML = [["editor_bekliyor","Onay bekleyen"],["iade","İade"],["yayinda","Yayında"],["isleniyor","İşleniyor"]].map(([k,a]) =>
    `<button data-d="${k}" class="${k===filtre?"secili":""}">${a} (${rows.filter(r=>r.durum===k).length})</button>`).join("");
  const l = rows.filter(r => r.durum === filtre);
  $("sira").innerHTML = l.map(r => `<div class="kart ${secili===r.id?"secili":""}" data-id="${r.id}"><div class="kart-ic">${durumRozet(r.durum)} <span class="rozet-t t-${esc(r.tur)}">${esc(TUR[r.tur]||r.tur)}</span>
    <h3 style="font-size:18px">${esc(r.baslik||"(işleniyor)")}</h3><div class="ust-bilgi">${esc(r.yazar)} · ${esc(r.kategori)}</div></div></div>`).join("") || "<p>Kuyruk boş.</p>";
  if (secili == null && l[0]) goster(l[0].id);
}
function goster(id){
  secili = id; const r = rows.find(x => x.id === id); if (!r) return;
  $("onizle").innerHTML = `${durumRozet(r.durum)}<h1 style="font-family:Georgia,serif">${esc(r.baslik)}</h1>
   <p class="ust-bilgi">${esc(r.yazar)} · ${esc(r.kategori)} · ${(r.etiketler||[]).map(e=>"#"+esc(e)).join(" ")}</p>
   <div class="fiyat" style="font-weight:400"><b>Yapay zekâ özeti</b> ${r.ozet_onayli?"":'<span class="onay">(rakam içeriyor — kontrol et)</span>'}<br>${esc(r.ozet)}</div>
   <label><input type="checkbox" id="ozet-ok" ${r.ozet_onayli?"checked":""}> Özeti kontrol ettim, onaylıyorum</label>
   <textarea id="not" placeholder="İade notu (muhabire gider)">${esc(r.editor_notu||"")}</textarea>
   <div class="eylem"><button class="btn yesil" id="onay" style="width:auto">Onayla ve yayına al</button><button class="btn" id="iade" style="width:auto">Notla iade et</button></div>
   <hr style="margin:24px 0;border:0;border-top:1px solid #eee"><div class="yazi"><div class="icerik">${r.icerik_html||""}</div></div>`;
  $("onay").onclick = () => guncelle(r, { durum: "yayinda", ozet_onayli: $("ozet-ok").checked, editor_notu: null });
  $("iade").onclick = () => { const n = $("not").value.trim(); if (!n) { alert("İade için not yaz."); return; } guncelle(r, { durum: "iade", editor_notu: n }); };
  ciz();
}
async function guncelle(r, alan){
  if (DEMO) { Object.assign(r, alan); secili = null; ciz(); return; }
  const { error } = await sb.from("abone_yazilar").update(alan).eq("id", r.id);
  if (error) alert("Hata: " + error.message); else { secili = null; yukle(); }
}
$("sira").addEventListener("click", e => { const k = e.target.closest(".kart"); if (k) goster(+k.dataset.id); });
$("filtre").addEventListener("click", e => { if (e.target.dataset.d) { filtre = e.target.dataset.d; secili = null; ciz(); }});
yukle();
})();
