// Menu do site original (Google Sites). Itens com "sub" são subpáginas.
const SETORES = [
 "Início","Academia da Saúde","ACS - Agentes Comunitários de Saúde","Ambulatório da Dor","Ambulatório de Estimulação Precoce",
 "Ambulatório de Seguimento do RN de Risco","Ambulatório de Pequenos Procedimentos","Almoxarifado","APAE","Cadernos da Atenção Básica",
 "Cadernos de Atenção Domiciliar","CEC - Centro de Especialidades Clínicas","Centro de Saúde da Pessoa Idosa","DAB - Departamento de Atenção Básica",
 ["Mapas"],"DP - Departamento de Pessoal","Encaminha Cachoeirinha","Educação Continuada e Permanente",["Doenças Raras"],"Enfermagem","Equidade","eSUS",
 "Farmácia","Fluxogramas","Gabinete","GERCON","Indicadores - Previne Brasil","IPM","Medicina","NUMESC","Nutrição","Odontologia",["Fluxogramas - Odontologia"],
 "Pessoas com Deficiência (PCD)",["Autismo"],["Documentos para Isenção em Transporte Público Municipal"],["Documentos para Cartão de Estacionamento"],
 "Programa Saúde na Escola",["Guia de Bolso"],["Caderno Temático"],"POPs","Protocolos","Regulação",["Exames Laboratoriais"],"SAE","Tuberculose",
 "Saúde da Criança","Saúde da Mulher",["Notas Técnicas"],["Implanon"],"Saúde Mental",["eMulti"],"Tabagismo","Telefone das Unidades","Telefone dos Setores da SMS",
 "TI - Informática","Transporte","UPA 24h","Vigilância Ambiental","Vigilância em Saúde do Trabalhador - VISAT",["Fichas de Notificação VISAT"],
 "Vigilância Epidemiológica","Vigilância Sanitária","Vacinas","POPs - Vacinas"
];
const ATUAL = "Academia da Saúde";
const list = document.getElementById("navList");
const items = SETORES.map(s => {
  const sub = Array.isArray(s), name = sub ? s[0] : s;
  const li = document.createElement("li"), a = document.createElement("a");
  a.textContent = name; a.href = name === ATUAL ? "#" : "#em-breve"; if (sub) a.className = "sub";
  if (name === ATUAL) a.setAttribute("aria-current", "page");
  li.appendChild(a); list.appendChild(li); return {li, name};
});
const norm = t => t.normalize("NFD").replace(/[̀-ͯ]/g,"").toLowerCase();
const empty = document.getElementById("navEmpty");
document.getElementById("search").addEventListener("input", e => {
  const q = norm(e.target.value.trim()); let n = 0;
  items.forEach(i => { const ok = !q || norm(i.name).includes(q); i.li.hidden = !ok; if (ok) n++; });
  empty.hidden = n > 0;
});
const side = document.getElementById("sidebar"), btn = document.getElementById("menuBtn"), scrim = document.getElementById("scrim");
const toggle = open => { side.classList.toggle("open", open); scrim.hidden = !open; btn.setAttribute("aria-expanded", open); };
btn.addEventListener("click", () => toggle(!side.classList.contains("open")));
scrim.addEventListener("click", () => toggle(false));
document.addEventListener("keydown", e => { if (e.key === "Escape") toggle(false); });

// ---- Simulação de acesso restrito (somente demonstração; não protege nada de verdade) ----
const $ = id => document.getElementById(id);
const KEY_LIST = "rvs_emails", KEY_SESSION = "rvs_sessao", ADMIN_PASS = "admin";
const store = {
  get(k, s){ try { return (s ? sessionStorage : localStorage).getItem(k); } catch(e){ return null; } },
  set(k, v, s){ try { (s ? sessionStorage : localStorage).setItem(k, v); } catch(e){} },
  del(k, s){ try { (s ? sessionStorage : localStorage).removeItem(k); } catch(e){} }
};
const getList = () => { try { const l = JSON.parse(store.get(KEY_LIST)); if (Array.isArray(l) && l.length) return l; } catch(e){} return ["ueldomiguel@gmail.com"]; };
const saveList = l => store.set(KEY_LIST, JSON.stringify(l));
const root = document.documentElement;
function entrar(mail){
  mail = mail.trim().toLowerCase();
  if (!getList().includes(mail)) { const e = $("gateErr"); e.textContent = "Acesso não autorizado: " + mail + " não está na lista de servidores."; e.hidden = false; return; }
  store.set(KEY_SESSION, mail, true); mostrar(mail);
}
function mostrar(mail){ root.classList.remove("locked"); $("userBox").hidden = false; $("userMail").textContent = mail; $("gateErr").hidden = true; }
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
const atual = store.get(KEY_SESSION, true);
if (atual && getList().includes(atual)) mostrar(atual); else root.classList.add("locked");

// Copiar e-mail de contato
const cp = document.getElementById("copyMail");
if (cp) cp.addEventListener("click", async () => {
  const t = cp.dataset.mail, old = cp.textContent;
  try { await navigator.clipboard.writeText(t); cp.textContent = "E-mail copiado"; }
  catch (e) { const r = document.createRange(), el = document.querySelector(".mail"); r.selectNodeContents(el); const s = getSelection(); s.removeAllRanges(); s.addRange(r); cp.textContent = "Selecionado: use Ctrl+C"; }
  setTimeout(() => cp.textContent = old, 2200);
});
