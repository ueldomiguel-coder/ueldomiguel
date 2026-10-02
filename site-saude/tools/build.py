"""Gera o site estático a partir do JSON extraído do Google Sites.
Uso: build.py <pages.json> <pasta com images.json e imagens baixadas> <pasta de saída do site>"""
import re, json, html, os, sys, unicodedata, urllib.parse
from PIL import Image

PAGES_JSON, RAW, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
D = json.load(open(PAGES_JSON))
P, NAVSRC = D['pages'], D['nav']
HERE = os.path.dirname(os.path.abspath(__file__))
TEMPLATE = open(os.path.join(HERE, 'template.html'), encoding='utf-8').read()
SITE = 'https://sites.google.com/view/saudecachoeirinha'
SITE_NAME = 'Repositório Virtual - Saúde - Cachoeirinha'

# ---------------------------------------------------------------- textos
ACRONYMS = set("""AB ABS ACS AD AG AIDS AIH APAE APS BAAR BVS CAB CAPS CD CDS CEC CEO CER CEVS CGICI CGZV CIAP CNES COREN COVID CP CRIE DAB DAPPS DDA DEDT DFD DIU
DNPM DORT DP DPNI DPS DST DTM DVE DVRT EEI EP ESF ETP FTA GAL GERCON GTIM HB HBV HCV HIV HPJ HTLV ICOM ICOPE IGHAR II III IV IJ ILPI IOS IPI IPM IST ISTS IVCF LFN LT MDDA
MEEM MG MS MSD NASF NR NS NUMESC ODIL OPAS OPM PAIR PAI PCD PCDT PCR PEC PEP PNAB PNAR PNI POP POPS PPD PSE RAPS RN RS SAE SAM SAR SCPA SES SI SIPNI SISCAN SMS SNAP SOAP SUS SVSA DSTS
TARV TEA TI TR TSH UBS UPA VDRL VI VISAT B C D F I J M N R S T W X LGPD CRM CFM CRO DATASUS INCA ESAVI EAPV HGT IM SINAN SISAB""".split())
SPECIAL = {'ESUS': 'eSUS', 'E-SUS': 'e-SUS', 'EMULTI': 'eMulti', 'POPS': 'POPs', '24H': '24h', 'MPOX': 'Mpox', 'DANTS': 'DANTs', 'IOS': 'iOS', 'HBSAG': 'HBsAg', 'E-MAIL': 'e-mail', 'EMAIL': 'e-mail'}
SMALL = {'a','o','as','os','e','de','da','do','das','dos','em','na','no','nas','nos','para','por','com','sem','ao','aos','à','às','um','uma','ou','que','pela','pelo','pelas','pelos','se'}

def smart_title(t):
    letters = [c for c in t if c.isalpha()]
    if not letters or sum(c.isupper() for c in letters) / len(letters) < .7: return t.strip()
    out = []
    for i, w in enumerate(re.split(r'(\s+)', t.strip())):
        if not w.strip(): out.append(w); continue
        m = re.match(r'^([^\wÀ-ÿ]*)(.*?)([^\wÀ-ÿ]*)$', w, re.S)
        pre, core, post = m.groups()
        u = core.upper()
        prev = ''.join(out).lower().rstrip()
        if u in SPECIAL: c = SPECIAL[u]
        elif len(core) == 1 and re.search(r'(hepatite|vitamina|tipo|grupo|classe|fase|anexo|vírus|virus)$', prev): c = u
        elif core.lower() in SMALL and out: c = core.lower()
        elif '/' in core and all(x.lower() in SMALL for x in core.split('/')) and out: c = core.lower()
        elif u in ACRONYMS or re.fullmatch(r'[IVX]{1,4}', u) or any(ch.isdigit() for ch in u): c = u
        elif '(' in pre and ')' in post and len(core) <= 6: c = u
        elif '/' in core and all(len(x) <= 5 for x in core.split('/')) and not any(x.lower() in SMALL for x in core.split('/')): c = u
        elif '-' in core and all(x.upper() in ACRONYMS or any(ch.isdigit() for ch in x) for x in core.split('-')): c = u
        else: c = core.lower().capitalize() if '-' not in core else '-'.join(x.capitalize() for x in core.lower().split('-'))
        out.append(pre + c + post)
    return ''.join(out)

