"""Baixa imagens (cabeçalho e conteúdo) de cada página do Google Sites logo após buscar a página.
Os endereços das imagens expiram rápido, por isso a busca e o download acontecem juntos."""
import re, json, html, sys, os, subprocess, urllib.parse
from concurrent.futures import ThreadPoolExecutor
SRC, IMG = sys.argv[1], sys.argv[2]
os.makedirs(IMG, exist_ok=True)
res = json.load(open(os.path.join(SRC, 'index.json')))
PAT = re.compile(r'https://sites\.google\.com/sitesv-images-rt/[^"\'\s)\\]+')
def run(item):
    slug, fn, _ = item
    p = '/view/saudecachoeirinha/' + slug if slug != 'inicio' else '/view/saudecachoeirinha'
    u = 'https://sites.google.com' + urllib.parse.quote(p, safe='/')
    page = os.path.join(SRC, fn)
    subprocess.run(['curl','-sS','-L','--max-time','60','-o',page,u])
    s = open(page, encoding='utf-8', errors='ignore').read()
    urls = list(dict.fromkeys(html.unescape(x) for x in PAT.findall(s)))
    got = {}
    for x in urls:
        key = x[48:70]
        out = os.path.join(IMG, re.sub(r'[^A-Za-z0-9_-]','',key) + '.bin')
        if not os.path.exists(out):
            subprocess.run(['curl','-sS','-L','--max-time','60','-H','Accept: image/*','-o',out,x])
        got[key] = out
    return slug, got
with ThreadPoolExecutor(4) as ex: out = list(ex.map(run, res))
json.dump(dict(out), open(os.path.join(SRC, 'images.json'), 'w'))
print('ok', len(out))
