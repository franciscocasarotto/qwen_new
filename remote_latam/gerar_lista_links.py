#!/usr/bin/env python3
"""Gera LISTA DE LINKS do LinkedIn para validacao manual.

Fonte: br_remoto_final.json (761 vagas remotas BR, links ja revalidados HTTP 200,
ingles avancado/fluente obrigatorio removido).

Entregas em /workspace/remote_latam/:
  - lista_links_linkedin.html  -> pagina com checkboxes, filtro por nota e copia em lote
  - lista_links_linkedin.csv   -> planilha simples (nota, empresa, cargo, link)
  - lista_links_linkedin.txt   -> uma URL por linha (colar no navegador/ferramenta)
Ordenacao: mais compativeis primeiro (nota desc), depois data desc.
"""
import csv
import html
import json
import re
from collections import Counter
from pathlib import Path

BASE = Path(__file__).resolve().parent
SRC = BASE / "br_remoto_final.json"
OUT_HTML = BASE / "lista_links_linkedin.html"
OUT_CSV = BASE / "lista_links_linkedin.csv"
OUT_TXT = BASE / "lista_links_linkedin.txt"
OUT_MD = BASE / "TOP50_links_para_validar.md"

TOP_N_HTML = 120          # linhas renderizadas na aba principal (performance)
MIN_NOTA_HTML = 70         # corte de relevancia para a lista de validacao


def job_id(url: str) -> str:
    m = re.search(r"-(\d{8,})/?$", url or "")
    return m.group(1) if m else ""


def clean_url(url: str) -> str:
    """URL canonica do LinkedIn (sem traking/query)."""
    jid = job_id(url)
    return f"https://www.linkedin.com/jobs/view/{jid}/" if jid else url


def flat(s) -> str:
    """Colapsa espacos/quebras de linha (CSV e tabelas Markdown em 1 linha)."""
    return re.sub(r"\s+", " ", str(s or "")).strip()


