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
