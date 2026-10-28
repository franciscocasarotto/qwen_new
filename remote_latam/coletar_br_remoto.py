# -*- coding: utf-8 -*-
"""Etapa 1 (BR, REMOTO): coleta ampliada via LinkedIn guest API + validacao de links."""
import re, time, json, html, random, urllib.request, urllib.parse

KW = [
    "arquiteto de solucoes cloud", "arquiteto cloud", "cloud architect", "solutions architect",
    "arquiteto de solucoes", "arquiteto de dados", "data architect", "finops",
    "arquiteto de ia", "ai architect", "machine learning architect", "engenheiro de dados",
    "sap basis", "arquiteto sap", "devsecops", "site reliability engineer", "sre",
    "gerente de projetos ti", "gestor de projetos tecnologia", "it service manager", "itsm",
    "service now", "head de infraestrutura", "gerente de infraestrutura e cloud",
    "tech lead", "principal engineer", "distinguished engineer", "cloud security architect",
    "arquiteto de integracoes", "databricks", "plataforma digital",
]
LOCS = ["Brazil", "São Paulo, Brazil", "Campinas, Brazil", "Belo Horizonte, Brazil",
        "Rio de Janeiro, Brazil", "Curitiba, Brazil", "Porto Alegre, Brazil",
        "Brasília, Brazil", "Florianópolis, Brazil", "Recife, Brazil", "Goiânia, Brazil"]

def fetch(kw, loc, start=0):
    url = ("https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords="
           + urllib.parse.quote(kw) + "&location=" + urllib.parse.quote(loc)
           + "&f_WT=2&f_TPR=r1296000&sortBy=DD&position=" + str(start))
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36"})
    return urllib.request.urlopen(req, timeout=25).read().decode("utf-8", "ignore")

def parse(t):
    out = []
    for c in t.split("<li>")[1:]:
        m_link  = re.search(r'base-card__full-link[^>]*href="([^"]+)"', c)
        m_title = re.search(r'base-search-card__title">\s*([^<]+?)\s*</h3>', c)
        m_comp  = re.search(r'base-search-card__subtitle">\s*<a[^>]*>\s*([^<]+?)\s*</a>', c)
        m_loc   = re.search(r'job-search-card__location">\s*([^<]+?)\s*</span>', c)
        m_date  = re.search(r'datetime="([^"]+)"', c)
        if not (m_link and m_title): continue
        out.append({"titulo": html.unescape(m_title.group(1)),
                    "empresa": html.unescape(m_comp.group(1)) if m_comp else "?",
                    "local":   html.unescape(m_loc.group(1)) if m_loc else "?",
                    "data":    m_date.group(1)[:10] if m_date else "",
                    "link":    html.unescape(m_link.group(1)).split("?")[0]})
    return out

def is_br(local):
    l = local.lower()
    if any(x in l for x in ("brazil","brasil")): return True
    ufs = ("são paulo","sao paulo","rio de janeiro","minas gerais","parana","bahia","rio grande do sul",
           "pernambuco","ceara","pará","para ","goiás","goias","distrito federal","brasília","brasilia",
           "santa catarina","espírito santo","espirito santo","maranhão","tocantins","mato grosso","amazonas",
           "paraíba","cuiabá","curitiba","porto alegre","belém","manaus","fortaleza","recife","salvador",
           "goiânia","florianópolis","joinville","campinas","santos","abc paulista","barueri","osasco",
           "guarulhos","são josé dos campos","jundiaí","ribeirão preto","uberlândia","londrina","blumenau")
    return any(x in l for x in ufs)

vistos, todas, erros = set(), [], 0
for loc in LOCS:
    for kw in KW:
        try:
            jobs = parse(fetch(kw, loc))
        except Exception as e:
            erros += 1; print("ERRO", loc, kw, "->", type(e).__name__); time.sleep(4); continue
        novas = 0
        for j in jobs:
            if j["link"] in vistos or not is_br(j["local"]): continue
            vistos.add(j["link"]); j["pais"]="BR"; j["eixo"]=kw
            todas.append(j); novas += 1
        print(f"[{loc[:18]:<18}] {kw[:28]:<28} cards={len(jobs):>3} novas_BR={novas:>3} total={len(todas)}")
        time.sleep(random.uniform(1.0, 1.9))

json.dump(todas, open("br_remoto_brutos.json","w"), ensure_ascii=False, indent=1)
print("\n>>> TOTAL VAGAS UNICAS BR REMOTO:", len(todas), "| erros de rede:", erros)
