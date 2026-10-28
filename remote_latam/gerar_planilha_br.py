# -*- coding: utf-8 -*-
"""Planilha final: vagas REMOTAS BRASIL validadas, ordenadas por compatibilidade."""
import json, re, csv, datetime
from collections import Counter
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

V = json.load(open("br_remoto_final.json"))
REMOVIDAS = json.load(open("br_remoto_removidas_ingles.json"))
V.sort(key=lambda z: (-z["nota"], z["data"]))

# ---------------------------------------------------------------- CV -> ajuste
EIXOS = {
 "IA/DADOS": ["inteligência artificial","inteligencia artificial","machine learning"," llm","rag",
              "genai","generativa","databricks","pyspark","dataops","data lake","datalake","lakehouse",
              "ia generativa","dados","analytics","big data","etl","langchain"],
 "FINOPS":   ["finops","custo","cost optimization","otimiza","orçament","budget","p&l","billin"],
 "ITSM/GEST":["itsm","servicenow","service now","itil","service desk","sla","ola","mttr","war room","nps",
              "gerente de projetos","gestor","pmo","pmbok","stakeholder","coordenac"],
 "SEGUR":    ["segurança","seguranca","security","ccsp","devsecops","waf","fortinet","soc ","siem","compliance","iso 27"],
}
def eixos_da(texto):
    t = texto.lower(); out=[]
    for nome, kws in EIXOS.items():
        if any(k in t for k in kws): out.append(nome)
    return out or ["CLOUD"]

GAPS = {"kubernetes":"Kubernetes (CKA)","cks":"CKS","openshift":"OpenShift","helm":"Helm","gitops":"GitOps/ArgoCD",
        "argo":"GitOps/ArgoCD","airflow":"Airflow","dbt":"dbt","snowflake":"Snowflake","splunk":"Splunk",
        "prometheus":"Prometheus","entra id":"Entra ID/IAM","active directory":"AD/Entra","pentest":"Pentest",
        "penetration test":"Pentest","threat modeling":"Threat Modeling","java":"Java",".net":".NET",
        "power bi":"Power BI","dynamics":"Dynamics 365"}

def mudancas(v):
    t = (v["titulo"] + " " + v.get("descricao","")).lower()
    ex = eixos_da(t); hits = [h[0] for h in v.get("_hits",[])]
    p = []
    # 1. Espelho escolhido
    esp = {"IA/DADOS":"ESPELHO #3 (IA & Dados)", "ITSM/GEST":"ESPELHO #2 (Gestão de TI / ITSM)",
           "FINOPS":"ESPELHO #1 (Cloud + FinOps)", "SEGUR":"ESPELHO #4 (Segurança/DevSecOps)",
           "CLOUD":"ESPELHO #1 (Cloud + FinOps)"}
    p.append(esp[ex[0]])
    # 2. Titulo do CV
    titulo = {"IA/DADOS":"'Arquiteto de Soluções de IA e Dados — LLM/RAG, Databricks, DataOps'",
              "ITSM/GEST":"'Líder de TI e Gestor de Serviços (ITSM/ITIL, ServiceNow, PMP) com background em Cloud'",
              "FINOPS":"'Arquiteto de Soluções Cloud & FinOps (FOCP, AZ-305, AWS SA)'",
              "SEGUR":"'Arquiteto de Soluções Cloud & Segurança (CCSP/CCSK, Security by Design)'",
              "CLOUD":"'Arquiteto de Soluções Multi-Cloud (Azure/AWS/GCP/OCI)'"}
    p.append("Título do CV → " + titulo[ex[0]])
    # 3. Keywords a subir para o topo
    top_k = [h for h in hits[:6]]
    if top_k: p.append("Subir p/ Core Competencies: " + ", ".join(sorted(set(top_k))[:6]))
    # 4. Métricas exigidas
    metricas = []
    if re.search(r"custo|cost|finops|budget|otimiz", t): metricas.append("R$/% de redução de OPEX")
    if re.search(r"sla|disponibil|uptime|alta disponibilidade", t): metricas.append("% de SLA/disponibilidade")
    if re.search(r"mttr|incident|estabilidad|sre", t): metricas.append("% de queda de MTTR")
    if re.search(r"nps|satisfa|cliente", t): metricas.append("pontos de NPS")
    if re.search(r"prazo|entrega|deadline|lead time", t): metricas.append("% de aderência a prazo/escopo")
    if metricas: p.append("Preencher métricas: " + "; ".join(metricas[:3]))
    # 5. Gaps
    g = sorted({nome for kw,nome in GAPS.items() if kw in t})
    if g: p.append("⚠ Gap no CV (" + ", ".join(g[:4]) + ") → adicionar certificação/prova ou omitir se não tiver")
    # 6. Extras especificos
    if "sap" in t: p.append("Puxar cases SAP (BTP/CPI/HANA/Fiori) da Nexa e Indra para o 1º terço do CV")
    if "oci" in t or "oracle" in t: p.append("Nomear serviços OCI usados (VCN, OKE, Autonomous)")
    if "pre-venda" in t or "presales" in t or "pré vendas" in t or "proposta" in t:
        p.append("Criar bloco 'Presales/Proposta Técnica': sizing, BOM, estimativas e win rate")
    if any(x in t for x in ("lider","head","gerente","gestor","coordena")):
        p.append("Detalhar governança: tamanho de time, budget gerenciado, rituais e comitês")
    if "azure" in t and "aws" not in t: p.append("Enxugar menções a GCP/OCI; concentrar 70% do CV em Azure")
    if "aws" in t and "azure" not in t: p.append("Enxugar Azure; reforçar AWS SA + Well-Architected")
    if v.get("_idioma_classe") == "MANTER_LEITURA_OU_BAICO":
        p.append("Inglês: manter versão PT + linha 'leitura técnica avançada' (não prometer conversação)")
    if v.get("_idioma_classe") == "MANTER_DESEJAVEL":
        p.append("Inglês é diferencial: citar Certificações em inglês (PMP/AZ-305) como evidência")
    return " • ".join(p)

