# -*- coding: utf-8 -*-
"""Auditoria pos-filtro de idioma (nao pode sobrar nenhum ingles avancado na lista final)."""
import json, re, unicodedata, collections

def norm(s):
    s = unicodedata.normalize("NFKD", s).replace("&amp;", " ").replace("&nbsp;", " ")
    return re.sub(r"\s+", " ", s)

FR = re.compile(r"[^.;\n|•–—()\[\]]{0,150}\b(?:ingl[eê]s|english)\b[^.;\n|•–—()\[\]]{0,120}", re.I)
ADV = re.compile(r"(advanced|avanzad|fluent|fluency|fluente|native|business[- ]level|professional proficiency"
                 r"|upper-intermediate|\bc1\b|\bc2\b|b2\+?|conversacional|conversational|outstanding"
                 r"|spoken english|verbal and written|written and verbal|oral and written|both written and"
                 r"|spoken and written|required to be fluent)", re.I)
BAIXO = re.compile(r"(intermedi|basico|b[áa]sico|reading|leitura|documentation|documenta|working knowledge"
                   r"|\ba1\b|\ba2\b|beginner|elementary|async)", re.I)
AT = re.compile(r"(desejable|desej[áa]vel|a plus|diferencial|nice to have|preferible|preferred|optional"
                r"|would be|bonus)", re.I)

V = json.load(open("/workspace/remote_latam/vagas_remote_idiomas.json"))
OK = json.load(open("/workspace/remote_latam/vagas_remote_final_sem_ingles_avancado.json"))
print("analisadas:", len(V), "| lista final:", len(OK), "| removidas:", len(V)-len(OK))

fugas = []
for x in OK:
    t = norm(x["titulo"] + "\n" + x["descricao"])
    for f in {fr.strip() for fr in FR.findall(t)}:
        if ADV.search(f) and not BAIXO.search(f) and not AT.search(f):
            fugas.append((x, f)); break
print("FUGAS (ingles avancado nao atenuado ainda na lista final):", len(fugas))
for x, f in fugas[:10]: print("   !", x["nota"], x["empresa"][:22], "|", f[:110])

sem_ev = [x for x in V if x["_idioma_remover"] and not ADV.search(norm(x["_idioma_evidencia"]))]
print("REMOVIDAS sem marcador de nivel alto na evidencia:", len(sem_ev))
print("Flags _idioma_remover na lista final:", sum(z.get("_idioma_remover") for z in OK))
print("Por pais (final):", collections.Counter(z["pais"] for z in OK).most_common())
print("Notas 90+ na final:", sum(1 for z in OK if z["nota"] >= 90), "| 80-89:", sum(1 for z in OK if 80 <= z["nota"] < 90))
