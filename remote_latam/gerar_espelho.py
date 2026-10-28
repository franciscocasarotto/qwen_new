# -*- coding: utf-8 -*-
"""Gera a Versao Espelho (tabela) do perfil publico de Francisco Casarotto no LinkedIn."""
import re, json, urllib.request

URL = "https://www.linkedin.com/in/francisco-casarotto/"
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36",
      "Accept-Language": "en-US,en;q=0.9"}
try:
    html_txt = urllib.request.urlopen(urllib.request.Request(URL, headers=UA), timeout=25).read().decode("utf-8","ignore")
    status = 200
except Exception as e:
    html_txt, status = "", type(e).__name__

def grab(patterns, text):
    for p in patterns:
        m = re.search(p, text, re.I)
        if m: return re.sub(r"\s+"," ",m.group(1)).strip()
    return ""

out = {"url": URL, "http_status": status}
if status == 200:
    out["headline"] = grab([r'<title>([^<]*?)\s*\|\s*LinkedIn', r'"headline"\s*:\s*"([^"]+)"'], html_txt)
    out["skills"]   = sorted(set(re.findall(r'skill-entity__name-text[^>]*>\s*([^<]{3,40})\s*<', html_txt)))[:40]
    out["certs"]    = sorted(set(re.findall(r'certification-entity__subtitle-text[^>]*>\s*([^<]{3,80})\s*<', html_txt)))
    out["locale"]   = bool(re.search(r'pt-br|português|Portuguese', html_txt, re.I))
json.dump(out, open("perfil_linkedin_espeelho.json","w"), ensure_ascii=False, indent=1)
print(json.dumps({k:(v if k!="skills" else v[:15]) for k,v in out.items()}, ensure_ascii=False, indent=1)[:900])