def ascii_slug(t):
    t = unicodedata.normalize('NFKD', t).encode('ascii', 'ignore').decode().lower()
    return re.sub(r'[^a-z0-9]+', '-', t).strip('-')

esc = html.escape

# ---------------------------------------------------------------- páginas e arquivos
HOME = 'início'
files, used = {}, {'index'}
for n in NAVSRC:
    s = n['slug']
    if s == 'tela-inicial': continue
    if s == HOME: files[s] = 'inicio.html'; continue
    base = ascii_slug(s.split('/')[-1]) or 'pagina'
    name = base; k = 2
    while name in used: name = f'{base}-{k}'; k += 1
    used.add(name); files[s] = name + '.html'

def title_of(s):
    if s == HOME: return 'Repositório Virtual de Saúde de Cachoeirinha'
    nt = next(n['navtitle'] for n in NAVSRC if n['slug'] == s)
    return smart_title(nt)

def depth(s): return 0 if s == HOME else s.count('/') - 1

order = [n['slug'] for n in NAVSRC if n['slug'] in files]
children = {s: [] for s in order}
for s in order:
    if s == HOME: continue
    parent = s.rsplit('/', 1)[0] if s.count('/') > 1 else None
    if parent in children: children[parent].append(s)

# ---------------------------------------------------------------- imagens
tokfile = {}
for slug, m in json.load(open(os.path.join(RAW, 'images.json'))).items():
    for tok, f in m.items(): tokfile.setdefault(tok, f)
os.makedirs(os.path.join(OUT, 'assets/img/p'), exist_ok=True)
img_cache = {}
def image(tok, maxw=1100):
    if tok in img_cache: return img_cache[tok]
    src = tokfile.get(tok)
    if not src or not os.path.exists(src): img_cache[tok] = None; return None
    try:
        im = Image.open(src); im.load()
    except Exception: img_cache[tok] = None; return None
    has_alpha = im.mode in ('RGBA', 'LA') or (im.mode == 'P' and 'transparency' in im.info)
    if im.width > maxw: im = im.resize((maxw, round(im.height * maxw / im.width)), Image.LANCZOS)
    name = re.sub(r'[^A-Za-z0-9_-]', '', tok)
    if has_alpha:
        fn = name + '.png'; im.convert('RGBA').save(os.path.join(OUT, 'assets/img/p', fn), optimize=True)
    else:
        fn = name + '.jpg'; im.convert('RGB').save(os.path.join(OUT, 'assets/img/p', fn), quality=78, optimize=True, progressive=True)
    img_cache[tok] = ('assets/img/p/' + fn, im.width, im.height)
    return img_cache[tok]

