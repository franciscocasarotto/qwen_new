# -*- coding: utf-8 -*-
"""Etapa 2 (BR): baixa descricao de cada vaga + VALIDA o link (HTTP 200 vs expirado)."""
import json, re, time, random, urllib.request, urllib.error

def clean(h):
    m = re.search(r'description__text[^>]*>(.*?)</div>', h, re.S)
    if not m: return ""
    txt = re.sub(r"<[^>]+>", " ", m.group(1))
    return re.sub(r"\s+", " ", txt).strip()

vagas = json.load(open("br_remoto_brutos.json"))
antigos = {}
for f in ("vagas_remote_idiomas.json", "/workspace/vagas_enriquecidas.json"):
    try:
        for v in json.load(open(f)): antigos[v["link"]] = v
    except Exception: pass
print("vagas:", len(vagas), "| cache de descricoes:", len(antigos), flush=True)

ok = cache = morto = 0
for i, v in enumerate(vagas):
    a = antigos.get(v["link"])
    if a and a.get("descricao"):
        v["descricao"] = a["descricao"]; v["http_status"] = 200; v["link_ok"] = True
        cache += 1; continue
    try:
        req = urllib.request.Request(v["link"], headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120"})
        html_txt = urllib.request.urlopen(req, timeout=20).read().decode("utf-8", "ignore")
        v["http_status"] = 200; v["link_ok"] = True
        v["descricao"] = clean(html_txt); ok += 1
        if not v["descricao"] and "This job is no longer available" in html_txt:
            v["link_ok"] = False; v["motivo_morto"] = "encerrada/expirada"; morto += 1
    except urllib.error.HTTPError as e:
        v["http_status"] = e.code; v["descricao"] = ""; v["link_ok"] = e.code not in (404, 410)
        if not v["link_ok"]: v["motivo_morto"] = f"HTTP {e.code}"; morto += 1
    except Exception as e:
        v["http_status"] = 0; v["descricao"] = ""; v["link_ok"] = None
        v["motivo_morto"] = type(e).__name__
    if i % 50 == 0: print(f"  {i}/{len(vagas)} baixadas={ok} cache={cache} mortas={morto}", flush=True)
    time.sleep(random.uniform(0.35, 0.75))

json.dump(vagas, open("br_remoto_descricoes.json","w"), ensure_ascii=False, indent=1)
print(f"\n>>> DOWNLOAD CONCLUIDO | novas={ok} cache={cache} links invalidos={morto} "
      f"| sem status={sum(1 for v in vagas if v.get('http_status')==0)}")
