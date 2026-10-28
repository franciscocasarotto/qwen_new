# -*- coding: utf-8 -*-
"""Etapa 1 (América do Sul, REMOTO): coleta via LinkedIn guest API."""
import re, time, json, html, random, urllib.request, urllib.parse

KW = [
    "cloud architect", "solutions architect", "arquiteto de solucoes", "arquiteto cloud",
    "finops", "data architect", "ai architect", "sap basis", "devops engineer",
    "site reliability engineer", "it service manager", "itsm", "cloud security architect",
    "gerente de projetos ti", "tech lead", "head of infrastructure",
]
LOCS = {
    "AR": "Argentina", "BR": "Brazil", "CL": "Chile", "CO": "Colombia",
    "PE": "Peru", "UY": "Uruguay", "PY": "Paraguay", "EC": "Ecuador",
    "BO": "Bolivia", "VE": "Venezuela", "GEO": "South America",
}
def fetch(kw, loc):
    url = ("https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords="
           + urllib.parse.quote(kw) + "&location=" + urllib.parse.quote(loc)
           + "&f_WT=2&f_TPR=r1296000&sortBy=DD")   # f_WT=2 => REMOTO | f_TPR=r1296000 => 15 dias
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36"})
    return urllib.request.urlopen(req, timeout=25).read().decode("utf-8", "ignore")

def parse(t):
    out = []
    for c in t.split("<li>")[1:]:
        m_link = re.search(r'base-card__full-link[^>]*href="([^"]+)"', c)
        m_title = re.search(r'base-search-card__title">\s*([^<]+?)\s*</h3>', c)
        m_comp = re.search(r'base-search-card__subtitle">\s*<a[^>]*>\s*([^<]+?)\s*</a>', c)
        m_loc = re.search(r'job-search-card__location">\s*([^<]+?)\s*</span>', c)
        m_date = re.search(r'datetime="([^"]+)"', c)
        if not (m_link and m_title): continue
        out.append({"titulo": html.unescape(m_title.group(1)),
                    "empresa": html.unescape(m_comp.group(1)) if m_comp else "?",
                    "local": html.unescape(m_loc.group(1)) if m_loc else "?",
                    "data": m_date.group(1) if m_date else "",
                    "link": html.unescape(m_link.group(1)).split("?")[0]})
    return out

LATAM_COUNTRIES = ["argentina","brazil","brasil","chile","colombia","peru","perú","uruguay",
                   "paraguay","ecuador","bolivia","bolívia","venezuela","south america","latam",
                   "latin america","américa latina","guatemala","costa rica","panama","republica dominicana"]
def is_latam(local):
    l = local.lower()
    return any(c in l for c in LATAM_COUNTRIES)

vistos, todas = set(), []
for cc, loc in LOCS.items():
    for kw in KW:
        try:
            jobs = parse(fetch(kw, loc))
        except Exception as e:
            print("ERRO", cc, kw, "->", e); time.sleep(3); continue
        novas = 0
        for j in jobs:
            if j["link"] in vistos or not is_latam(j["local"]): continue
            vistos.add(j["link"]); j["pais"] = cc; j["eixo"] = kw
            todas.append(j); novas += 1
        print(f"[{cc}] {kw}: {len(jobs)} cards, {novas} novas LATAM")
        time.sleep(random.uniform(1.2, 2.2))
    print(f"--- acumulado: {len(todas)} ---")

json.dump(todas, open("/workspace/remote_latam/vagas_remote_brutos.json","w"), ensure_ascii=False, indent=1)
print("TOTAL únicas LATAM remoto:", len(todas))