# ---------------------------------------------------------------- ícones
ICONS = {
 'file': '<path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z"/><path d="M14 3v5h5M9 13h6M9 17h6"/>',
 'folder': '<path d="M3 7a2 2 0 0 1 2-2h4l2 2h8a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>',
 'form': '<rect x="5" y="3" width="14" height="18" rx="2"/><path d="m9 9 1.5 1.5L14 7M9 15h6"/>',
 'chart': '<path d="M4 20V10M10 20V4M16 20v-7M22 20H2"/>',
 'play': '<rect x="3" y="5" width="18" height="14" rx="3"/><path d="m10 9 5 3-5 3z"/>',
 'link': '<path d="M10 14a4 4 0 0 0 5.7 0l3-3a4 4 0 0 0-5.7-5.7l-1 1"/><path d="M14 10a4 4 0 0 0-5.7 0l-3 3a4 4 0 0 0 5.7 5.7l1-1"/>',
 'page': '<path d="M4 6h16M4 12h16M4 18h10"/>',
 'cal': '<rect x="3" y="5" width="18" height="16" rx="2"/><path d="M3 10h18M8 3v4M16 3v4"/>',
 'syringe': '<path d="m18 2 4 4"/><path d="m17 7 3-3"/><path d="M19 9 8.7 19.3c-1 1-2.5 1-3.4 0l-.6-.6c-1-1-1-2.5 0-3.4L15 5"/><path d="m9 11 4 4"/><path d="m5 19-3 3"/><path d="m14 4 6 6"/>',
 'flow': '<rect x="3" y="3" width="7" height="5" rx="1"/><rect x="14" y="10" width="7" height="5" rx="1"/><rect x="3" y="16" width="7" height="5" rx="1"/><path d="M6.5 8v2a2 2 0 0 0 2 2H14M10 18.500h1a3 3 0 0 0 3-3"/>',
 'checklist': '<path d="m4 7 2 2 3-3M4 17l2 2 3-3M12 8h8M12 18h8"/>',
 'clip': '<rect x="8" y="2" width="8" height="4" rx="1"/><path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2M9 12h6M9 16h4"/>',
 'book': '<path d="M4 19.500A2.500 2.500 0 0 1 6.500 17H20V3H6.500A2.500 2.500 0 0 0 4 5.500z"/><path d="M4 19.500V21h16M9 7h6"/>',
 'virus': '<circle cx="12" cy="12" r="4"/><path d="M12 3v3M12 18v3M3 12h3M18 12h3M5.600 5.600l2.100 2.100M16.300 16.300l2.100 2.100M18.400 5.600l-2.100 2.100M7.700 16.300l-2.100 2.100"/>',
 'bug': '<ellipse cx="12" cy="13.500" rx="4" ry="5"/><path d="M12 8.500V5M9.500 6l1 2.500M14.500 6l-1 2.500M8 12H4M16 12h4M8 16H5M16 16h3M9.500 19.500 8 21.500M14.500 19.500l1.500 2"/>',
 'paw': '<circle cx="6" cy="10" r="2"/><circle cx="10" cy="5.500" r="2"/><circle cx="14" cy="5.500" r="2"/><circle cx="18" cy="10" r="2"/><path d="M12 12c-3 0-6 3-6 6 0 2 2 2 3.500 1.500 1.500-.5 3.500-.5 5 0C16 20 18 20 18 18c0-3-3-6-6-6z"/>',
 'lungs': '<path d="M12 4v9M9 11c-3 0-5 3-5 6 0 2 1 3 2.500 3S9 18.500 9 16.500zM15 11c3 0 5 3 5 6 0 2-1 3-2.500 3S15 18.500 15 16.500zM12 8c-2-2-4-1-4 1M12 8c2-2 4-1 4 1"/>',
 'ribbon': '<path d="M12 3c-3 0-5 2-5 4.500 0 2 1.500 3.500 3 5L7 21M12 3c3 0 5 2 5 4.500 0 2-1.500 3.500-3 5L17 21M9.500 13l5-5"/>',
 'brain': '<path d="M9.500 3A3.500 3.500 0 0 0 6 6.500c-2 .5-3 2-3 4 0 1.500.7 2.500 1.800 3.200-.3 1.800.2 3.300 1.700 3.800A3 3 0 0 0 12 19V5.500A2.500 2.500 0 0 0 9.500 3zM14.500 3A3.500 3.500 0 0 1 18 6.500c2 .5 3 2 3 4 0 1.500-.7 2.500-1.800 3.200.3 1.800-.2 3.300-1.700 3.800A3 3 0 0 1 12 19"/>',
 'tooth': '<path d="M7 3C5 3 3 5 3 8c0 4 2 5 2 9 0 2 1 4 2 4s1.500-3 2-5c.4-1.500 1-2 2-2s1.600.5 2 2c.5 2 1 5 2 5s2-2 2-4c0-4 2-5 2-9 0-3-2-5-4-5-2 0-3 1-4 1S9 3 7 3z"/>',
 'heart': '<path d="M20.800 5.600a5 5 0 0 0-7.100 0L12 7.300l-1.700-1.700a5 5 0 0 0-7.100 7.100L12 21l8.800-8.300a5 5 0 0 0 0-7.100z"/>',
 'child': '<circle cx="12" cy="12" r="9"/><path d="M8 14s1.500 2 4 2 4-2 4-2M9 9.500h.01M15 9.500h.01"/>',
 'user': '<circle cx="12" cy="7" r="3.500"/><path d="M5 21a7 7 0 0 1 14 0"/>',
 'access': '<circle cx="12" cy="4.500" r="1.800"/><path d="M5 8.500h14M12 8.500v6l-3 6M12 14.500l3 6"/>',
 'apple': '<path d="M12 7c-2-2-6-1-6 4 0 5 3 9 5 9 .7 0 1-.3 1-.3s.3.3 1 .3c2 0 5-4 5-9 0-5-4-6-6-4zM12 7c0-2 1-3 3-4"/>',
 'dumbbell': '<path d="M6.500 6.500v11M17.500 6.500v11M3 9v6M21 9v6M6.500 12h11"/>',
 'ban': '<circle cx="12" cy="12" r="9"/><path d="M5.600 5.600l12.800 12.800"/>',
 'pill': '<rect x="2" y="8.500" width="20" height="7" rx="3.500" transform="rotate(-40 12 12)"/><path d="m8.700 8.700 6.600 6.600"/>',
 'flask': '<path d="M9 3h6M10 3v6L4.500 19a2 2 0 0 0 1.800 3h11.400a2 2 0 0 0 1.800-3L14 9V3M7.500 15h9"/>',
 'map': '<path d="M9 4 3 6v14l6-2 6 2 6-2V4l-6 2zM9 4v14M15 6v14"/>',
 'grad': '<path d="m2 9 10-5 10 5-10 5zM6 11v5c0 1.500 3 3 6 3s6-1.500 6-3v-5M22 9v6"/>',
 'scale': '<path d="M12 3v18M6 21h12M5 7h14M5 7l-3 7a3 3 0 0 0 6 0zM19 7l-3 7a3 3 0 0 0 6 0z"/>',
 'mail': '<rect x="3" y="5" width="18" height="14" rx="2"/><path d="m3 7 9 6 9-6"/>',
 'ambu': '<path d="M3 17V7a1 1 0 0 1 1-1h9v11M13 9h4l3 4v4h-2M3 17h2M9 17h6"/><circle cx="7" cy="17.500" r="1.500"/><circle cx="17" cy="17.500" r="1.500"/><path d="M8 9v4M6 11h4"/>',
 'idcard': '<rect x="3" y="5" width="18" height="14" rx="2"/><circle cx="9" cy="11" r="2"/><path d="M6 16c.5-1.500 1.500-2 3-2s2.500.5 3 2M15 10h3M15 14h3"/>',
 'monitor': '<rect x="3" y="4" width="18" height="12" rx="2"/><path d="M8 20h8M12 16v4"/>',
 'shield': '<path d="M12 3 4 6v6c0 5 3.500 8 8 9 4.500-1 8-4 8-9V6z"/><path d="m9 12 2 2 4-4"/>',
 'cross': '<path d="M9 3h6v6h6v6h-6v6H9v-6H3V9h6z"/>',
 'drop': '<path d="M12 3s6 6.500 6 11a6 6 0 0 1-12 0c0-4.500 6-11 6-11z"/>',
 'phone': '<path d="M5 4h4l2 5-2.5 1.5a11 11 0 0 0 5 5L15 13l5 2v4a2 2 0 0 1-2 2A16 16 0 0 1 3 6a2 2 0 0 1 2-2z"/>',
}
SPRITE = '<svg width="0" height="0" style="position:absolute" aria-hidden="true"><defs>' + ''.join(
    f'<symbol id="i-{k}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">{v}</symbol>' for k, v in ICONS.items()) + '</defs></svg>'

