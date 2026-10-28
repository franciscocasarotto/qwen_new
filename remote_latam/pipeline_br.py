# -*- coding: utf-8 -*-
"""Etapas 3-6 (BR REMOTO): modo de trabalho, pontuacao vs CV, filtro de idioma, saida."""
import json, re, sys
from collections import Counter
sys.path.insert(0, "/workspace/remote_latam")
from reclass_remote import pontuar_lote, classificar

V = json.load(open("br_remoto_descricoes.json"))
print("coletadas:", len(V))

# ---------- ETAPA 3: classificacao honesta do MODO DE TRABALHO ----------
RE_REMOTO = re.compile(r"100%\s*remoto|remoto\b|home\s*office|teletrabalho|anywhere|work from home|fully remote|distributed", re.I)
RE_HIBRIDO = re.compile(r"hibrid[oa]|h[íi]brid|partially remote|presencial.*remoto|remoto.*presencial|2x|3x.*semana", re.I)
RE_PRES = re.compile(r"presencial|on[- ]site|onsite|no escritório|in office", re.I)

def modo(v):
    blob = v["titulo"] + " | " + v.get("descricao", "")[:900]
    if RE_HIBRIDO.search(blob): return "Híbrido (revisar)"
    if RE_PRES.search(blob) and not RE_REMOTO.search(blob): return "Presencial (revisar)"
    if RE_REMOTO.search(blob): return "Remoto confirmado na JD"
    return "Remoto (filtro LinkedIn)"
for v in V: v["modo"] = modo(v)

# ---------- ETAPAS 4 e 5 ----------
pontuar_lote(V)
mantidas, removidas_idioma = [], []
for v in V:
    cls, ev = classificar(v["titulo"] + "\n" + v.get("descricao",""))
    v["_idioma_classe"], v["_idioma_evidencia"] = cls, ev
    (removidas_idioma if cls == "REMOVER_INGLES_AVANCADO" else mantidas).append(v)

# ---------- EXCLUSOES AUTOMATICAS ----------
JUNIOR = re.compile(r"\b(junior|trainee|est[aá]gio|intern|assistente|assistant|júnior)\b", re.I)
OK = [v for v in mantidas if v.get("link_ok") is not False
      and not JUNIOR.search(v["titulo"])
      and v["modo"] != "Presencial (revisar)"]
print("links invalidos:", sum(1 for v in V if v.get("link_ok") is False))
print("removidas por ingles avancado:", len(removidas_idioma))
print("FINAL BR remoto:", len(OK), "|", dict(Counter(v["modo"] for v in OK)))

json.dump(OK, open("br_remoto_final.json","w"), ensure_ascii=False, indent=1)
json.dump(removidas_idioma, open("br_remoto_removidas_ingles.json","w"), ensure_ascii=False, indent=1)
top = sorted(OK, key=lambda z: -z["nota"])[:20]
for x in top:
    print(f'{x["nota"]:>2} | {x["empresa"][:26]:<26} | {x["titulo"][:52]:<52} | {x["modo"][:22]}')
