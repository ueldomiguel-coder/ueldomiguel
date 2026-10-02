// Menu lateral (árvore com grupos) e busca por setores e documentos.
// Os dados vêm de assets/nav.js (gerado por tools/build.py).
const mem = (() => { try { return JSON.parse(window.name || "{}") || {}; } catch(e){ return {}; } })();
const flush = () => { try { window.name = JSON.stringify(mem); } catch(e){} };
const store = {
  get(k, s){ try { const v = (s ? sessionStorage : localStorage).getItem(k); if (v !== null) return v; } catch(e){} return k in mem ? mem[k] : null; },
  set(k, v, s){ mem[k] = v; flush(); try { (s ? sessionStorage : localStorage).setItem(k, v); } catch(e){} },
  del(k, s){ delete mem[k]; flush(); try { (s ? sessionStorage : localStorage).removeItem(k); } catch(e){} }
};
const NAV = window.NAV || [], SEARCH = window.SEARCH || [];
const SLUG = document.body.dataset.slug;
const norm = t => t.normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase();
const el = (tag, cls, txt) => { const e = document.createElement(tag); if (cls) e.className = cls; if (txt) e.textContent = txt; return e; };

const openSet = () => { try { return JSON.parse(store.get("rvs_nav_open", true)) || []; } catch(e){ return []; } };
const saveOpen = (s, o) => { const l = openSet().filter(x => x !== s); if (o) l.push(s); store.set("rvs_nav_open", JSON.stringify(l), true); };

function buildTree() {
  const root = document.getElementById("navList");
  const stack = [{ d: -1, ul: root }];
  NAV.forEach((it, i) => {
    const next = NAV[i + 1], hasKids = next && next.d > it.d;
    while (stack[stack.length - 1].d >= it.d) stack.pop();
    const li = el("li"), row = el("div", "row-nav"), a = el("a", "", it.t);
    a.href = it.h; if (it.s === SLUG) a.setAttribute("aria-current", "page");
    row.appendChild(a); li.appendChild(row);
    stack[stack.length - 1].ul.appendChild(li);
    if (hasKids) {
      const ul = el("ul"), b = el("button", "tog"); b.type = "button"; b.setAttribute("aria-label", "Expandir " + it.t);
      b.innerHTML = '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round"><path d="m9 6 6 6-6 6"/></svg>';
      row.appendChild(b); li.appendChild(ul); li.classList.add("grp");
      const open = SLUG === it.s || SLUG.startsWith(it.s + "/") || openSet().includes(it.s);
      li.classList.toggle("open", open); b.setAttribute("aria-expanded", open);
      b.addEventListener("click", () => { const o = li.classList.toggle("open"); b.setAttribute("aria-expanded", o); saveOpen(it.s, o); });
      stack.push({ d: it.d, ul });
    }
  });
}
buildTree();

// Mantém a posição do menu lateral ao trocar de página (cada página é um arquivo separado).
// A rolagem só pode ser aplicada depois que o site é liberado pelo login (antes, o menu está oculto).
let navRestored = false;
function restoreNav() {
  const sb = document.getElementById("sidebar"); if (!sb || navRestored) return; navRestored = true;
  const saved = store.get("rvs_nav_scroll", true);
  if (saved !== null && !isNaN(+saved)) sb.scrollTop = +saved;
  else { const cur = sb.querySelector("[aria-current]"); if (cur) { const r = cur.getBoundingClientRect(), s = sb.getBoundingClientRect(); if (r.top < s.top || r.bottom > s.bottom) sb.scrollTop = cur.offsetTop - sb.clientHeight / 2; } }
}
(function listenSidebarScroll() {
  const sb = document.getElementById("sidebar"); if (!sb) return;
  const save = () => { if (navRestored) store.set("rvs_nav_scroll", String(sb.scrollTop), true); };
  sb.addEventListener("scroll", save, { passive: true });
  window.addEventListener("pagehide", save);
  sb.addEventListener("click", save, true);
})();

const input = document.getElementById("search"), wrap = document.getElementById("navWrap"), results = document.getElementById("results");
const LABEL = { file: "Documento", folder: "Pasta", form: "Formulário", chart: "Painel", play: "Vídeo", cal: "Agenda", link: "Link", phone: "Telefone" };
input.addEventListener("input", () => {
  const q = norm(input.value.trim());
  if (!q) { results.hidden = true; wrap.hidden = false; return; }
  const words = q.split(/\s+/);
  const hit = s => words.every(w => norm(s).includes(w));
  const pages = NAV.filter(n => hit(n.t)).slice(0, 12);
  const docs = SEARCH.filter(d => hit(d.n + " " + d.p)).slice(0, 40);
  results.innerHTML = ""; wrap.hidden = true; results.hidden = false;
  if (!pages.length && !docs.length) { results.appendChild(el("p", "nav-empty", "Nada encontrado.")); return; }
  if (pages.length) { results.appendChild(el("div", "nav-title", "Setores")); const ul = el("ul", "res"); pages.forEach(n => { const li = el("li"), a = el("a", "", n.t); a.href = n.h; li.appendChild(a); ul.appendChild(li); }); results.appendChild(ul); }
  if (docs.length) {
    results.appendChild(el("div", "nav-title", "Documentos" + (docs.length === 40 ? " (primeiros 40)" : "")));
    const ul = el("ul", "res");
    docs.forEach(d => { const li = el("li"), a = el("a"); a.href = d.u; a.target = "_blank"; a.rel = "noopener";
      a.appendChild(el("span", "r-t", d.n)); a.appendChild(el("span", "r-s", (LABEL[d.k] || "Link") + " · " + d.p)); li.appendChild(a); ul.appendChild(li); });
    results.appendChild(ul);
  }
});

