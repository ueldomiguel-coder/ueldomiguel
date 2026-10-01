"""Extrai o conteúdo das páginas baixadas do Google Sites para JSON estruturado.
Uso: extract.py <pasta com as páginas e index.json/images.json> <saida.json>"""
import re, json, html, sys, os, urllib.parse
from bs4 import BeautifulSoup, NavigableString

SRC, OUT = sys.argv[1], sys.argv[2]
res = json.load(open(os.path.join(SRC, 'index.json')))
imgmap = json.load(open(os.path.join(SRC, 'images.json')))
PREFIX = '/view/saudecachoeirinha'
SLUGS = {slug for slug, _, _ in res}

def txt(el):
    t = el.get_text('').replace(' ', ' ')
    return re.sub(r'[ \t]+', ' ', t).strip()

def fix_href(h):
    h = html.unescape(h)
    if h.startswith('https://www.google.com/url'):
        q = urllib.parse.parse_qs(urllib.parse.urlparse(h).query).get('q')
        if q: h = q[0]
    if h.startswith(PREFIX):
        slug = urllib.parse.unquote(h[len(PREFIX):]).split('#')[0].strip('/') or 'tela-inicial'
        if slug in SLUGS: return 'page:' + slug
    return h

def is_bold(span):
    st = span.get('style', '')
    return 'font-weight: 700' in st or 'font-weight:700' in st or 'font-weight: bold' in st

def inline(el):
    out = []
    for c in el.children:
        if isinstance(c, NavigableString):
            out.append(html.escape(str(c).replace(' ', ' ')))
        elif c.name == 'a' and c.get('href'):
            out.append('<a href="%s">%s</a>' % (html.escape(fix_href(c['href']), quote=True), inline(c).strip() or html.escape(c['href'])))
        elif c.name == 'br': out.append('<br>')
        elif c.name in ('span', 'strong', 'em', 'b', 'i', 'u'):
            inner = inline(c)
            if inner.strip() and (c.name in ('strong', 'b') or is_bold(c)): inner = '<strong>%s</strong>' % inner
            out.append(inner)
        else: out.append(inline(c))
    return re.sub(r'(?:<br>\s*)+$', '', ''.join(out)).replace('</strong><strong>', '')

def all_bold(p):
    spans = [s for s in p.find_all('span') if s.get_text('').strip() and not s.find('span')]
    return bool(spans) and all(is_bold(s) for s in spans)

def header_token(s):
    pre = s[:s.find('role="main"')]
    m = list(re.finditer(r'class="IFuOkc"[^>]*background-image: url\((https://sites\.google\.com/sitesv-images-rt/[^)]+)\)', pre))
    return html.unescape(m[-1].group(1))[48:70] if m else None

pages = {}
for slug, fn, _ in res:
    s = open(os.path.join(SRC, fn), encoding='utf-8', errors='ignore').read()
    tok = header_token(s)
    i = s.find('role="main"'); i = s.rfind('<div', 0, i); j = s.rfind('<footer')
    soup = BeautifulSoup(s[i:j], 'lxml')
    blocks, title = [], None
    for el in soup.find_all(['h1', 'h2', 'h3', 'h4', 'p', 'ul', 'ol', 'table', 'iframe', 'img', 'a']):
        n = el.name
        if n == 'a':
            if el.find_parent(['p', 'li', 'td', 'th', 'h1', 'h2', 'h3', 'h4']) or not el.get('href'): continue
            t, h = txt(el), fix_href(el['href'])
            if h.startswith('#'): continue
            im = el.find('img')
            if not t and im is not None and 'sitesv-images' in (im.get('src') or ''):
                blocks.append({'t': 'imglink', 'tok': html.unescape(im['src'])[48:70], 'href': h, 'alt': im.get('aria-label') or im.get('alt') or ''})
                continue
            if not t: continue
            blocks.append({'t': 'btn', 'text': t, 'href': h})
        elif n in ('h1', 'h2', 'h3', 'h4'):
            t = txt(el)
            if not t: continue
            if title is None and n == 'h1': title = t
            else: blocks.append({'t': 'h', 'text': t})
        elif n == 'p':
            if el.find_parent(['a', 'ul', 'ol', 'table', 'h1', 'h2', 'h3', 'h4']): continue
            t = txt(el)
            if not t: continue
            blocks.append({'t': 'p', 'html': inline(el).strip(), 'text': t, 'bold': all_bold(el) and len(t) <= 100,
                           'raw': el.get_text('').replace(' ', ' ')})
        elif n in ('ul', 'ol'):
            if el.find_parent(['ul', 'ol']): continue
            items = [inline(li).strip() for li in el.find_all('li') if txt(li)]
            if items: blocks.append({'t': 'list', 'ordered': n == 'ol', 'items': items})
        elif n == 'table':
            rows = [[inline(c).strip() for c in r.find_all(['td', 'th'])] for r in el.find_all('tr')]
            if rows: blocks.append({'t': 'table', 'rows': rows})
        elif n == 'iframe':
            src = html.unescape(el.get('src') or '')
            m = re.search(r'youtube\.com/embed/([\w-]+)', src)
            if m: blocks.append({'t': 'video', 'href': 'https://www.youtube.com/watch?v=' + m.group(1)})
        elif n == 'img':
            src = html.unescape(el.get('src', ''))
            if el.find_parent('a', href=True) and not txt(el.find_parent('a')): continue
            if 'sitesv-images' in src: blocks.append({'t': 'img', 'tok': src[48:70], 'alt': el.get('aria-label') or el.get('alt') or ''})
    pages[slug] = {'slug': slug, 'title': title, 'header': tok, 'blocks': blocks}

# ordem e hierarquia do menu, na ordem em que aparecem na página inicial
home = open(os.path.join(SRC, dict((a, b) for a, b, _ in res)['tela-inicial']), encoding='utf-8', errors='ignore').read()
nav, seen = [], set()
for m in re.finditer(r'<a [^>]*href="(%s[^"#?]*)"[^>]*>(.*?)</a>' % PREFIX, home, re.S):
    slug = urllib.parse.unquote(m.group(1)[len(PREFIX):]).strip('/') or 'tela-inicial'
    t = re.sub(r'<[^>]+>', '', m.group(2)); t = html.unescape(re.sub(r'\s+', ' ', t)).strip()
    if slug in seen or slug not in SLUGS or not t: continue
    seen.add(slug); nav.append({'slug': slug, 'navtitle': t})
json.dump({'pages': pages, 'nav': nav, 'tokens': imgmap}, open(OUT, 'w'), ensure_ascii=False, indent=1)
print(len(pages), 'páginas;', len(nav), 'itens de menu')
