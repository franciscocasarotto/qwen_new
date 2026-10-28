#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
consolidar_fontes.py — Une LinkedIn + Indeed (e qualquer import) em UMA base com nota comparável.

Faz o que a coleta do LinkedIn já fazia, só que agora para todas as fontes:
  1. junta as 657 vagas LinkedIn validadas + todos os JSONs de remote_latam/fontes/*.json
  2. deduplica por URL e por (empresa+cargo) normalizado -> vaga cross-postada não é contada 2x
  3. repontua TODO o lote junto (percentil sobre o lote combinado => notas comparáveis)
  4. re-aplica o filtro de idioma (remove inglês avançado/fluente obrigatório)
  5. grava universo + planilha unificada (gerar_remote.py) + fila de inscrição (fila_inscricao.py)

Uso:
    python consolidar_fontes.py            # roda o pipeline completo
    python consolidar_fontes.py --sem-fila # só consolida e gera planilha
"""
import argparse
import glob
import json
import os
import re
import subprocess
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)
from reclass_remote import pontuar_lote, filtrar_idioma  # noqa: E402

LINKEDIN_FILTRADO = os.path.join(BASE, "vagas_remote_final_sem_ingles_avancado.json")
LINKEDIN_COMPLETO = os.path.join(BASE, "vagas_remote_idiomas.json")
DIR_FONTES = os.path.join(BASE, "fontes")
UNIVERSO = os.path.join(BASE, "vagas_universo.json")
REMOVIDAS_IDIOMA = os.path.join(BASE, "universo_removidas_por_idioma.json")


def _slug_titulo(t):
    t = re.sub(r"\(.*?\)", " ", (t or "").lower())
    t = re.sub(r"\b(sr|s\.?r\.?|senior|sênior|pleno|junior|especialista|iii|ii|iv|l\d+)\b", " ", t)
    return re.sub(r"[^a-z0-9áéíóúâêôãõçü]+", "-", t).strip("-")


def _empresa_base(e):
    e = re.sub(r"[^a-z0-9 ]+", " ", (e or "").lower())
    e = re.sub(r"\b(ltda|sa|s\.a|inc|llc|spa|eirl|me|brasil|do brasil|group|grupo|tech)\b", " ", e)
    partes = [w for w in e.split() if len(w) > 2]
    return "-".join(partes[:2])


def url_key(link):
    return re.sub(r"[?#].*$", "", (link or "")).rstrip("/")


def par_key(v):
    return f"{_empresa_base(v.get('empresa'))}||{_slug_titulo(v.get('titulo'))}"


def carregar_linkedin():
    """Usa o lote já baixado/validado; se não existir, nada é perdido — só não há LinkedIn."""
    for caminho in (LINKEDIN_FILTRADO, LINKEDIN_COMPLETO):
        if os.path.exists(caminho):
            with open(caminho, encoding="utf-8") as f:
                dados = json.load(f)
            for v in dados:
                v["_fonte"] = v.get("_fonte") or "LinkedIn"
            print(f"[linkedin] {os.path.basename(caminho)}: {len(dados)} vagas")
            return dados
    print("[linkedin] base local não encontrada — consolidando só as importações")
    return []


def carregar_importacoes():
    out = []
    arquivos = sorted(glob.glob(os.path.join(DIR_FONTES, "*.json")))
    if not arquivos:
        print("[imports] nenhum arquivo em remote_latam/fontes/ — rode importar_indeed.py <arquivo>")
    for arq in arquivos:
        try:
            dados = json.load(open(arq, encoding="utf-8"))
        except Exception as exc:
            print(f"[aviso] {os.path.basename(arq)} ignorado: {exc}")
            continue
        if not isinstance(dados, list):
            print(f"[aviso] {os.path.basename(arq)} não é uma lista — ignorado")
            continue
        nome = os.path.basename(arq)
        for v in dados:
            v.setdefault("_fonte", "Indeed" if "indeed" in nome.lower() else "Importada")
            v["_origem_arquivo"] = nome
        print(f"[imports] {nome}: {len(dados)} vagas")
        out.extend(dados)
    return out


def consolidar():
    linkedin = carregar_linkedin()
    imports = carregar_importacoes()

    universo, urls, pares, dup = [], set(), set(), 0
    for v in linkedin + imports:
        uk, pk = url_key(v.get("link")), par_key(v)
        if not uk.startswith("http") or uk in urls or pk in pares:
            dup += 1
            continue
        urls.add(uk)
        pares.add(pk)
        universo.append(v)
    print(f"Deduplicação: {dup} registros repetidos/cross-postados descartados | únicos: {len(universo)}")

    # nota recalculada sobre o lote combinado -> Indeed e LinkedIn na mesma régua
    pontuar_lote(universo)
    for v in universo:
        t = (v.get("titulo", "") + " " + v.get("descricao", "")).lower()
        v["_lang_en"] = any(k in t for k in ("english", "inglês fluente", "inglés fluido"))
        v["_lang_es"] = any(k in t for k in ("español", "espanhol", "spanish", "latinoamérica"))

    mantidas, removidas = filtrar_idioma(universo)
    print(f"Filtro de idioma: {len(removidas)} removidas por exigir inglês avançado/fluente | "
          f"{len(mantidas)} mantidas")

    json.dump(mantidas, open(UNIVERSO, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    json.dump(removidas, open(REMOVIDAS_IDIOMA, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    from collections import Counter
    print("Fontes no universo:", Counter(v["_fonte"] for v in mantidas).most_common())
    print("Países:", dict(Counter(v["pais"] for v in mantidas).most_common()))
    print("Nota ≥80:", sum(1 for v in mantidas if v["nota"] >= 80))
    return mantidas


def rodar(script, *args):
    cmd = [sys.executable, os.path.join(BASE, script), *args]
    print("\n$ " + " ".join(os.path.basename(c) for c in cmd))
    r = subprocess.run(cmd, cwd=BASE)
    if r.returncode != 0:
        print(f"[aviso] {script} terminou com código {r.returncode}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sem-fila", action="store_true")
    ap.add_argument("--sem-planilha", action="store_true")
    args = ap.parse_args()

    consolidar()
    if not args.sem_planilha:
        rodar("gerar_remote.py")           # lê fontes/*.json + LinkedIn -> xlsx/csv unificado
        rodar("gerar_sem_ingles.py")       # visões HTML/CSV auditáveis do universo
    if not args.sem_fila:
        rodar("fila_inscricao.py")         # fila pronta p/ JobSpy (só Easy Apply LinkedIn)
    print("\nUniverso consolidado em:", UNIVERSO)


if __name__ == "__main__":
    main()
