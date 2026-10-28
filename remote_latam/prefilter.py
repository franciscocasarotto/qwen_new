import json, re
from collections import Counter
d = json.load(open("vagas_remote_brutos.json"))
STRONG = re.compile(r"architect|arquitet|arquitect|solu[cç][oõ]es|solutions|finops|itsm|service manager|reliability|devops|data engineer|tech lead|head of|gerente|gestor|cloud|sap|infraestructura|plataforma|platform", re.I)
JUNIOR = re.compile(r"\bjunior\b|\btrainee\b|estagio|est[aá]gio|intern\b|assistente|assistant", re.I)
keep, drop = [], 0
for x in d:
    t = x["titulo"] + " | " + x["empresa"] + " | " + x.get("eixo", "")
    if JUNIOR.search(t):
        drop += 1; continue
    if STRONG.search(t):
        keep.append(x)
    else:
        drop += 1
json.dump(keep, open("vagas_prefiltradas.json", "w"), ensure_ascii=False, indent=1)
print("mantidas:", len(keep), "| descartadas:", drop)
print(Counter(x["pais"] for x in keep).most_common())