const side = document.getElementById("sidebar"), btn = document.getElementById("menuBtn"), scrim = document.getElementById("scrim");
const toggle = open => { side.classList.toggle("open", open); scrim.hidden = !open; btn.setAttribute("aria-expanded", open); };
btn.addEventListener("click", () => toggle(!side.classList.contains("open")));
scrim.addEventListener("click", () => toggle(false));
document.addEventListener("keydown", e => { if (e.key === "Escape") toggle(false); });

// ---- Simulação de acesso restrito (somente demonstração; não protege nada de verdade) ----
const $ = id => document.getElementById(id);
const KEY_LIST = "rvs_emails", KEY_SESSION = "rvs_sessao", ADMIN_PASS = "admin";

const getList = () => { try { const l = JSON.parse(store.get(KEY_LIST)); if (Array.isArray(l) && l.length) return l; } catch(e){} return ["ueldomiguel@gmail.com"]; };
const saveList = l => store.set(KEY_LIST, JSON.stringify(l));
const root = document.documentElement;
function entrar(mail){
  mail = mail.trim().toLowerCase();
  if (!getList().includes(mail)) { const e = $("gateErr"); e.textContent = "Acesso não autorizado: " + mail + " não está na lista de servidores."; e.hidden = false; return; }
  store.set(KEY_SESSION, mail, true); mostrar(mail);
}
function mostrar(mail){ registrar(mail); root.classList.remove("locked"); restoreNav(); $("userBox").hidden = false; $("userMail").textContent = mail; $("gateErr").hidden = true; }
function sair(){ store.del(KEY_SESSION, true); root.classList.add("locked"); $("userBox").hidden = true; }
document.querySelectorAll(".acct").forEach(b => b.addEventListener("click", () => entrar(b.dataset.mail)));
$("otherForm").addEventListener("submit", e => { e.preventDefault(); entrar($("otherMail").value); });
$("logoutBtn").addEventListener("click", sair);
function renderAdmin(){
  const ul = $("admList"); ul.innerHTML = "";
  getList().forEach(m => { const li = document.createElement("li"), s = document.createElement("span"), b = document.createElement("button");
    s.textContent = m; b.textContent = "Remover"; b.type = "button";
    b.addEventListener("click", () => { const l = getList().filter(x => x !== m); if (l.length) { saveList(l); renderAdmin(); } });
    li.append(s, b); ul.appendChild(li); });
}
const modal = $("adminModal");
$("adminBtn").addEventListener("click", () => { $("admLogin").hidden = false; $("admPanel").hidden = true; $("admPass").value = ""; $("admErr").hidden = true; modal.hidden = false; $("admPass").focus(); });
$("admClose").addEventListener("click", () => modal.hidden = true);
modal.addEventListener("click", e => { if (e.target === modal) modal.hidden = true; });
$("admLogin").addEventListener("submit", e => { e.preventDefault();
  if ($("admPass").value === ADMIN_PASS) { $("admLogin").hidden = true; $("admPanel").hidden = false; renderAdmin(); } else $("admErr").hidden = false; });
$("admAdd").addEventListener("submit", e => { e.preventDefault(); const m = $("admMail").value.trim().toLowerCase(), l = getList();
  if (m && !l.includes(m)) { l.push(m); saveList(l); renderAdmin(); } $("admMail").value = ""; });
document.addEventListener("keydown", e => { if (e.key === "Escape") modal.hidden = true; });

// Copiar e-mail de contato
const cp = document.getElementById("copyMail");
if (cp) cp.addEventListener("click", async () => {
  const t = cp.dataset.mail, old = cp.textContent;
  try { await navigator.clipboard.writeText(t); cp.textContent = "E-mail copiado"; }
  catch (e) { const r = document.createRange(), el = document.querySelector(".mail"); r.selectNodeContents(el); const s = getSelection(); s.removeAllRanges(); s.addRange(r); cp.textContent = "Selecionado: use Ctrl+C"; }
  setTimeout(() => cp.textContent = old, 2200);
});