def kind(h):
    if h.startswith('page:'): return 'page'
    if 'youtube.com' in h or 'youtu.be' in h: return 'play'
    if 'drive.google.com/drive' in h or '/folders/' in h: return 'folder'
    if 'docs.google.com/forms' in h: return 'form'
    if 'spreadsheets' in h or 'lookerstudio' in h or 'datastudio' in h: return 'chart'
    if 'calendar.google' in h: return 'cal'
    if h.startswith('tel:'): return 'phone'
    if 'drive.google.com' in h or 'docs.google.com' in h: return 'file'
    return 'link'


TOPICS = [
 (r'vacin|imuniz|\bpni\b|rotavirus|bcg|pentavalente|antirrabica', 'syringe', 'teal'),
 (r'fluxograma|fluxo\b|fluxos', 'flow', 'blue'),
 (r'covid|corona|influenza|gripal|gripe|sars|mpox|varicela|sarampo|virus|bronquiolite', 'virus', 'red'),
 (r'dengue|chikungunya|zika|mosquito|aedes|arbovir|leptospir|chagas|leishman|esporotric|toxoplasm|zoonose|escorpi|pediculose|mao.pe.boca|conjuntivite', 'bug', 'orange'),
 (r'raiva|animal|canino|felino', 'paw', 'orange'),
 (r'tubercul|pulmon|respirat|oxigen|bilevel|respirador|asma|dpoc|coqueluche', 'lungs', 'teal'),
 (r'\bhiv\b|aids|\bist\b|\bists\b|sifilis|hepatite|htlv|\bprep\b|\bpep\b|preservativo', 'ribbon', 'red'),
 (r'mental|psic|caps\b|autism|\btea\b|depress|ansied|suicid|emulti|multiprofission', 'brain', 'purple'),
 (r'odonto|dent[ai]|bucal|\bceo\b', 'tooth', 'blue'),
 (r'gestante|pre.natal|prenatal|puerper|parto|gravid|perinatal|mulher|mama\b|mamograf|colo do utero|citopatol|implanon|contracep|encarte', 'heart', 'pink'),
 (r'crianca|infantil|pediatr|neonat|\brn\b|estimulacao precoce|puericult', 'child', 'teal'),
 (r'idos[oa]|envelhec|longevidade', 'user', 'amber'),
 (r'deficien|\bpcd\b|acessibil|cadeira de rodas|isencao|estacionamento|\bbpc\b', 'access', 'blue'),
 (r'nutri|aliment|obesidade|diabet|sobrepeso|sisvan|\bdant', 'apple', 'green'),
 (r'atividade fisica|academia|exercicio|pratica corporal', 'dumbbell', 'green'),
 (r'tabag|fumo|cigarro|tabaco', 'ban', 'amber'),
 (r'farmac|medicament|remedio|rename|insulina|fralda|dispensa', 'pill', 'green'),
 (r'exame|laborat|laudo|teste rapido|coleta|resultado|metanol|intoxic', 'flask', 'teal'),
 (r'telefone|contato|ramal|whatsapp|\d{4}-\d{4}', 'phone', 'green'),
 (r'mapa|territor|georref|abrangencia', 'map', 'blue'),
 (r'agenda|reuniao|calendario|cronograma|escala\b|agendamento', 'cal', 'orange'),
 (r'capacita|curso|treinamento|educacao|aula\b|formacao|webinar|palestra|oficina|numesc', 'grad', 'purple'),
 (r'portaria|\blei\b|decreto|resolucao|norma|nota tecnica|nota informativa|legisl|instrucao normativa|deliberac|ordem de servico|lgpd', 'scale', 'amber'),
 (r'memorando|oficio|informe|comunicado|circular|boletim|carta\b', 'mail', 'amber'),
 (r'transporte|ambulanc|samu|\bupa\b|urgencia|emergencia|remocao|veicul', 'ambu', 'red'),
 (r'cartao|carteira|cadastro|\bcns\b|identifica|cracha', 'idcard', 'blue'),
 (r'sistema|e.?sus|sisab|\bipm\b|software|aplicativo|tutorial|informatica|\bti\b|senha|portal|gercon|sisreg|cnes|\bpec\b', 'monitor', 'blue'),
 (r'vigilancia sanitaria|inspec|fiscaliza|alvara|licenca', 'shield', 'teal'),
 (r'planilha|painel|indicador|dashboard|relatorio|previne|estatistic|grafico|monitoramento|looker', 'chart', 'blue'),
 (r'cirurgi|ambulatorio|curativo|ortoped|traumat|tala\b|enfermagem|medicina|clinic|sae\b|especialidade', 'cross', 'red'),
 (r'diarre|agua|hidrata', 'drop', 'blue'),
 (r'cardio|hipertens|infarto|\bavc\b|pressao arterial', 'heart', 'red'),
 (r'checklist|check.list|protocolo|\bpops?\b|procedimento operacional|diretriz|linha de cuidado|orienta|rotina|criterio', 'checklist', 'blue'),
 (r'ficha|notifica|investiga|sinan|formulario|solicita|requisi|termo|modelo', 'clip', 'orange'),
 (r'cartilha|caderno|guia|manual|livro|apostila|material|cartaz|folder|infograf', 'book', 'purple'),
]
TOPICS = [(re.compile(a), b, c) for a, b, c in TOPICS]
KIND_TONE = {'play': 'red', 'folder': 'amber', 'form': 'amber', 'chart': 'blue', 'cal': 'orange', 'file': 'blue', 'link': 'blue', 'page': 'blue', 'phone': 'green'}
def norm_txt(t): return unicodedata.normalize('NFKD', t).encode('ascii', 'ignore').decode().lower()
def topic(text, href=''):
    n = norm_txt(text)
    for rx, ic, tone in TOPICS:
        if rx.search(n): return ic, tone
    k = kind(href)
    return k, KIND_TONE.get(k, 'blue')

