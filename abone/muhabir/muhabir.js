(async function(){
const $ = id => document.getElementById(id), {esc, durumRozet, DEMO, sb} = DN;
const u = await DN.oturum(["muhabir","editor"], $);
if (u === null) { $("giris").hidden = false; DN.girisBagla($); return; }
if (!u) return;
$("panel").hidden = false;
async function listele(){
  const rows = DEMO ? (await (await fetch("../demo-panel.json")).json()).filter(r => r.sahip === "demo")
    : (await sb.from("abone_yazilar").select("id,slug,baslik,tur,kategori,durum,editor_notu,guncelleme,dosya_yolu").eq("sahip", u.id).order("guncelleme",{ascending:false})).data || [];
  $("liste").innerHTML = rows.map(r => `<div class="kart"><div class="kart-ic">${durumRozet(r.durum)}
    <h3>${esc(r.baslik || r.dosya_yolu?.split("/").pop() || "(işleniyor)")}</h3>
    <div class="ust-bilgi">${esc(r.tur)} · ${esc(r.kategori||"—")} · ${esc((r.guncelleme||"").slice(0,16).replace("T"," "))}</div>
    ${r.editor_notu ? `<p class="onay">Editör notu: ${esc(r.editor_notu)}</p>` : ""}</div></div>`).join("") || "<p>Henüz gönderi yok.</p>";
}
$("yukle").onclick = async () => {
  const f = $("dosya").files[0]; if (!f) return;
  if (!/\.docx$/i.test(f.name) || f.size > 10*1024*1024) { $("yukle-mesaj").textContent = "Yalnız .docx, en fazla 10 MB."; return; }
  if (DEMO) { $("yukle-mesaj").textContent = "Demo: yükleme yapılmadı."; return; }
  const yol = `${u.id}/${Date.now()}-${f.name.replace(/[^\w.-]+/g,"_")}`;
  const up = await sb.storage.from("muhabir-yuklemeleri").upload(yol, f, { contentType: f.type });
  if (up.error) { $("yukle-mesaj").textContent = "Yüklenemedi: " + up.error.message; return; }
  const ins = await sb.from("abone_yazilar").insert({ slug: "yukleme-" + Date.now(), tur: $("tur").value, sahip: u.id, dosya_yolu: yol, durum: "isleniyor" });
  $("yukle-mesaj").textContent = ins.error ? "Kayıt hatası: " + ins.error.message : "Yüklendi. Dönüştürülüp editöre iletilecek.";
  listele();
};
listele();
})();
