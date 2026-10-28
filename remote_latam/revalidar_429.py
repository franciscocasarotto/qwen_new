# -*- coding: utf-8 -*-
"""Re-baixa apenas as vagas que retornaram HTTP 429 (rate limit)."""
import json, re, time, random, urllib.request
def clean(h):
    m = re.search(r'description__text[^>]*>(.*?)</div>', h, re.S)
    if not m: return ""
    return re.sub(r"\s+"," ",re.sub(r"<[^>]+>"," ",m.group(1))).strip()

D = json.load(open("br_remoto_descricoes.json"))
pend = [v for v in D if not v.get("descricao")]
print("revalidando:", len(pend))
for v in pend:
    for tentativa in range(3):
        try:
            req = urllib.request.Request(v["link"], headers={"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120"})
            h = urllib.request.urlopen(req, timeout=25).read().decode("utf-8","ignore")
            v["descricao"] = clean(h); v["http_status"] = 200; v["link_ok"] = True
            print("OK ", v["empresa"], "|", len(v["descricao"]), "chars"); break
        except Exception as e:
            v["http_status"] = getattr(e,"code",0); time.sleep(random.uniform(6,12))
    else:
        print("FALHOU", v["empresa"], v["titulo"])
json.dump(D, open("br_remoto_descricoes.json","w"), ensure_ascii=False, indent=1)
print("restam sem descricao:", sum(1 for v in D if not v.get("descricao")))