def icon(k, size=22): return f'<svg class="ic" width="{size}" height="{size}" aria-hidden="true"><use href="#i-{k}"/></svg>'

def href_of(h):
    if h.startswith('page:'):
        s = h[5:]
        if s == 'tela-inicial': s = HOME
        return files.get(s, '#')
    return h

def attrs_of(h):
    return '' if h.startswith('page:') or h.startswith('#') else ' target="_blank" rel="noopener"'

def fix_inline(h_):
    def rep(m):
        raw = html.unescape(m.group(1)); return 'href="%s"%s' % (esc(href_of(raw), quote=True), attrs_of(raw))
    return re.sub(r'href="([^"]*)"', rep, h_)

# ---------------------------------------------------------------- blocos
ARROW = '<svg class="go" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><path d="M7 17 17 7M8 7h9v9"/></svg>'
CHEV = '<svg class="go" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><path d="m9 6 6 6-6 6"/></svg>'

def card(text, href, thumb=None, k=None):
    ic, tone = (k, KIND_TONE.get(k, 'blue')) if k else topic(text, href); inner = ''
    if thumb:
        im = image(thumb)
        if im: inner = f'<span class="thumb"><img src="{im[0]}" width="{im[1]}" height="{im[2]}" alt="" loading="lazy" decoding="async"></span>'
    has = bool(inner)
    if not inner: inner = f'<span class="ico tone-{tone}">{icon(ic)}</span>'
    cls = 'docc has-thumb' if has else 'docc'
    return f'<a class="{cls}" href="{esc(href_of(href), quote=True)}"{attrs_of(href)}>{inner}<span class="tx">{esc(smart_title(text))}</span>{CHEV if href.startswith("page:") else ARROW}</a>'

