# -*- coding: utf-8 -*-
"""
Etapa 2: baixa a descrição completa de cada vaga real coletada e calcula a
NOTA DE COMPATIBILIDADE contra a Versão Mestre do currículo (palavras-chave
ponderadas) + bônus por senioridade/arquitetura/liderança.
Saída: /workspace/vagas_enriquecidas.json
"""
import json, re, time, random, urllib.request

PERFIL = {
    # termo : peso
    "azure": 6, "aws": 6, "gcp": 5, "oci": 6, "multicloud": 7, "multi-cloud": 7,
    "híbrida": 3, "hibrida": 3, "híbrido": 3, "landing zone": 4, "infraestrutura como código": 4,
    "terraform": 4, "iac": 3, "ansible": 2, "bicep": 2,
    "arquitetur": 8, "soluç": 4, "solucao": 3, "integracao": 3, "integração": 3, "api": 3,
    "sap": 8, "btp": 6, "hana": 4, "cpi": 4, "fiori": 3, "s/4hana": 4,
    "finops": 10, "custo": 4, "otimiza": 3, "governan": 5, "compliance": 3, "segurança": 4,
    "seguranca": 4, "security": 4, "ccsp": 5, "itil": 5, "servicenow": 6, "itsm": 6,
    "sla": 3, "mttr": 4, "observab": 5, "datadog": 5, "zabbix": 4, "dynatrace": 4, "grafana": 3,
    "sre": 5, "site reliability": 5, "kubernetes": 3, "devops": 4, "ci/cd": 4, "pipeline": 3,
    "ia": 3, "inteligência artificial": 7, "inteligencia artificial": 7, "machine learning": 6,
    "ml": 2, "llm": 5, "rag": 6, "genai": 5, "generativa": 4, "databricks": 7,
    "pyspark": 5, "spark": 3, "data lake": 5, "datalake": 4, "dataops": 6, "etl": 3,
    "big data": 4, "python": 3, "nps": 3, "orçament": 3, "orcament": 3, "pl ": 2, "p&l": 3,
    "lider": 5, "lideran": 6, "gest": 5, "gerente": 4, "coorden": 2, "stakeholder": 4,
    "pmi": 3, "pmp": 5, "ágil": 2, "scrum": 3, "kanban": 2, "migra": 4, "moderniza": 4,
    "disponibilidad": 4, "alta disponibilidade": 5, "resili": 3, "microsservi": 3,
    "salesforce": 3, "mulesoft": 5, "digibee": 5, "fortinet": 3, "akamai": 3, "waf": 2,
    "cloud": 5, "certifica": 3, "powershell": 1, "linux": 1, "vmware": 3, "av s": 0, "avs": 3,
}
SENIOR_BONUS = {"sr": 8, "sênior": 8, "senior": 8, "especialista": 8, "head": 6,
                "principal": 6, "lead": 6, "arquiteto": 6, "arquiteta": 6, "gerente": 5,
                "coordenador": 2, "analista": -6, "assistente": -15, "júnior": -20,
                "junior": -20, "estágio": -30, "estagio": -30, "pleno": -8}

def score(texto):
    t = texto.lower()
    pts, hits = 0, []
    for kw, w in PERFIL.items():
        n = t.count(kw)
        if n:
            add = w * min(n, 3)          # repete até 3x para não inflar
            pts += add; hits.append((kw, add))
    bonus = 0
    for k, b in SENIOR_BONUS.items():
        if re.search(r'\b' + re.escape(k), t):
            bonus += b
    hits.sort(key=lambda x: -x[1])
    return pts, bonus, hits[:12]

def fetch_desc(link):
    req = urllib.request.Request(link, headers={"User-Agent": "Mozilla/5.0"})
    html_txt = urllib.request.urlopen(req, timeout=20).read().decode("utf-8", "ignore")
    m = re.search(r'description__text[^>]*>(.*?)</div>', html_txt, re.S)
    if not m:
        return ""
    txt = re.sub(r'<[^>]+>', ' ', m.group(1))
    return re.sub(r'\s+', ' ', txt).strip()

vagas = json.load(open("/workspace/vagas_brutos.json"))
print("Coletando descrições de", len(vagas), "vagas...")
for i, v in enumerate(vagas, 1):
    try:
        d = fetch_desc(v["link"])
    except Exception as e:
        d = ""
        print(i, "erro", type(e).__name__)
    v["descricao"] = d[:4000]
    if i % 15 == 0:
        print(f"  {i}/{len(vagas)}"); time.sleep(random.uniform(2, 4))
    else:
        time.sleep(random.uniform(0.6, 1.4))

for v in vagas:
    pts, bonus, hits = score((v["titulo"] + " " + v["descricao"]))
    ment = 0
    for c in ["nexa", "votorantim", "cimed", "indra", "minsait", "locaweb", "nextios",
              "union it", "porto seguro", "jadlog", "semad", "heineken", "baucco", "bauducco", "vivo"]:
        if c in v["empresa"].lower():
            ment = 6; break
    raw = pts + bonus + ment
    v["pts"], v["bonus"], v["bonus_cliente"], v["hits"] = pts, bonus, ment, hits
    v["nota_raw"] = raw

mx = max(x["nota_raw"] for x in vagas) or 1
mn = min(x["nota_raw"] for x in vagas)
for v in vagas:
    v["nota"] = round(max(0, min(100, 40 + 60 * (v["nota_raw"] - mn) / (mx - mn))))

vagas.sort(key=lambda x: -x["nota"])
json.dump(vagas, open("/workspace/vagas_enriquecidas.json", "w"), ensure_ascii=False, indent=1)
print("\nTOP 25:")
for v in vagas[:25]:
    print(f'{v["nota"]:>3} | {v["data"]} | {v["titulo"][:46]:46} | {v["empresa"][:26]:26} | pts{v["pts"]} bon{v["bonus"]} cli{v["bonus_cliente"]}')
print("\nBOTTOM 8:")
for v in vagas[-8:]:
    print(f'{v["nota"]:>3} | {v["titulo"][:50]} | {v["empresa"][:26]}')
