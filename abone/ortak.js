// Ortak yardımcılar (muhabir + editör). Yalnız publishable anahtar kullanılır.
window.DN = (function(){
  const esc = s => String(s ?? "").replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
  const DURUM = {isleniyor:["İşleniyor","#f4a261"],editor_bekliyor:["Editör bekliyor","#3a86ff"],iade:["İade edildi","#e63946"],yayinda:["Yayında","#0aa37f"],taslak:["Taslak","#8d99ae"]};
  const durumRozet = d => `<span class="rozet-t" style="background:${(DURUM[d]||["",""])[1]||"#999"}">${esc((DURUM[d]||[d])[0])}</span>`;
  const DEMO = (new URLSearchParams(location.search).has("demo") && ["localhost","127.0.0.1"].includes(location.hostname));
  const sb = DEMO ? null : supabase.createClient(ABONE_AYAR.url, ABONE_AYAR.anahtar);
  async function oturum(rolGerekli, $){
    if (DEMO) return { email: "demo@ornek", id: "demo" };
    const { data: { session } } = await sb.auth.getSession();
    if (!session) return null;
    const { data } = await sb.rpc("rolum");
    if (data !== rolGerekli) { $("durum").textContent = `Bu sayfa için "${rolGerekli}" yetkisi gerekiyor.`; return false; }
    return session.user;
  }
  function girisBagla($){
    $("gonder").onclick = async () => { const email = $("eposta").value.trim(); if (!email) return;
      const { error } = await sb.auth.signInWithOtp({ email, options: { emailRedirectTo: location.origin + location.pathname, shouldCreateUser: false } });
      $("giris-mesaj").textContent = error ? "Gönderilemedi: " + error.message : "Bağlantı gönderildi."; };
  }
  return { esc, durumRozet, DEMO, sb, oturum, girisBagla };
})();