def split_cells(raw): return [c.strip() for c in re.split(r'\t+|[  ]{2,}', raw.strip()) if c.strip()]

def render_blocks(blocks, slug):
    out, i, n = [], 0, len(blocks)
    sec_open = False
    cur = {'t': ''}
    def open_sec(title=None):
        nonlocal sec_open
        cur['t'] = title or ''
        if sec_open: out.append('</div></section>')
        out.append('<section class="sec">' + (f'<h2>{esc(smart_title(title))}</h2>' if title else '') + '<div class="sec-body">'); sec_open = True
    open_sec()
    cards = []; gallery = []
    def flush():
        nonlocal cards, gallery
        if cards: out.append('<div class="docs">' + ''.join(cards) + '</div>'); cards = []
        if gallery: out.append('<div class="gallery">' + ''.join(gallery) + '</div>'); gallery = []
    while i < n:
        b = blocks[i]; t = b['t']
        nxt = blocks[i + 1] if i + 1 < n else None
        if t in ('img', 'imglink') and nxt and nxt['t'] == 'btn' and not gallery:
            cards.append(card(nxt['text'], nxt['href'])); i += 2; continue
        if t == 'imglink' and nxt and nxt['t'] == 'p' and len(nxt['text']) <= 60 and not gallery and not b['href'].startswith('#'):
            cards.append(card(nxt['text'], b['href'])); i += 2; continue
        if t == 'btn':
            if gallery: flush()
            cards.append(card(b['text'], b['href'])); i += 1; continue
        if t == 'video':
            if gallery: flush()
            cards.append(card(('Vídeo - ' + smart_title(cur['t'])) if cur['t'] else 'Assistir vídeo no YouTube', b['href'], k='play')); i += 1; continue
        if t in ('img', 'imglink'):
            if cards: flush()
            im = image(b['tok'])
            if im:
                tag = f'<img src="{im[0]}" width="{im[1]}" height="{im[2]}" alt="{esc(b.get("alt") or "Imagem informativa")}" loading="lazy" decoding="async">'
                poster = im[1] >= 500
                if t == 'imglink':
                    h = b['href']; tag = f'<a href="{esc(href_of(h), quote=True)}"{attrs_of(h)} aria-label="Abrir">{tag}</a>'
                elif poster:
                    tag = f'<a href="{im[0]}" target="_blank" rel="noopener" aria-label="Ampliar imagem">{tag}</a>'
                gallery.append(f'<figure{" class=poster" if poster else ""}>{tag}</figure>')
            i += 1; continue
        flush()
        if t == 'h':
            open_sec(b['text']); i += 1; continue
        if t == 'p':
            # linhas alinhadas por espaços viram tabela
            j = i; rows = []
            while j < n and blocks[j]['t'] == 'p' and len(split_cells(blocks[j]['raw'])) >= 2: rows.append(split_cells(blocks[j]['raw'])); j += 1
            if len(rows) >= 3:
                hw = len(rows[0]); ph = re.compile(r'\d{4}\s?-?\s?\d{4}')
                for r in rows[1:]:   # nome com espaço duplo (ex.: "CAPS  IJ") vira uma célula só
                    if len(r) > hw:
                        k = next((x for x, c in enumerate(r) if ph.search(c)), None)
                        if k and k > 1: r[:k] = [' '.join(r[:k])]
                w = max(len(r) for r in rows)
                head = ''.join(f'<th>{esc(smart_title(c))}</th>' for c in rows[0] + [''] * (w - len(rows[0])))
                body = ''.join('<tr>' + ''.join(f'<td>{esc(c)}</td>' for c in r + [''] * (w - len(r))) + '</tr>' for r in rows[1:])
                out.append(f'<div class="tbl"><table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div>'); i = j; continue
            txt = b['text']
            if (not b['bold']) and len(txt) <= 40 and nxt and nxt['t'] in ('btn', 'imglink') and sum(c.isupper() for c in txt if c.isalpha()) >= .7 * max(1, sum(c.isalpha() for c in txt)) and not re.search(r'\d{4}[- ]?\d{4}', txt):
                open_sec(txt); i += 1; continue
            if b['bold'] and re.search(r'[A-Za-zÀ-ú]{3}', txt) and not re.search(r'\d{4}[- ]?\d{4}', txt) and not txt.startswith('#'):
                open_sec(txt); i += 1; continue
            cls = ' class="note"' if re.search(r'\d{4}[- ]?\d{4}', txt) else ''
            body = fix_inline(b['html'])
            if txt.startswith('#'): cls = ' class="tags"'
            out.append(f'<p{cls}>{body}</p>'); i += 1; continue
        if t == 'list':
            tag = 'ol' if b['ordered'] else 'ul'
            out.append(f'<{tag}>' + ''.join(f'<li>{fix_inline(x)}</li>' for x in b['items']) + f'</{tag}>'); i += 1; continue
        if t == 'table':
            out.append('<div class="tbl"><table>' + ''.join('<tr>' + ''.join(f'<td>{fix_inline(c)}</td>' for c in r) + '</tr>' for r in b['rows']) + '</table></div>'); i += 1; continue
        i += 1
    flush()
    out.append('</div></section>')
    res = ''.join(out)
    return re.sub(r'<section class="sec"><div class="sec-body"></div></section>', '', res)