def justificativa(v):
    hits = sorted(set(h[0] for h in v.get("_hits",[])[:8]))
    partes = []
    if hits: partes.append("Match de palavras-chave: " + ", ".join(hits[:6]).title())
    b = v.get("_bonus",0)
    if b >= 20: partes.append("Senioridade alinhada (arquétipo Sr/Especialista/Head)")
    gp = v.get("_gap_pen",0)
    if gp >= 12: partes.append(f"Penalidade de gap técnico −{gp}")
    elif gp: partes.append(f"Gaps leves −{gp}")
    partes.append("BR = contrato local, sem barreira de fuso/visto")
    return " | ".join(partes)

# ---------------------------------------------------------------- XLSX
wb = openpyxl.Workbook(); ws = wb.active; ws.title = "Vagas BR Remoto"
HDR = ["Prior.","Nota","Empresa","Cargo","Publicada","Local","Modo de trabalho","Link validado (LinkedIn)",
       "Status do link","Justificativa da compatibilidade","Mudanças necessárias no currículo"]
ws.append(HDR)
thin = Border(*[Side(style="thin", color="D9D9D9")]*4)
for c,_ in enumerate(HDR,1):
    cell = ws.cell(1,c); cell.font = Font(bold=True,color="FFFFFF",size=10)
    cell.fill = PatternFill("solid",fgColor="1F3864"); cell.alignment = Alignment(vertical="center",wrap_text=True)
green = PatternFill("solid",fgColor="C6EFCE"); yellow = PatternFill("solid",fgColor="FFEB9C"); red = PatternFill("solid",fgColor="FFC7CE")
for i,v in enumerate(V,1):
    st = "✅ ATIVA (HTTP 200)" if v.get("link_ok") else ("❌ " + str(v.get("motivo_morto","verificar")) if v.get("link_ok") is False else "⚠ SEM VERIFICACAO")
    ws.append([i, v["nota"], v["empresa"], v["titulo"], v.get("data",""), v.get("local",""),
               v.get("modo",""), v["link"], st, justificativa(v), mudancas(v)])
    r = ws.max_row
    ws.cell(r,2).fill = green if v["nota"]>=85 else (yellow if v["nota"]>=70 else red)
    ws.cell(r,2).font = Font(bold=True)
    lk = ws.cell(r,8); lk.hyperlink = v["link"]; lk.value = "abrir vaga"; lk.font = Font(color="0563C1",underline="single")
    for c in range(1,len(HDR)+1):
        ws.cell(r,c).alignment = Alignment(vertical="top", wrap_text=c in (4,10,11))
        ws.cell(r,c).border = thin
for col,w in zip("ABCDEFGHIJK",[6,6,26,42,11,26,20,12,18,52,72]): ws.column_dimensions[col].width = w
ws.freeze_panes = "C2"; ws.auto_filter.ref = f"A1:K{ws.max_row}"

# Aba 2 - TOP 30 fila de aplicacao
w2 = wb.create_sheet("TOP 30 - Aplicar já")
w2.append(["Ordem","Nota","Empresa","Cargo","Link","Deadline sugerida","Canal alternativo"])
for c in range(1,8):
    cell=w2.cell(1,c); cell.font=Font(bold=True,color="FFFFFF"); cell.fill=PatternFill("solid",fgColor="375623")
for i,v in enumerate(V[:30],1):
    dl = (datetime.date.fromisoformat(v["data"]) + datetime.timedelta(days=6)).isoformat() if v.get("data") else "—"
    w2.append([i,v["nota"],v["empresa"],v["titulo"],"abrir",dl,"buscar cargo similar na Gupy/portal da empresa"])
    lk=w2.cell(i+1,5); lk.hyperlink=v["link"]; lk.font=Font(color="0563C1",underline="single")
