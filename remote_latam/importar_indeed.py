#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
importar_indeed.py — Importador da lista Indeed (e de qualquer fonte externa) para a base unificada.

Por que este arquivo existe
---------------------------
O Indeed bloqueia raspagem neste ambiente (HTTP 403 Cloudflare em www./br./ar.
inclusive nos feeds públicos /rss e /feeds/lcp). Portanto as vagas do Indeed só
entram na campanha se vierem de um arquivo exportado por você (planilha, CSV,
JSON ou HTML salvo do navegador). Este script NORMALIZA esse arquivo e aplica o
MESMO pipeline já usado no LinkedIn: pontuação -> nota 0-100 -> validação de
idioma (remove inglês avançado/fluente obrigatório) -> fila de inscrição.

Uso
---
    python importar_indeed.py <arquivo> [--pais BR] [--debug]

Formatos aceitos: .csv .tsv .xlsx .xls .json .html
Colunas reconhecidas (sinônimos, sem acento):
    link/url/vaga/job link | empresa/company/nome da empresa | titulo/cargo/role/job title
    local/location/cidade | data/posted/publicada | descricao/description/detalhes | pais/country
Critério de detecção da fonte: se o domínio for indeed -> fonte "Indeed", senão "Outra".

Saídas:
    imported_raw.json          (registro cru normalizado, com _fonte)
    imported_pontuadas.json    (com nota e campos de idioma)
    console: resumo + quantas foram removidas por idioma