# ---------------------------------------------------------------- páginas
LOGO_ART = {'início/academia-da-saúde'}  # usa o recorte limpo do logotipo (sem as faixas cinza da captura original)
# posição do enquadramento de cada imagem de cabeçalho, copiada do Google Sites original
HEADPOS = json.load(open(os.path.join(HERE, 'header-positions.json')))
POS_CSS = {'center center': 'center', 'top center': 'center top', 'bottom center': 'center bottom', 'center right': 'right center', 'center left': 'left center'}
DESCR = {'início/academia-da-saúde': 'Documentos e materiais de referência do programa Academia da Saúde.'}
ABOUT = '''<aside class="about" aria-labelledby="sobre-h">
      <div class="about-text">
        <h2 id="sobre-h">Sobre este repositório</h2>
        <p>Este repositório tem por objetivo informar, reunir, preservar, divulgar e garantir o acesso confiável e permanente aos documentos administrativos, técnicos, fluxos, protocolos, linhas de cuidado, entre outros documentos que se julguem relevantes para a rede de atenção à saúde de Cachoeirinha.</p>
      </div>
      <div class="about-contact">
        <h3>Arquivo fora de conformidade?</h3>
        <p>Avise nossa equipe para que a situação seja regularizada.</p>
        <a class="mail" href="mailto:repositoriosaudecachoeirinha@gmail.com">repositoriosaudecachoeirinha@gmail.com</a>
        <button type="button" class="btn ghost" id="copyMail" data-mail="repositoriosaudecachoeirinha@gmail.com">Copiar e-mail</button>
      </div>
    </aside>'''

