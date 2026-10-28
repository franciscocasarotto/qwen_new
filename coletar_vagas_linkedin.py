# -*- coding: utf-8 -*-
"""
Coleta vagas REAIS do LinkedIn (guest API) — últimos 15 dias.
Localização-alvo: região de Bragança Paulista/SP + Brasil (para vagas remotas).
Saída: /workspace/vagas_brutos.json
"""
import re, time, json, html, random, urllib.request, urllib.parse

LOC_BRA = "Bragan%C3%A7a%20Paulista%20Region,%20State%20of%20S%C3%A3o%20Paulo,%20Brazil"
KW_BR = [
    "arquiteto de soluções", "arquiteto cloud", "cloud architect", "arquiteto azure",
    "arquiteto aws", "arquiteto de dados", "arquiteto sap", "arquiteto ia",
    "finops", "gerente de projetos ti", "gestor de ti", "itsm servicenow",
    "site reliability engineer", "cloud security architect", "solutions architect",
    "head de infraestrutura", "coordenador de ti",
]
KW_REMOTO = [
    "arquiteto cloud remoto", "cloud architect remote", "arquiteto de soluções remoto",
    "finops remoto", "data architect remote", "solutions architect remote brazil",
]

def fetch(kw, loc):
    url = ("https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords="
           + urllib.parse.quote(kw) + f"&location={loc}&f_TPR=r1296000&sortBy=DD")
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36"})
    return urllib.request.urlopen(req, timeout=20).read().decode("utf-8", "ignore")

def parse(t):
    out = []
    for c in t.split("<li>")[1:]:
        m_link = re.search(r'base-card__full-link[^>]*href="([^"]+)"', c)
        m_title = re.search(r'base-search-card__title">\s*([^<]+?)\s*</h3>', c)
        m_comp = re.search(r'base-search-card__subtitle">\s*<a[^>]*>\s*([^<]+?)\s*</a>', c)
        m_loc = re.search(r'job-search-card__location">\s*([^<]+?)\s*</span>', c)
        m_date = re.search(r'datetime="([^"]+)"', c)
        if not (m_link and m_title):
            continue
        link = html.unescape(m_link.group(1)).split("?")[0]
        out.append({
            "titulo": html.unescape(m_title.group(1)),
            "empresa": html.unescape(m_comp.group(1)) if m_comp else "?",
            "local": html.unescape(m_loc.group(1)) if m_loc else "?",
            "data": m_date.group(1) if m_date else "",
            "link": link,
        })
    return out

def is_brazil(local):
    l = local.lower()
    bad = ["united states", ", ca", ", tx", ", fl", ", ny", ", nj", ", ma", ", il", ", oh",
           ", wa", ", co", ", nc", ", ga", ", pa", ", mi", ", md", ", az", ", tn", ", mo",
           "canberra", "kuwait", "peru", "london", "united kingdom", "germany", "india"]
    if any(b in l for b in bad):
        return False
    return "brazil" in l or "brasil" in l or any(
        s in l for s in ["são paulo", "sao paulo", "rio de janeiro", "minas", "paraná",
                         "campinas", "barueri", "osasco", "jundiaí", "são josé dos campos"])

vistos, todas = set(), []
plan = [(kw, LOC_BRA) for kw in KW_BR] + [(kw, "Brasil") for kw in KW_REMOTO]
for kw, loc in plan:
    try:
        jobs = parse(fetch(kw, loc))
    except Exception as e:
        print("ERRO", kw, "->", e)
        time.sleep(3); continue
    novas = 0
    for j in jobs:
        if j["link"] in vistos or not is_brazil(j["local"]):
            continue
        vistos.add(j["link"]); j["eixo"] = kw
        todas.append(j); novas += 1
    print(f"[{kw}] ({'região BP' if 'Bragan' in loc else 'Brasil'}): {len(jobs)} cards, {novas} novas BR")
    time.sleep(random.uniform(1.5, 2.5))

json.dump(todas, open("/workspace/vagas_brutos.json", "w"), ensure_ascii=False, indent=1)
print("TOTAL únicas no Brasil:", len(todas))