"""
import argparse
import json
import os
import re
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

import pandas as pd  # noqa: E402
from reclass_remote import pontuar_lote, filtrar_idioma  # noqa: E402

CAMPOS = {
    "link": ["link", "url", "link da vaga", "job link", "linkvaga", "vaga"],
    "empresa": ["empresa", "company", "company name", "nome da empresa", "organizacao", "organização"],
    "titulo": ["titulo", "título", "cargo", "role", "job title", "title", "position", "postura"],
    "local": ["local", "location", "cidade", "localidade", "localizacao", "localização"],
    "data": ["data", "posted", "publicada", "date posted", "data de publicacao", "data de publicação"],
    "descricao": ["descricao", "descrição", "description", "detalhes", "job description", "jd", "texto"],
    "pais": ["pais", "país", "country", "pais (sigla)"],
    "modo": ["modo", "work mode", "tipo de trabalho", "regime", "modelo"],
}


def _norm_col(c):
    s = str(c).strip().lower()
    s = re.sub(r"[_\-.]+", " ", s)
    return s


def mapear(df):
    """Devolve dict {campo_canonico: nome_real_da_coluna}."""
    out = {}
    cols = {c: _norm_col(c) for c in df.columns}
    for canon, aliases in CAMPOS.items():
        best = None
        for real, n in cols.items():
            if n == canon or n in aliases:
                best = real
                break
        if best is None:
            for real, n in cols.items():
                if any(a in n for a in aliases):
                    best = real
                    break
        if best is not None:
            out[canon] = best
    return out


def carregar_arquivo(path):
    ext = os.path.splitext(path)[1].lower()
    if ext in (".xlsx", ".xls"):
        return pd.read_excel(path, dtype=str)
    if ext == ".json":
        with open(path, encoding="utf-8") as f:
            dados = json.load(f)
        if isinstance(dados, dict):
            dados = dados.get("vagas") or dados.get("results") or dados.get("data") or list(dados.values())[0]
        return pd.DataFrame(dados, dtype=str)
    if ext == ".html":
        tables = pd.read_html(path)
        if not tables:
            raise SystemExit("Nenhuma <table> encontrada no HTML. Exporte como CSV/XLSX.")
        return max(tables, key=len).astype(str)
    if ext in (".txt", ""):
        return pd.read_csv(path, dtype=str, sep=None, engine="python")
    sep = "\t" if ext == ".tsv" else None
    return pd.read_csv(path, dtype=str, sep=sep, engine="python")


PAIS_POR_SIGLA = {"brazil": "BR", "brasil": "BR", "argentina": "AR", "chile": "CL",
                  "colombia": "CO", "colômbia": "CO", "peru": "PE", "perú": "PE",
                  "ecuador": "EC", "uruguay": "UY", "uruguai": "UY", "venezuela": "VE",
                  "bolivia": "BO", "bolívia": "BO", "paraguay": "PY", "costa rica": "CR",
                  "mexico": "MX", "méxico": "MX", "republica dominicana": "DO"}
CIDADE_PAIS = {  # heurística: a coluna "Local" do Indeed costuma trazer cidade/país
    "BR": ("são paulo", "sao paulo", "campinas", "bragança", "braganca", "rio de janeiro",
           "belo horizonte", "curitiba", "porto alegre", "recife", "florianópolis", "brasília",
           "salvador", "fortaleza", "barueri", "osasco", "santa catarina", "minas gerais",
           "paraná", "parana", "rio grande do sul", "bahia", "pernambuco", "ceará", "ceara"),
    "AR": ("buenos aires", "córdoba", "cordoba", "rosario", "mendoza", "argentina"),
    "CL": ("santiago", "valparaíso", "valparaiso", "concepción", "chile"),
    "CO": ("bogotá", "bogota", "medellín", "medellin", "cali", "cartagena", "colômbia", "colombia"),
    "PE": ("lima", "arequipa", "peru", "perú"),
    "EC": ("quito", "guayaquil", "equador", "ecuador"),
    "UY": ("montevideo", "uruguai", "uruguay"),
    "VE": ("caracas", "valencia", "venezuela"),
    "BO": ("la paz", "lapaz", "santa cruz", "cochabamba", "bolívia", "bolivia"),
    "PY": ("asunción", "asuncion", "paraguai", "paraguay"),
}


def inferir_pais(pais_raw, local, default):
    """Sigla > nome por extenso > cidade no campo Local > default."""
    s = (pais_raw or "").strip().lower()
    if len(s) == 2 and s.isalpha():
        return s.upper()
    if s in PAIS_POR_SIGLA:
        return PAIS_POR_SIGLA[s]
    texto = f"{local} {pais_raw}".lower()
    for sigla, cidades in CIDADE_PAIS.items():
        if any(c in texto for c in cidades):
            return sigla
    return (default or "BR").upper()


def _slug_titulo(t):
    t = re.sub(r"\(.*?\)", " ", (t or "").lower())
    t = re.sub(r"\b(sr|s\.?r\.?|senior|sênior|pleno|junior|especialista|iii|ii|iv|l\d+)\b", " ", t)
    t = re.sub(r"[^a-z0-9áéíóúâêôãõçü]+", "-", t)
    return t.strip("-")


def _empresa_base(e):
    e = re.sub(r"[^a-z0-9 ]+", " ", (e or "").lower())
    e = re.sub(r"\b(ltda|sa|s\.a|inc|llc|spa|eirl|me|brasil|do brasil|group|grupo|tech)\b", " ", e)
    partes = [w for w in e.split() if len(w) > 2]
    return "-".join(partes[:2])


def carregar_chaves_linkedin():
    """Índices das 657 vagas LinkedIn já validadas -> evita contar a mesma vaga 2x.
    Retorna (chaves de URL, índice empresa+cargo normalizado)."""
    urls, indice = set(), set()
    caminho = os.path.join(BASE, "vagas_remote_final_sem_ingles_avancado.json")
    try:
        with open(caminho, encoding="utf-8") as f:
            for v in json.load(f):
                u = re.sub(r"[?#].*$", "", (v.get("link") or "")).rstrip("/")
                if u:
                    urls.add(u)
                st, eb = _slug_titulo(v.get("titulo")), _empresa_base(v.get("empresa"))
                if st and eb:
                    indice.add(f"{eb}||{st}")
    except FileNotFoundError:
        pass
    return urls, indice


_LI_URLS, _LI_INDICE = carregar_chaves_linkedin()


def chave_url(link):
    return re.sub(r"[?#].*$", "", link).rstrip("/")


def chave_par(empresa, titulo):
    return f"{_empresa_base(empresa)}||{_slug_titulo(titulo)}"


def detectar_fonte(link):
    l = (link or "").lower()
    if "indeed." in l:
        return "Indeed"
    if "linkedin." in l:
        return "LinkedIn"
    if "gupy" in l or "cumpanite" in l:
        return "Gupy"
    if "workday" in l or "myworkdayjobs" in l:
        return "Workday"
    if "lever" in l or "greenhouse" in l:
        return "Lever/Greenhouse"
    return "Outra"


def normalizar(df, pais_default, debug=False):
    mapa = mapear(df)
    obrigatorios = {"link", "titulo"}
    faltando = obrigatorios - set(mapa)
    if faltando:
        print("Colunas não encontradas:", faltando)
        print("Colunas detectadas:", dict(mapa))
        raise SystemExit("Ajuste o cabeçalho do arquivo (ou me envie as 3 primeiras linhas).")
    print("Mapeamento de colunas:", json.dumps(mapa, ensure_ascii=False))

    registros, vistos, duplicadas_fonte = [], set(), 0
    for _, row in df.iterrows():

        def get(campo):
            col = mapa.get(campo)
            if col is None:
                return ""
            val = row.get(col)
            if val is None or (isinstance(val, float) and pd.isna(val)):
                return ""
            s = str(val).strip()
            return "" if s.lower() in ("nan", "none", "null") else s

        link = get("link")
        if not link.startswith("http"):
            continue
        titulo = get("titulo")
        empresa = get("empresa") or "(empresa não informada)"
        cu, cp = chave_url(link), chave_par(empresa, titulo)
        if cu in vistos:
            continue
        vistos.add(cu)
        if cu in _LI_URLS or cp in _LI_INDICE:   # mesma vaga já está na base LinkedIn
            duplicadas_fonte += 1
            continue

        local = get("local") or pais_default
        desc = get("descricao")
        pais = inferir_pais(get("pais"), local, pais_default)

        registros.append({
            "titulo": titulo,
            "empresa": empresa,
            "local": local,
            "data": get("data"),
            "link": link,
            "pais": pais,
            "eixo": "indeed-import" if detectar_fonte(link) == "Indeed" else "import",
            "descricao": desc or titulo,
            "modo": get("modo") or "Remoto (a confirmar)",
            "_fonte": detectar_fonte(link),
            "_raw_desc_len": len(desc),
        })
        if debug and len(registros) >= 5:
            break
    print(f"Já presentes na base LinkedIn (ignoradas para não inflar a nota): {duplicadas_fonte}")
    return registros


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("arquivo")
    ap.add_argument("--pais", default="BR", help="sigla ISO usada quando o arquivo não traz país")
    ap.add_argument("--debug", action="store_true")
    ap.add_argument("--saida", default=os.path.join(BASE, "indeed_importadas.json"))
    args = ap.parse_args()

    df = carregar_arquivo(args.arquivo)
    print(f"Linhas lidas: {len(df)}")
    regs = normalizar(df, args.pais, args.debug)
    print(f"Registros válidos únicos: {len(regs)}")
    from collections import Counter
    print("Por fonte:", Counter(r["_fonte"] for r in regs).most_common())

    if args.debug:
        print(json.dumps(regs[:2], ensure_ascii=False, indent=1)[:1500])
        return

    # ---- mesmo pipeline do LinkedIn -------------------------------------
    pontuar_lote(regs)                       # adds _pts/_bonus/_hits/_gap_pen/nota
    mantidas, removidas = filtrar_idioma(regs)

    with open(args.saida, "w", encoding="utf-8") as f:
        json.dump(mantidas, f, ensure_ascii=False, indent=1)
    with open(os.path.join(BASE, "imported_pontuadas.json"), "w", encoding="utf-8") as f:
        json.dump(regs, f, ensure_ascii=False, indent=1)

    print(f"Nota>=80: {sum(1 for v in mantidas if v['nota'] >= 80)} | removidas por inglês avançado: {len(removidas)}")
    print("Salvo em:", args.saida)
    top = sorted(mantidas, key=lambda z: -z["nota"])[:15]
    for x in top:
        print(f'{x["nota"]:>2} | {x["_fonte"]:<7} | {x["pais"]} | {x["empresa"][:26]:<26} | {x["titulo"][:46]}')


if __name__ == "__main__":
    main()