for col,w in zip("ABCDEFG",[6,6,26,42,10,16,44]): w2.column_dimensions[col].width=w

# Aba 3 - removidas por ingles
w3 = wb.create_sheet("Removidas (inglês obrig.)")
w3.append(["Empresa","Cargo","Evidência do requisito de inglês","Link"])
for c in range(1,5):
    cell=w3.cell(1,c); cell.font=Font(bold=True,color="FFFFFF"); cell.fill=PatternFill("solid",fgColor="833C00")
for v in sorted(REMOVIDAS,key=lambda z:-z["nota"]):
    w3.append([v["empresa"],v["titulo"],v.get("_idioma_evidencia",""),"abrir"])
    lk=w3.cell(w3.max_row,4); lk.hyperlink=v["link"]; lk.font=Font(color="0563C1",underline="single")
for col,w in zip("ABCD",[26,42,80,10]): w3.column_dimensions[col].width=w

# Aba 4 - metodologia
w4 = wb.create_sheet("Metodologia")
hoje = datetime.date.today().isoformat()
linhas = [
 ["PARÂMETRO","VALOR"],
 ["Fonte","LinkedIn Jobs Guest API (end point público, sem login)"],
 ["Geografia","Somente BRASIL (11 recortes: país + SP, Campinas, BH, RJ, CWB, POA, BSB, Floripa, Recife, Goiânia)"],
 ["Filtro remoto","f_WT=2 aplicado na busca + reclassificação textual da descrição"],
 ["Janela temporal","f_TPR=r1296000 = publicados nos últimos 15 dias"],
 ["Coletadas brutas", len(V)+len(REMOVIDAS)],
 ["Removidas: inglês avançado/fluente obrigatório", len(REMOVIDAS)],
 ["Removidas: link inválido/encerrado", sum(1 for x in V+REMOVIDAS if x.get('link_ok') is False)],
 ["Removidas: júnior/estágio/presencial", "ver log do pipeline"],
 ["LISTA FINAL", len(V)],
 ["Validação de link","GET HTTP em cada URL; só entra na lista quem respondeu 200 e tinha descrição legível"],
 ["Nota 0-100","Percentil interno do lote sobre (keywords do CV ponderadas + senioridade − penalidade de gap técnico)"],
 ["Critérios de idioma","Frase a frase: remove C1/C2/fluent/business-level/spoken required; mantém desejável, leitura técnica, básico/intermediário e curso de inglês como benefício"],
 ["Base de comparação","Versão Mestre (CV) + perfil público linkedin.com/in/francisco-casarotto"],
 ["Perfil público verificado","HTTP 200, headline 'Francisco Casarotto - Nexa Resources', idioma do perfil = PT-BR"],
 ["Data da execução", hoje],
 ["Re-executar","python coletar_br_remoto.py && python baixar_validar_br.py && python pipeline_br.py && python gerar_planilha_br.py"],
 ["Indeed","Bloqueio anti-bot (HTTP 403). Usar br.indeed.com/jobs?q=arquiteto+cloud&remote=1&fromage=15 e importar via importar_indeed.py"],
]
for row in linhas: w4.append(row)
for c in range(1,3):
    cell=w4.cell(1,c); cell.font=Font(bold=True,color="FFFFFF"); cell.fill=PatternFill("solid",fgColor="1F3864")
w4.column_dimensions["A"].width=46; w4.column_dimensions["B"].width=110
for r in range(1,w4.max_row+1): w4.cell(r,2).alignment=Alignment(wrap_text=True,vertical="top")

wb.save("/workspace/vagas_remotas_brasil_validadas.xlsx")

# CSV
with open("/workspace/vagas_remotas_brasil_validadas.csv","w",newline="",encoding="utf-8-sig") as f:
    wr=csv.writer(f,delimiter=";")
    wr.writerow(["Prioridade","Nota","Empresa","Cargo","Publicada","Local","Modo","Link","Status_link","Justificativa","Mudancas_CV"])
    for i,v in enumerate(V,1):
        wr.writerow([i,v["nota"],v["empresa"],v["titulo"],v.get("data",""),v.get("local",""),v.get("modo",""),
                     v["link"],"ATIVA" if v.get("link_ok") else "VERIFICAR",justificativa(v),mudancas(v)])

print("XLSX/CSV gravados.")
print("FINAL:", len(V), "| nota>=85:", sum(1 for x in V if x['nota']>=85), "| >=70:", sum(1 for x in V if x['nota']>=70))
print("modos:", dict(Counter(x['modo'] for x in V)))
print("links ativos:", sum(1 for x in V if x.get('link_ok')))
print("\nTOP 15:")
for i,v in enumerate(V[:15],1): print(f'{i:>2}. [{v["nota"]}] {v["empresa"][:28]:<28} {v["titulo"][:52]}')