def main() -> None:
    rows = json.loads(SRC.read_text(encoding="utf-8"))
    for v in rows:
        v["url_limpa"] = clean_url(v["link"])
        v["job_id"] = job_id(v["link"])

    rows.sort(key=lambda v: (-v["nota"], v.get("data") or "", v["empresa"]))
    keep = [v for v in rows if v["nota"] >= MIN_NOTA_HTML]
    shown = keep[:TOP_N_HTML]

    faixas = Counter()
    for v in keep:
        n = v["nota"]
        faixas["90-100" if n >= 90 else "80-89" if n >= 80 else "70-79"] += 1

    # ----------------------------- CSV --------------------------------------
    with OUT_CSV.open("w", newline="", encoding="utf-8-sig") as fh:
        w = csv.writer(fh, delimiter=";")
        w.writerow(["#", "Nota", "Empresa", "Cargo", "Local", "Modo",
                    "Publicada", "JobID", "Link para validar"])
        for i, v in enumerate(rows, 1):
            w.writerow([i, v["nota"], flat(v["empresa"]), flat(v["titulo"]), flat(v["local"]),
                        flat(v.get("modo", "")), flat(v.get("data", "")), v["job_id"],
                        v["url_limpa"]])

    # ----------------------------- TOP 50 (MD) --------------------------------
    OUT_MD = BASE / "TOP50_links_para_validar.md"
    with OUT_MD.open("w", encoding="utf-8") as fh:
        fh.write("# TOP 50 — Links LinkedIn para validação (Remoto · Brasil)\n\n")
        fh.write("Base: seu currículo (Arquitetura Cloud/FinOps · IA&Dados · Gestão de TI). "
                 "Filtros: últimos 15 dias, remoto BR, sem exigência de inglês avançado. "
                 "Ordenado por compatibilidade.\n\n")
        fh.write("| # | Nota (modo de trabalho) | Empresa | Cargo | Link |\n|---|---|---|---|---|\n")
        for i, v in enumerate(rows[:50], 1):
            t = flat(v["titulo"]).replace("|", "/")
            e = flat(v["empresa"]).replace("|", "/")
            fh.write(f"| {i} | {v['nota']} ({flat(v.get('modo', ''))}) | {e} | {t} | {v['url_limpa']} |\n")

    # ----------------------------- TXT --------------------------------------
    OUT_TXT.write_text("\n".join(v["url_limpa"] for v in rows) + "\n",
                       encoding="utf-8")

    # ----------------------------- HTML -------------------------------------
    def cor(n: int) -> str:
        return "#1e8e3e" if n >= 90 else "#f9ab00" if n >= 80 else "#a142f4" if n >= 70 else "#5f6368"

    trs = []
    for i, v in enumerate(shown, 1):
        c = cor(v["nota"])
        modo = v.get("modo", "")
        badge = ("<span class='ok'>REMOTO NA JD</span>" if "confirmado" in modo
                 else "<span class='warn'>HIBRIDO?</span>" if "brido" in modo else "")
        trs.append(
            f"<tr><td>{i}</td>"
            f"<td class='n' style='color:{c}'><b>{v['nota']}</b></td>"
            f"<td>{html.escape(str(v['empresa']))}</td>"
            f"<td>{html.escape(str(v['titulo']))} {badge}</td>"
            f"<td>{html.escape(str(v['local']))}</td>"
            f"<td>{v.get('data','')}</td>"
            f"<td><input type='checkbox' class='chk' data-url='{v['url_limpa']}' "
            f"data-t='{html.escape(v['titulo'], True)}|{html.escape(str(v['empresa']), True)}'>"
            f"<a href='{v['url_limpa']}' target='_blank' rel='noopener'>{v['url_limpa']}</a></td></tr>"
        )

    OUT_HTML.write_text(f"""<!doctype html><html lang="pt-br"><meta charset="utf-8">
<title>Links p/ validar - LinkedIn Remoto BR ({len(rows)} vagas)</title>
<style>
body{{font:14px/1.45 -apple-system,Segoe UI,Roboto,sans-serif;margin:0;background:#f6f8fa;color:#202124}}
header{{background:#0a66c2;color:#fff;padding:16px 22px}}
header h1{{margin:0 0 4px;font-size:19px}} header p{{margin:2px 0;font-size:13px;opacity:.92}}
.bar{{position:sticky;top:0;background:#fff;border-bottom:1px solid #dadce0;padding:10px 22px;display:flex;gap:10px;flex-wrap:wrap;align-items:center;z-index:5}}
.bar input,.bar select,.bar button{{padding:7px 10px;border:1px solid #dadce0;border-radius:6px;font-size:13px}}
.bar button{{background:#0a66c2;color:#fff;border:0;cursor:pointer}}
.bar button.g{{background:#fff;color:#0a66c2;border:1px solid #0a66c2}}
main{{padding:14px 22px 60px}}
table{{width:100%;border-collapse:collapse;background:#fff;box-shadow:0 1px 2px rgba(0,0,0,.08)}}
th,td{{padding:8px 10px;border-bottom:1px solid #eee;text-align:left;vertical-align:top}}
th{{background:#f1f3f4;position:sticky;top:56px;font-size:12px;text-transform:uppercase;letter-spacing:.3px}}
td.n{{font-size:16px;width:52px}} td:last-child{{word-break:break-all;font-size:12px}}
a{{color:#0a66c2;text-decoration:none}} a:hover{{text-decoration:underline}}
.ok{{background:#e6f4ea;color:#1e8e3e;font-size:10px;padding:2px 6px;border-radius:10px;font-weight:700}}
.warn{{background:#fef7e0;color:#b06000;font-size:10px;padding:2px 6px;border-radius:10px;font-weight:700}}
.chk{{margin-right:8px;transform:scale(1.25)}}
#count{{font-weight:700}} textarea{{width:100%;height:130px;font-family:ui-monospace,Menlo,monospace;font-size:11px;margin-top:8px}}
.box{{background:#fff;border:1px solid #dadce0;border-radius:8px;padding:12px;margin-top:14px}}
</style>
<header>
 <h1>Lista de links para valida&ccedil;&atilde;o &mdash; LinkedIn &middot; Remoto &middot; Brasil</h1>
 <p>Base do seu curr&iacute;culo (Arquitetura Cloud/FinOps/IA-Dados/Gest&atilde;o de TI) &middot; {len(rows)} vagas &middot; publicadas nos &uacute;ltimos 15 dias &middot; todos os links revalidados (HTTP 200)</p>
 <p>Filtros aplicados: remoto | Brasil | sem exig&ecirc;ncia de ingl&ecirc;s avan&ccedil;ado/fluente | nota de compatibilidade &ge; {MIN_NOTA_HTML} nesta tela ({len(keep)} vagas; exibindo as {len(shown)} primeiras)</p>
 <p>Faixas de nota &mdash; 90-100: {faixas['90-100']} &middot; 80-89: {faixas['80-89']} &middot; 70-79: {faixas['70-79']}</p>
</header>
<div class="bar">
 <input id="q" placeholder="filtrar por cargo ou empresa..." size="34">
 <select id="fn"><option value="0">todas as notas</option><option value="90">nota &ge; 90</option><option value="80">nota &ge; 80</option></select>
 <button onclick="marca()">Marcar vis&iacute;veis</button>
 <button class="g" onclick="limpa()">Desmarcar</button>
 <button onclick="copiar()">Copiar links marcados</button>
 <span id="count">0 marcadas</span>
</div>
<main>
<table id="t"><thead><tr><th>#</th><th>Nota</th><th>Empresa</th><th>Cargo</th><th>Local</th><th>Publicada</th><th>Link (marque o que validar)</th></tr></thead>
<tbody>
{''.join(trs)}
</tbody></table>
<div class="box"><b>Links marcados</b> (cole aqui ou use o bot&atildeo acima)<textarea id="out"></textarea></div>
<p style="font-size:12px;color:#5f6368">Lista completa das {len(rows)} vagas: <code>lista_links_linkedin.csv</code> (planilha) e <code>lista_links_linkedin.txt</code> (1 URL por linha).</p>
</main>
<script>
const t=document.getElementById('t'),q=document.getElementById('q'),fn=document.getElementById('fn');
function filt(){{const s=q.value.toLowerCase(),m=+fn.value;
 [...t.tBodies[0].rows].forEach(r=>{{const n=+r.cells[1].innerText;
 r.style.display=(r.innerText.toLowerCase().includes(s)&&n>=m)?'':'none';}});}}
q.oninput=filt; fn.onchange=filt;
function upd(){{const c=t.querySelectorAll('.chk:checked').length;document.getElementById('count').textContent=c+' marcadas';}}
function marca(){{[...t.tBodies[0].rows].forEach(r=>{{if(r.style.display!=='none')r.querySelector('.chk').checked=true;}});upd();}}
function limpa(){{t.querySelectorAll('.chk').forEach(c=>c.checked=false);upd();document.getElementById('out').value='';}}
function copiar(){{const l=[...t.querySelectorAll('.chk:checked')].map(c=>c.dataset.url);
 document.getElementById('out').value=l.join('\\n');navigator.clipboard&&navigator.clipboard.writeText(l.join('\\n'));upd();}}
t.addEventListener('change',upd);
</script></html>""", encoding="utf-8")

    print(f"HTML : {OUT_HTML} ({len(shown)} linhas exibidas de {len(keep)} com nota>={MIN_NOTA_HTML})")
    print(f"CSV  : {OUT_CSV} ({len(rows)} linhas)")
    print(f"TXT  : {OUT_TXT} ({len(rows)} URLs)")
    print(f"Faixas: {dict(faixas)}")


if __name__ == "__main__":
    main()