// ---- Contagem de acessos (simulação: salva só neste navegador) ----
const KEY_ACC = "rvs_acessos";
const getAcc = () => { try { const l = JSON.parse(store.get(KEY_ACC)); return Array.isArray(l) ? l : []; } catch(e){ return []; } };
const saveAcc = l => store.set(KEY_ACC, JSON.stringify(l.slice(-5000)));
let registrado = false;
function registrar(mail){ if (registrado) return; registrado = true; const l = getAcc(); l.push({ t: Date.now(), s: SLUG, u: mail }); saveAcc(l); }
const pageTitle = s => (NAV.find(n => n.s === s) || { t: s }).t;
const dayKey = t => { const d = new Date(t); return d.getFullYear() + "-" + String(d.getMonth() + 1).padStart(2, "0") + "-" + String(d.getDate()).padStart(2, "0"); };
const fmtDT = t => new Date(t).toLocaleString("pt-BR", { day: "2-digit", month: "2-digit", hour: "2-digit", minute: "2-digit" });
function rank(ol, entries, total) {
  ol.innerHTML = "";
  if (!entries.length) { ol.appendChild(el("li", "empty", "Sem dados ainda.")); return; }
  const max = entries[0][1];
  entries.slice(0, 8).forEach(([name, n]) => {
    const li = el("li"), top = el("div", "rk"), nm = el("span", "nm", name), ct = el("span", "ct", String(n)), bar = el("div", "bar"), fill = el("i");
    fill.style.width = Math.max(4, Math.round(n / max * 100)) + "%"; bar.appendChild(fill);
    top.append(nm, ct); li.append(top, bar); ol.appendChild(li);
  });
}
function renderAcc() {
  const l = getAcc(), now = Date.now(), today = dayKey(now), DAY = 864e5;
  const hoje = l.filter(e => dayKey(e.t) === today).length, sete = l.filter(e => now - e.t < 7 * DAY).length;
  const users = new Set(l.map(e => e.u));
  const st = $("accStats"); st.innerHTML = "";
  [["Hoje", hoje], ["Últimos 7 dias", sete], ["Total", l.length], ["Servidores distintos", users.size]].forEach(([k, v]) => {
    const d = el("div", "stat"); d.append(el("strong", "", v.toLocaleString("pt-BR")), el("span", "", k)); st.appendChild(d); });
  const days = [], counts = {};
  for (let i = 13; i >= 0; i--) { const t = now - i * DAY; days.push(t); counts[dayKey(t)] = 0; }
  l.forEach(e => { const k = dayKey(e.t); if (k in counts) counts[k]++; });
  const mx = Math.max(1, ...Object.values(counts)), bars = $("accBars"); bars.innerHTML = "";
  days.forEach(t => { const k = dayKey(t), n = counts[k], c = el("div", "col");
    c.title = new Date(t).toLocaleDateString("pt-BR") + ": " + n + " acesso" + (n === 1 ? "" : "s");
    const v = el("span", "v", n ? String(n) : ""), b = el("i"); b.style.height = (n ? Math.max(6, Math.round(n / mx * 100)) : 2) + "%";
    const d = el("span", "d", String(new Date(t).getDate()).padStart(2, "0")); c.append(v, b, d); bars.appendChild(c); });
  const by = (f) => { const m = {}; l.forEach(e => { const k = f(e); m[k] = (m[k] || 0) + 1; }); return Object.entries(m).sort((a, b) => b[1] - a[1]); };
  rank($("accPages"), by(e => pageTitle(e.s)), l.length);
  rank($("accUsers"), by(e => e.u), l.length);
  const ul = $("accLast"); ul.innerHTML = "";
  if (!l.length) ul.appendChild(el("li", "empty", "Nenhum acesso registrado ainda."));
  l.slice(-8).reverse().forEach(e => { const li = el("li"); li.append(el("span", "w", fmtDT(e.t)), el("span", "u", e.u), el("span", "p", pageTitle(e.s))); ul.appendChild(li); });
}
document.querySelectorAll(".tab").forEach(b => b.addEventListener("click", () => {
  document.querySelectorAll(".tab").forEach(x => { const on = x === b; x.classList.toggle("on", on); x.setAttribute("aria-selected", on); $(x.dataset.pane).hidden = !on; });
  if (b.dataset.pane === "paneAcc") renderAcc();
}));
$("accDemo").addEventListener("click", () => {
  const l = getAcc(), mails = [...new Set([...getList(), "servidor1@gmail.com", "servidor2@gmail.com", "servidor3@gmail.com", "enfermagem.ubs@gmail.com", "vigilancia.sms@gmail.com"])];
  const pages = NAV.filter(n => n.d <= 1), now = Date.now();
  for (let i = 0; i < 220; i++) { const w = Math.random() < .35 ? pages[Math.floor(Math.random() * 6)] : pages[Math.floor(Math.random() * pages.length)];
    l.push({ t: now - Math.floor(Math.random() * 14 * 864e5), s: w.s, u: mails[Math.floor(Math.random() * mails.length)] }); }
  l.sort((a, b) => a.t - b.t); saveAcc(l); renderAcc();
});
$("accClear").addEventListener("click", () => { saveAcc([]); registrado = false; renderAcc(); });
// ao abrir o painel após a senha, mostrar a aba de acessos
$("admLogin").addEventListener("submit", () => { setTimeout(() => { if (!$("admPanel").hidden) renderAcc(); }, 0); });

// Restaura a sessão só depois que todo o código acima foi inicializado
const atual = store.get(KEY_SESSION, true);
if (atual && getList().includes(atual)) mostrar(atual); else root.classList.add("locked");
