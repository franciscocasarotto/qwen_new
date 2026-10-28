# -*- coding: utf-8 -*-
"""Recalibra a nota 0-100 por percentil + penalidade de gap (exigências que o CV não cobre)."""
import json, math

v = json.load(open("vagas_remote_pontuadas.json"))

# Exigências duras que NÃO existem na Versão Mestre -> penalidade por presença na JD
GAP_PENALTY = {
 "kubernetes": 7, "cks": 8, "openshift": 5, "helm": 4, "argo": 5, "gitops": 5,
 "airflow": 4, "dbt": 4, "snowflake": 5, "splunk": 4, "prometheus": 3, "grafana": 0,
 "active directory": 5, "entra id": 5, "privileged access": 4, "pentest": 5,
 "penetration test": 5, "threat modeling": 5, "terraform": 2, "java": 3, ".net": 4,
 "power bi": 3, "dynamics": 4, "sap hana migration": 2, "servicenow": 0, "c2pa": 6,
}
# Termos que, se presentes na JD, indicam exigência de idioma
LANG_EN = ["english", "fluent english", "inglês fluente", "advanced english"]
LANG_ES = ["español", "spanish", "inglés", "latinoamérica", "hispanic"]

for x in v:
    t = (x["titulo"] + " " + x["descricao"]).lower()
    pen = sum(w for k, w in GAP_PENALTY.items() if k in t)
    x["_gap_pen"] = min(pen, 28)
    x["_lang_en"] = any(k in t for k in LANG_EN)
    x["_lang_es"] = any(k in t for k in LANG_ES)

raws = sorted(x["_pts"] + x["_bonus"] - x["_gap_pen"] for x in v)
n = len(raws)
adj = lambda x: x["_pts"] + x["_bonus"] - x["_gap_pen"]

def percentile(val):
    lo, hi = 0, n - 1
    while lo < hi:
        mid = (lo + hi) // 2
        if raws[mid] < val: lo = mid + 1
        else: hi = mid
    return lo / (n - 1)

for x in v:
    p = percentile(adj(x))
    x["nota"] = max(25, min(99, round(25 + p * 74)))

json.dump(v, open("vagas_remote_pontuadas.json", "w"), ensure_ascii=False, indent=1)
from collections import Counter
print("buckets:", dict(sorted(Counter(x["nota"] // 10 * 10 for x in v).items())))
print(">=80:", sum(1 for x in v if x["nota"] >= 80), "| >=70:", sum(1 for x in v if x["nota"] >= 70))
top = sorted(v, key=lambda z: -z["nota"])[:25]
for x in top:
    print(f'{x["nota"]:>2} | {x["pais"]} | pts={x["_pts"]:>3} bon={x["_bonus"]:>3} gap=-{x["_gap_pen"]:>2} | {x["empresa"][:24]:<24} | {x["titulo"][:48]}')
