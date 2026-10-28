# -*- coding: utf-8 -*-
"""Etapa 2 LATAM remoto: baixa descrição (se necessário) e pontua vs Versão Mestre."""
import json, re, time, random, urllib.request

PERFIL = {
 "azure":6,"aws":6,"gcp":5,"oci":6,"multicloud":7,"multi-cloud":7,"multi cloud":7,
 "hibrida":3,"híbrida":3,"landing zone":4,"infraestructura como codigo":4,"infraestrutura como código":4,
 "terraform":4,"iac":3,"ansible":2,"bicep":2,"arquitetur":8,"arquitectur":8,"solucoes":4,"soluções":4,
 "integracion":3,"integração":3,"api":3,"sap":8,"btp":6,"hana":4,"cpi":4,"fiori":3,"s/4hana":4,
 "finops":10,"costo":4,"custo":4,"optimiz":3,"otimiz":3,"gobernan":5,"governan":5,"compliance":3,
 "seguridad":4,"segurança":4,"security":4,"ccsp":5,"itil":5,"servicenow":6,"itsm":6,"sla":3,"mttr":4,
 "observab":5,"datadog":5,"zabbix":4,"dynatrace":4,"grafana":3,"sre":5,"site reliability":5,
 "kubernetes":3,"devops":4,"ci/cd":4,"pipeline":3,"inteligencia artificial":7,"inteligência artificial":7,
 "machine learning":6,"llm":5,"rag":6,"genai":5,"generativa":4,"databricks":7,"pyspark":5,"spark":3,
 "data lake":5,"datalake":4,"lakehouse":4,"dataops":6,"etl":3,"big data":4,"python":3,"nps":3,
 "presupuesto":3,"orçament":3,"p&l":3,"lideraz":6,"lideran":6,"lider ":4,"gest":5,"gerente":4,"jefe":2,
 "stakeholder":4,"pmi":3,"pmp":5,"scrum":3,"kanban":2,"migracion":4,"migra":4,"moderniz":4,
 "disponibilidad":4,"alta disponibilidad":5,"resili":3,"microservicios":3,"microsservi":3,
 "salesforce":3,"mulesoft":5,"digibee":5,"fortinet":3,"akamai":3,"waf":2,"cloud":5,"certificacion":3,
 "certifica":3,"linux":1,"vmware":3,"avs":3,"pre-sales":4,"preventa":4,"pré-venda":4,"cotizaci":3,
}
SENIOR = {"sr":8,"senior":8,"sênior":8,"especialista":8,"head":6,"principal":6,"lead":6,"iii":4,
          "arquiteto":6,"arquiteta":6,"arquitecto":6,"arquitecta":6,"gerente":5,"coordenador":2,
          "analista":-6,"pleno":-8}
BR_PTS = 12   # bônus: Brasil = contrato local CLT/PJ sem burocracia de visto/fuso
FUSO_OK = ("brazil","brasil","argentina","uruguay","paraguay","chile")

def score(texto, pais, local):
    t = texto.lower()
    pts, hits = 0, []
    for kw, w in PERFIL.items():
        n = t.count(kw)
        if n:
            add = w * min(n, 3); pts += add; hits.append((kw, add))
    bonus = 0
    for k, b in SENIOR.items():
        if re.search(r"\b" + re.escape(k), t): bonus += b
    if pais == "BR": bonus += BR_PTS
    if not any(f in local.lower() for f in FUSO_OK) and pais != "BR": bonus -= 5
    hits.sort(key=lambda x: -x[1])
    return pts, bonus, hits[:10]

def clean(html_txt):
    m = re.search(r'description__text[^>]*>(.*?)</div>', html_txt, re.S)
    if not m: return ""
    txt = re.sub(r"<[^>]+>", " ", m.group(1))
    return re.sub(r"\s+", " ", txt).strip()

vagas = json.load(open("vagas_prefiltradas.json"))
antigos = {v["link"]: v for v in json.load(open("/workspace/vagas_enriquecidas.json"))}
print("total a processar:", len(vagas), "| reaproveitando descrições já baixadas:", len(antigos))
ok, fail = 0, 0
for i, v in enumerate(vagas):
    if v["link"] in antigos and antigos[v["link"]].get("descricao"):
        v["descricao"] = antigos[v["link"]]["descricao"]; ok += 1; continue
    try:
        req = urllib.request.Request(v["link"], headers={"User-Agent": "Mozilla/5.0"})
        v["descricao"] = clean(urllib.request.urlopen(req, timeout=20).read().decode("utf-8", "ignore"))
        ok += 1
    except Exception as e:
        v["descricao"] = ""; fail += 1
    if i % 25 == 0: print(f"  {i}/{len(vagas)} (falhas={fail})", flush=True)
    time.sleep(random.uniform(0.4, 0.9))
print("descrições:", ok, "| falhas:", fail)

for v in vagas:
    base = v["titulo"] + " " + v["empresa"] + " " + v.get("eixo", "")
    pts, bonus, hits = score(base + " " + v["descricao"], v["pais"], v["local"])
    raw = pts + max(bonus, -30)
    v["_pts"], v["_bonus"], v["_hits"] = pts, bonus, hits
    v["nota"] = max(0, min(100, round(raw * 100 / 175)))
json.dump(vagas, open("vagas_remote_pontuadas.json", "w"), ensure_ascii=False, indent=1)
top = sorted(vagas, key=lambda x: -x["nota"])[:30]
for v in top:
    print(f'{v["nota"]:>3} | {v["pais"]} | {v["empresa"][:28]:<28} | {v["titulo"][:55]}')
print("\nsem descrição (nota só por título):", sum(1 for v in vagas if not v["descricao"]))
