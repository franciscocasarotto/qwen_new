#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
fila_inscricao.py — Pré-processador da campanha de candidatura automática.

Lê o resultado validado (657 vagas remotas LATAM sem inglês avançado obrigatório)
e produz uma FILA ORDENADA pronta para execução pelo JobSpy (linkedin-jobs-api),
com limites de segurança anti-ban embutidos.

Uso:
    python fila_inscricao.py                 # gera fila_completa.csv + fila_top50.csv
    python fila_inscricao.py --min-nota 90   # só vagas nota >= 90

IMPORTANTE: este script NÃO faz login nem envia candidaturas. Ele apenas
prepara a lista que será executada por você, com suas credenciais, na sua máquina.
"""
import argparse
import csv
import json
import os
import re
from datetime import datetime

BASE = os.path.dirname(os.path.abspath(__file__))
FONTE = os.path.join(BASE, "vagas_universo.json")   # gerado por consolidar_fontes.py
FONTE_LINKEDIN_ONLY = os.path.join(BASE, "vagas_remote_final_sem_ingles_avancado.json")

# ----- Limites de segurança (anti-ban do LinkedIn) --------------------------
MAX_CANDIDATURAS_DIA = 25          # acima disso o risco de restrição sobe muito
PAUSA_MIN_ENTRE_ACOES = (45, 120)  # segundos aleatórios entre cliques
MAX_DIAS_EM_FILA = 7               # espalhar as top 150 em ~1 semana

# Vagas "Presencial (revisar)" não são remotas -> fora da campanha, exceto BR
MODO_BLOQUEADO = {"Presencial (revisar)"}


def carregar():
    caminho = FONTE if os.path.exists(FONTE) else FONTE_LINKEDIN_ONLY
    with open(caminho, encoding="utf-8") as f:
        dados = json.load(f)
    print(f"Fonte da fila: {os.path.basename(caminho)} ({len(dados)} vagas)")
    return dados


def eh_facil(v):
    """Heurística Easy Apply: URL padrão /jobs/view/ do LinkedIn."""
    return "/jobs/view/" in v.get("link", "")


def _tem(t, *termos):
    """Match por token (evita falsos positivos como 'ia' dentro de 'via')."""
    toks = set(re.findall(r"[a-záéíóúâêôãõçü]+", t))
    return any(termo in toks or termo in t.split() for termo in termos)


def keywords(v):
    t = (v.get("titulo") or "").lower()
    kw = []
    if any(k in t for k in ("arquiteto", "architect", "arquitecto")):
        kw.append("cloud architect")
    if any(k in t for k in ("dados", "data", "datos")):
        kw.append("data")
    if any(k in t for k in ("finops", "cost")):
        kw.append("finops")
    if "sap" in t:
        kw.append("sap")
    if any(k in t for k in ("gerente", "head", "director", "lead", "coorden", "jefe")):
        kw.append("leadership")
    if _tem(t, "ai", "ia", "inteligencia", "inteligência", "machine", "learning", "ml", "ml"):
        kw.append("ai")
    return ",".join(kw) or "general"


def montar_fila(min_nota=80):
    vagas = carregar()
    fila = []
    for v in vagas:
        if v.get("nota", 0) < min_nota:
            continue
        if v.get("modo") in MODO_BLOQUEADO and v.get("pais") != "BR":
            # presencial fora do Brasil não atende ao pedido "remotas"
            continue
        fila.append({
            "prioridade": 0,  # preenchido abaixo
            "nota": v.get("nota", 0),
            "empresa": v.get("empresa", ""),
            "cargo": v.get("titulo", ""),
            "pais": v.get("pais", ""),
            "local": v.get("local", ""),
            "modo": v.get("modo", ""),
            "publicada": v.get("data", ""),
            "easy_apply_provavel": "SIM" if eh_facil(v) else "NAO",
            "facilitated_keywords": keywords(v),
            "link": v.get("link", ""),
            "fonte": v.get("_fonte", "LinkedIn"),
            "candidatura": ("Easy Apply (automação JobSpy)" if "/jobs/view/" in v.get("link", "")
                            and v.get("_fonte", "LinkedIn") == "LinkedIn"
                            else "Externo — formulário manual (Indeed/GATS)"),
            "status": "PENDENTE",
        })
    # ordenar: nota desc, depois priorizar remoto confirmado > filtro linkedin
    ordem_modo = {"Remoto confirmado": 0, "Remoto (filtro LinkedIn)": 1}
    fila.sort(key=lambda x: (-x["nota"], ordem_modo.get(x["modo"], 2)))
    for i, v in enumerate(fila, 1):
        v["prioridade"] = i
    return fila


def gravar_csv(nome, linhas):
    path = os.path.join(BASE, nome)
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=list(linhas[0].keys()), delimiter="|")
        w.writeheader()
        w.writerows(linhas)
    return path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--min-nota", type=int, default=80)
    args = ap.parse_args()

    fila = montar_fila(args.min_nota)
    p_all = gravar_csv("fila_completa.csv", fila)
    p_top = gravar_csv("fila_top50.csv", fila[:50])

    dias = max(1, -(-len(fila[:150]) // MAX_CANDIDATURAS_DIA))
    print(f"Fila gerada: {len(fila)} vagas (nota >= {args.min_nota})")
    print(f"  - {p_all}")
    print(f"  - {p_top}  (lote recomendado para começar)")
    print(f"Segurança: máx {MAX_CANDIDATURAS_DIA}/dia | pausa {PAUSA_MIN_ENTRE_ACOES}s "
          f"| top150 espalhadas em ~{dias} dias")
    print(f"Gerado em {datetime.now():%Y-%m-%d %H:%M}")


if __name__ == "__main__":
    main()