def crumbs(slug):
    if slug == HOME: return ''
    parts = [f'<a href="{files[HOME]}">Início</a>']
    segs = slug.split('/')
    for k in range(2, len(segs)):
        a = '/'.join(segs[:k])
        if a in files: parts.append(f'<a href="{files[a]}">{esc(title_of(a))}</a>')
    parts.append(f'<span aria-current="page">{esc(title_of(slug))}</span>')
    return '<nav class="crumbs" aria-label="Você está em">' + '<span>/</span>'.join(parts) + '</nav>'

def build_main(slug):
    p = P[slug]; blocks = p['blocks']; title = title_of(slug)
    hdr = ('assets/img/academia-da-saude.jpg', 1416, 555) if slug in LOGO_ART else (image(p['header'], 900) if p.get('header') else None)
    only_btn = [b for b in blocks if b['t'] != 'btn']
    cta = ''
    if len(blocks) == 1 and blocks[0]['t'] == 'btn' and not children[slug]:
        b = blocks[0]; cta = f'<a class="cta" href="{esc(href_of(b["href"]), quote=True)}"{attrs_of(b["href"])}>{icon(topic(b["text"], b["href"])[0])}<span>{esc(smart_title(b["text"]))}</span>{ARROW}</a>'
        blocks = []
    pos = POS_CSS.get((HEADPOS.get(slug) or {}).get('pos') or 'center center', 'center')
    st = f' style="object-position:{pos}"' if pos != 'center' else ''
    art = (f'<div class="hero-art"><img src="{hdr[0]}" width="{hdr[1]}" height="{hdr[2]}" alt=""{st} decoding="async"></div>' if hdr else '')
    descr = f'<p>{esc(DESCR[slug])}</p>' if slug in DESCR else ''
    hero = f'<section class="hero{"" if hdr else " no-art"}">{art}<div class="hero-text"><h1>{esc(title)}</h1>{descr}{cta}</div></section>'
    sub = ''
    if children[slug]:
        sub = '<section class="sec"><h2>Neste setor</h2><div class="sec-body"><div class="docs">' + ''.join(card(title_of(c), 'page:' + c) for c in children[slug]) + '</div></div></section>'
    body = render_blocks(blocks, slug) if blocks else ''
    if not blocks and not cta and not children[slug]:
        body = f'<section class="sec"><div class="sec-body"><p class="note">Este conteúdo é um recurso incorporado do Google (mapa, planilha ou painel) e ainda precisa ser migrado. Enquanto isso, abra a página original: <a href="{SITE}/{urllib.parse.quote(slug)}" target="_blank" rel="noopener">abrir no site atual</a>.</p></div></section>'
    about = ABOUT if slug == HOME else ''
    return f'<main id="conteudo">{crumbs(slug)}{hero}{sub}{body}{about}</main>'

def page_html(slug):
    t = title_of(slug)
    full = SITE_NAME if slug == HOME else f'{t} · {SITE_NAME}'
    h = TEMPLATE.replace('{{TITLE}}', esc(full)).replace('{{SLUG}}', esc(slug)).replace('{{MAIN}}', build_main(slug))
    return h.replace('<div class="scrim"', SPRITE + '\n<div class="scrim"', 1)

# ---------------------------------------------------------------- saída
for s in order: open(os.path.join(OUT, files[s]), 'w', encoding='utf-8').write(page_html(s))
# cópia da página inicial como index.html (hospedagem comum); no protótipo do Claude, index.html é reservado
open(os.path.join(OUT, 'index.html'), 'w', encoding='utf-8').write(page_html(HOME))

nav = [{'s': s, 't': ('Início' if s == HOME else title_of(s)), 'h': files[s], 'd': depth(s)} for s in order]
search, seen = [], set()
for s in order:
    for b in P[s]['blocks']:
        if b['t'] == 'btn' and not b['href'].startswith('page:'):
            key = (b['text'], b['href'])
            if key in seen: continue
            seen.add(key)
            search.append({'n': smart_title(b['text']), 'p': title_of(s), 'f': files[s], 'u': b['href'], 'k': kind(b['href'])})
open(os.path.join(OUT, 'assets/nav.js'), 'w', encoding='utf-8').write(
    'window.NAV=' + json.dumps(nav, ensure_ascii=False, separators=(',', ':')) + ';\nwindow.SEARCH=' + json.dumps(search, ensure_ascii=False, separators=(',', ':')) + ';\n')
print(len(order), 'páginas,', len(search), 'documentos indexados,', len(img_cache), 'imagens')
