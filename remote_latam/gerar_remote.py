# -*- coding: utf-8 -*-
"""Etapa 3 final LATAM REMOTO — gera XLSX + CSV.

Agora unifica QUALQUER fonte presente em /workspace/remote_latam/fontes/:
LinkedIn (coletado aqui) + Indeed/Gupy/outras (importadas via importar_indeed.py).
Rode com --test para gerar num arquivo de demonstração sem sobrescrever a base real.
"""
import argparse, glob, json, csv, os, re
from collections import Counter
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

NOMES_PAIS = {"AR": "Argentina", "BR": "Brasil", "CL": "Chile", "CO": "Colômbia", "PE": "Peru",
              "UY": "Uruguai", "PY": "Paraguai", "EC": "Equador", "BO": "Bolívia", "VE": "Venezuela"}
AP = argparse.ArgumentParser(description="Monta a planilha unificada (LinkedIn + Indeed)")
AP.add_argument("--saida-xlsx", default="/workspace/vagas_remotas_sul_america.xlsx")
AP.add_argument("--saida-csv", default="/workspace/vagas_remotas_sul_america.csv")
AP.add_argument("--fontes", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "fontes"))
AP.add_argument("--apenas-fonte", default=None, help="filtra por fonte (ex.: Indeed)")
AP_ARGS, _ = AP.parse_known_args()

FONTE_LINKEDIN = "/workspace/remote_latam/vagas_remote_final_sem_ingles_avancado.json"


def carregar_unificado():
    """LinkedIn validado + todos os imports (Indeed/Gupy/externos), deduplicado e repontuado junto."""
    from reclass_remote import pontuar_lote, filtrar_idioma
    conj, vistos = [], set()

    def add(v, fonte):
        u = re.sub(r"[?#].*$", "", (v.get("link") or "")).rstrip("/")
        if not u or u in vistos:
            return
        vistos.add(u)
        v["_fonte"] = v.get("_fonte") or fonte
        conj.append(v)

    try:
        for v in json.load(open(FONTE_LINKEDIN, encoding="utf-8")):
            add(v, "LinkedIn")
    except FileNotFoundError:
        pass

    for arq in sorted(glob.glob(os.path.join(AP_ARGS.fontes, "*.json"))):
        try:
            dados = json.load(open(arq, encoding="utf-8"))
        except Exception as exc:
            print(f"[aviso] {os.path.basename(arq)} ignorado: {exc}")
            continue
        for v in dados if isinstance(dados, list) else []:
            add(v, v.get("_fonte") or "Importada")

    # idioma: só entra quem já passou pelo filtro (o LinkedIn já veio filtrado)
    conj = [v for v in conj if not v.get("_idioma_remover")]
    if AP_ARGS.apenas_fonte:
        conj = [v for v in conj if v["_fonte"].lower() == AP_ARGS.apenas_fonte.lower()]

    # repontuação única sobre o lote combinado -> notas comparáveis entre fontes
    campos = ("titulo", "descricao", "pais", "local", "empresa", "link", "data", "modo")
    slim = [{k: v.get(k, "") for k in campos} for v in conj]
    for extra in ("_lang_en", "_lang_es"):
        for v, sl in zip(conj, slim):
            t = (v.get("titulo", "") + " " + v.get("descricao", "")).lower()
            sl[extra] = v.get(extra, any(k in t for k in
                                         (("english", "inglês fluente") if extra == "_lang_en"
                                          else ("español", "espanhol", "spanish", "latinoamérica"))))
    pontuar_lote(slim)
    for v, sl in zip(conj, slim):
        v.update({k: sl[k] for k in ("nota", "_pts", "_bonus", "_hits", "_gap_pen", "_lang_en", "_lang_es")})
    return conj


VAGAS = carregar_unificado()
print(f"Lote unificado: {len(VAGAS)} vagas | fontes: {Counter(x['_fonte'] for x in VAGAS).most_common()}")

TRAD = {
    "finops": "FinOps → trazer FOCP para a 1ª linha de certs e nomear Azure Cost Management + AWS Cost Explorer.",
    "cloud architect": "Arquitetura cloud → manter 'Multi-Cloud (Azure/AWS/GCP/OCI)' como 1ª linha das Core Competencies.",
    "solutions architect": "Solutions Architect → usar o termo exato 'Solutions Architect' no título do CV (ATS lê o cargo).",
    "solution architect": "Solutions Architect → usar o termo exato 'Solutions Architect' no título do CV.",
    "arquitecto": "Arquitecto → versão ES do CV com 'Arquitecto de Soluciones' no título.",
    "arquiteto": "Arquiteto de Soluções → espelhar o título da vaga na 1ª linha do CV.",
    "azure": "Azure → abrir o resumo com AZ-305 / Azure Solutions Architect Expert.",
    "aws": "AWS → reordenar stack com AWS SAAC02 na frente; traduzir termos Azure→AWS.",
    "gcp": "GCP → puxar GCP/BigQuery da Semad/CIMED para os dois primeiros bullets.",
    "oci": "OCI → nomear serviços usados (VCN, OKE, Autonomous): diferencial raro na LATAM.",
    "sap": "SAP → subir BTP/CPI/HANA/Fiori para a 1ª linha das competências.",
    "btp": "SAP BTP → detalhar nº de integrações CPI e Fiori apps entregues.",
    "hana": "HANA → detalhar dimensionamento on-prem/cloud conduzido (Nexa/Indra).",
    "basis": "SAP Basis → trocar narrativa de arquitetura por SO Linux/Windows + HANA + clusterização.",
    "kubernetes": "KUBERNETES exigido e ausente do CV → citar OKE/EKS/AKS reais ou evitar até ter evidência.",
    "terraform": "Terraform → nomear módulo/landing zone escrito por você (CV só diz 'IaC').",
    "ansible": "Ansible → nomear nas automações da CIMED.",
    "servicenow": "ServiceNow → subir ServiceNow/TopDesk (Nextios) para Core Competencies.",
    "itil": "ITIL → declarar certificação ITIL (Foundation/Intermediate); hoje é só keyword.",
    "itsm": "ITSM → criar seção dedicada 'IT Service Management' (ITIL/ServiceNow/SLA/OLA/KPI).",
    "databricks": "Databricks → consolidar as 3 passagens num bloco único 'Data & Analytics'.",
    "rag": "RAG → descrever 1 caso concreto com base documental e ganho medido.",
    "llm": "LLM → LLM/RAG da Semad no topo do resumo.",
    "machine learning": "ML → amarrar à acurácia [+X]% da Semad (preencher placeholder).",
    "data lake": "Data Lake → nomear camadas/capacidade e quem consome (BI/ML).",
    "snowflake": "SNOWFLAKE ausente do CV → priorizar JDs com Databricks ou citar equivalência honesta.",
    "airflow": "AIRFLOW ausente → ponte honesta: 'ADF / Databricks Workflows (equivalente a Airflow)'.",
    "dbt": "dbt ausente do stack de dados — lacuna real se a JD exigir transformação modular.",
    "power bi": "Power BI não consta do CV → citar dashboards sobre Databricks/ADF se existirem.",
    "microservicios": "Microsserviços → ligar a DDD/C4 + nº de serviços em produção.",
    "microsservi": "Microsserviços → ligar a DDD/C4 + nº de serviços em produção.",
    "devsecops": "DevSecOps → unir 'Security by Design' + CI/CD sob o termo DevSecOps.",
    "security": "Segurança → elevar CCSP/CCSK + Fortinet/WAF/Akamai (Nextios) para bloco visível.",
    "seguridad": "Seguridad → bloco 'Security by Design' com CCSP/CCSK + caso de remediação (CV ES).",
    "iam": "IAM/Zero Trust ausente do CV → gap real; citar Entra ID/IAM se tiver feito, senão evitar essas vagas.",
    "active directory": "AD/Entra ID não nomeados — lacuna real em vagas de infra.",
    "pentest": "Pentest/resposta a incidentes de segurança não documentados — lacuna real.",
    "splunk": "Splunk ausente (você tem Datadog/Dynatrace/Zabbix) → fazer ponte explícita no CV.",
    "prometheus": "Prometheus ausente → ponte: 'stack equivalente (Datadog/Zabbix/Grafana)'.",
    "observab": "Observabilidade → bloco unificado (Datadog, Dynatrace, Zabbix, Grafana) com escopo 24x7.",
    "sre": "SRE → converter war-rooms em bullet com MTTR e volume de incidentes P1.",
    "mttr": "MTTR → preencher % real de redução (Union It/CIMED).",
    "sla": "SLA → substituir placeholders por percentuais reais de atingimento.",
    "costo": "Costo → métrica real de economia no CV ES ([R$ X] preenchido).",
    "custo": "Custo → trocar [R$ X]/[X]% por números reais de economia.",
    "budget": "Budget → declarar orçamento gerenciado (US$/R$ M); CV não dimensiona.",
    "presupuesto": "Presupuesto → declarar budget gerenciado (US$/R$ M) no CV ES.",
    "p&l": "P&L → dimensionar o book da Nextios (nº de contas cloud/mês).",
    "lideraz": "Liderança → informar nº de pessoas lideradas (diretas/indiretas).",
    "lideran": "Liderança → informar nº de pessoas lideradas (diretas/indiretas).",
    "stakeholder": "Stakeholders → especificar nível (C-level, nº de áreas).",
    "nps": "NPS → preencher o [X] pontos da Indra com número real.",
    "pmp": "PMP → garantir PMP na 1ª linha de certs (vagas de gestão).",
    "english": "INGLÊS exigido → versão EN do CV sem placeholders antes de aplicar.",
    "inglés": "ESPANHOL exigido → versão ES do CV; sem ela a aplicação morre no RH.",
    "español": "ESPANHOL exigido → versão ES do CV obrigatória.",
    "latam": "LATAM → destacar atuação regional (Indra/multinacionais) como prova de escopo.",
    "latin america": "LATAM → destacar atuação regional multi-país.",
    "time zone": "Fuso → declarar disponibilidade GMT-3 e sobreposição com a equipe.",
    "travel": "Viagens → esclarecer disponibilidade presencial eventual (CV não menciona).",
}
WEIGHT = {"finops": 10, "kubernetes": 9, "oci": 9, "sap": 9, "btp": 9, "rag": 9, "iam": 8,
          "snowflake": 8, "airflow": 8, "pentest": 8, "inglés": 8, "español": 8, "english": 7,
          "servicenow": 8, "itsm": 8, "itil": 7, "databricks": 8, "microservicios": 7,
          "microsservi": 7, "custo": 7, "costo": 7, "mttr": 7, "sla": 7, "nps": 7, "pmp": 7,
          "p&l": 6, "lideraz": 6, "lideran": 6, "stakeholder": 6, "budget": 6, "presupuesto": 6,
          "security": 6, "seguridad": 6, "observab": 6, "sre": 6, "splunk": 6, "prometheus": 6,
          "dbt": 6, "power bi": 6, "active directory": 6, "devsecops": 6, "basis": 6, "hana": 6,
          "travel": 4, "time zone": 4, "latam": 5, "latin america": 5, "llm": 7,
          "machine learning": 6, "data lake": 6, "azure": 6, "aws": 6, "gcp": 6, "terraform": 6,
          "ansible": 5, "arquitecto": 6, "arquiteto": 6, "cloud architect": 6,
          "solutions architect": 6, "solution architect": 6}


def mudancas(x):
    t = (x["titulo"] + " " + x["descricao"]).lower()
    ach, vistos = [], set()
    for k, txt in TRAD.items():
        if k in t and txt not in vistos:
            vistos.add(txt); ach.append((WEIGHT.get(k, 4), txt))
    ach.sort(key=lambda a: -a[0])
    receitas = [a[1] for a in ach[:6]]

    def pontu(*keys):
        return sum(t.count(k) for k in keys)

    scores = {
        "#1 Cloud+FinOps": pontu("finops", "cloud", "cost", "custo", "costo", "migra", "migracion", "disponibilidad"),
        "#2 Gestão/ITSM": pontu("gest", "itsm", "servicenow", "itil", "nps", "stakeholder", "pmp", "gerente", "jefe", "lead", "head", "director"),
        "#3 IA/Dados": pontu("inteligencia artificial", "inteligência artificial", "llm", "rag", "genai", "machine learning", "databricks", "data lake", "etl", "datos"),
        "#4 SAP/Integração": pontu("sap", "btp", "hana", "basis", "mulesoft", "digibee", "erp"),
    }
    esp = max(scores, key=scores.get)
    titulos = {
        "#1 Cloud+FinOps": "ESPELHO #1 (Cloud+FinOps) → título: 'Arquiteto de Soluções Cloud & FinOps (FOCP, AZ-305, AWS SA)'; Nexa/CIMED como evidência principal.",
        "#2 Gestão/ITSM": "ESPELHO #2 (Gestão/ITSM) → título: 'Líder de TI & Gestão de Serviços (PMP, ITIL, FinOps)'; subir Indra/Nextios e cortar jargão de arquitetura.",
        "#3 IA/Dados": "ESPELHO #3 (IA/Dados) → título: 'Arquiteto de IA & Dados (RAG, LLM, Databricks)'; Semad como 1ª experiência.",
        "#4 SAP/Integração": "ESPELHO #4 (SAP/Integração) → título: 'Arquiteto de Soluções SAP BTP & Integração Híbrida'; Indra/Nexa como evidência.",
    }
    out = [titulos[esp]] + receitas
    if x["_lang_en"]:
        out.append("JD cita INGLÊS → anexar versão EN do CV.")
    if x["_lang_es"]:
        out.append("JD cita ESPANHOL → anexar versão ES do CV.")
    if x["pais"] != "BR":
        out.append(f"CONTRATO {NOMES_PAIS[x['pais']]}: esperar contractor internacional (Deel/EOR), negociar em US$ e declarar GMT-3.")
    if x["modo"].startswith(("Presencial", "Híbrido")):
        out.append("⚠ CONFIRMAR: o texto da JD menciona presença/híbrido apesar do filtro Remoto.")
    if x.get("_fonte") == "Indeed":
        out.append("INDEED → candidatura por site externo (não é Easy Apply): anexar CV em PDF, "
                   "preencher os campos de formulário e salvar a resposta de screening.")
    if x["nota"] < 50:
        out.append("PRIORIDADE BAIXA: não adapte o CV-mestre para esta vaga agora — dilui a narrativa sênior.")
    return " • ".join(out)


def justificativa(x):
    fortes = ", ".join(h[0] for h in x["_hits"][:6]) or "-"
    base = f"Sobreposição com a Versão Mestre: {fortes}."
    gaps = []
    t = (x["titulo"] + " " + x["descricao"]).lower()
    for kw, rot in [("kubernetes", "Kubernetes"), ("airflow", "Airflow"), ("snowflake", "Snowflake"),
                    ("dbt", "dbt"), ("iam", "IAM/Zero Trust"), ("active directory", "AD/Entra ID"),
                    ("pentest", "pentest"), ("splunk", "Splunk"), ("prometheus", "Prometheus"),
                    ("power bi", "Power BI")]:
        if kw in t and rot not in gaps:
            gaps.append(rot)
    if gaps:
        base += f" Gap real (−{x['_gap_pen']} pts): " + ", ".join(gaps[:4]) + "."
    if x["_lang_en"]:
        base += " Exige inglês."
    if x["_lang_es"]:
        base += " Exige espanhol."
    base += (" Brasil: contrato local, mesmo idioma/fuso — menor atrito." if x["pais"] == "BR"
             else f" {NOMES_PAIS[x['pais']]}: contratação internacional (fuso compatível).")
    return base


HEADERS = ["Nota", "Fonte", "Empresa", "Cargo", "País", "Modo", "Publicada em", "Local (Remoto)",
           "Idiomas exigidos", "Link da vaga", "Justificativa da Compatibilidade",
           "Mudanças necessárias no Currículo"]
wb = Workbook(); ws = wb.active; ws.title = "Remoto LATAM (ordenadas)"
hdr_fill = PatternFill("solid", fgColor="1F3864"); hdr_font = Font(color="FFFFFF", bold=True)
thin = Side(style="thin", color="BFBFBF"); border = Border(thin, thin, thin, thin)
for c, h in enumerate(HEADERS, 1):
    cell = ws.cell(row=1, column=c, value=h)
    cell.fill, cell.font, cell.border = hdr_fill, hdr_font, border
    cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)


def cor(n):
    if n >= 80:
        return PatternFill("solid", fgColor="C6EFCE")
    if n >= 60:
        return PatternFill("solid", fgColor="FFEB9C")
    return PatternFill("solid", fgColor="FFC7CE")


VAGAS.sort(key=lambda z: (-z["nota"], NOMES_PAIS[z["pais"]]))
linhas = []
for x in VAGAS:
    langs = " + ".join([l for l, f in [("Inglês", x["_lang_en"]), ("Espanhol", x["_lang_es"])] if f]) \
            or "Português/Inglês (padrão)"
    row = [x["nota"], x.get("_fonte", "LinkedIn"), x["empresa"], x["titulo"], NOMES_PAIS[x["pais"]],
           x["modo"], x["data"], x["local"], langs, x["link"], justificativa(x), mudancas(x)]
    linhas.append(row)
    r = ws.max_row + 1
    for c, val in enumerate(row, 1):
        cell = ws.cell(row=r, column=c, value=val); cell.border = border
        cell.alignment = Alignment(vertical="top", wrap_text=(c != 1))
        if c == 1:
            cell.fill, cell.font = cor(val), Font(bold=True)
            cell.alignment = Alignment(horizontal="center", vertical="center")
        if c == 10:
            cell.hyperlink = val; cell.font = Font(color="0563C1", underline="single")
for i, w in enumerate([6, 10, 24, 32, 11, 20, 12, 22, 18, 38, 46, 88], 1):
    ws.column_dimensions[get_column_letter(i)].width = w
ws.freeze_panes = "A2"; ws.auto_filter.ref = f"A1:L{ws.max_row}"

ws2 = wb.create_sheet("TOP 40 — Priorizar")
ws2.append(["#", "Nota", "Fonte", "Empresa", "Cargo", "País", "Idiomas", "Por que priorizar"])
for c in range(1, 9):
    cell = ws2.cell(row=1, column=c); cell.fill, cell.font = hdr_fill, hdr_font
for i, row in enumerate(linhas[:40], 1):
    ws2.append([i, row[0], row[1], row[2], row[3], row[4], row[8], row[10][:230]])
for col, w in zip("ABCDEFGH", [4, 6, 10, 24, 36, 11, 16, 78]):
    ws2.column_dimensions[col].width = w
for r in range(2, ws2.max_row + 1):
    for c in range(1, 9):
        ws2.cell(row=r, column=c).alignment = Alignment(vertical="top", wrap_text=True)

cnt = Counter(x["pais"] for x in VAGAS)
hi = Counter(x["pais"] for x in VAGAS if x["nota"] >= 80)
md = Counter(x["pais"] for x in VAGAS if 60 <= x["nota"] < 80)
ws4 = wb.create_sheet("Por País")
ws4.append(["País", "Vagas remotas coletadas", "Alta compat. (≥80)", "Média (60–79)", "Baixa (<60)"])
for c in range(1, 6):
    cell = ws4.cell(row=1, column=c); cell.fill, cell.font = hdr_fill, hdr_font
    cell.alignment = Alignment(wrap_text=True, horizontal="center")
for cc, _ in cnt.most_common():
    nm = NOMES_PAIS[cc]
    ws4.append([nm, cnt[cc], hi[cc], md[cc], cnt[cc] - hi[cc] - md[cc]])
for col, w in zip("ABCDE", [14, 22, 20, 16, 14]):
    ws4.column_dimensions[col].width = w

ws3 = wb.create_sheet("Metodologia")
datas = [x["data"] for x in VAGAS if x["data"]]
n80 = sum(1 for x in VAGAS if x["nota"] >= 80)
txt = [
    f"Fonte: LinkedIn Jobs (API pública guest) com f_WT=2 (filtro REMOTO oficial) + f_TPR=r1296000 (últimos 15 dias). Publicações entre {min(datas)} e {max(datas)}. Coleta em 28/10/2026.",
    f"Escopo: América do Sul — Argentina, Bolívia, Brasil, Chile, Colômbia, Equador, Paraguai, Peru, Uruguai e Venezuela. {len(VAGAS)} vagas remotas únicas após dedupe e pré-filtro de aderência; descrição completa baixada e analisada em 100% delas.",
    f"NOTA DE COMPATIBILIDADE (0–100): score ponderado das keywords da DESCRIÇÃO REAL (PT/EN/ES) contra a sua Versão Mestre (FinOps=10, SAP/BTP=9, Multi-cloud/OCI/RAG/Databricks/ITSM=8, Azure/AWS/GCP/Terraform=7...), + bônus de senioridade (Sr/Especialista/Lead/Head/Director positivo; Analista/Pleno negativo), +12 Brasil (contrato local, idioma/fuso), −5 fora do fuso GMT-3/-4, e PENALIDADE DE GAP quando a JD exige o que o CV não cobre (Kubernetes/CKA, IAM/Entra ID, GitOps/ArgoCD/Helm, Airflow, dbt, Snowflake, Splunk, Prometheus, pentest/threat modeling, .NET/Java). Escala final por percentil: {n80} vagas ficaram ≥80.",
    "COLUNA 'Modo': o filtro Remoto do LinkedIn nem sempre é fiel. Cada descrição foi relida — 'Remoto confirmado' = texto reitera remoto; 'Remoto (filtro LinkedIn)' = não contradiz; 'Híbrido/Presencial (revisar)' = o texto menciona presença, confirmar antes de aplicar.",
    "'Mudanças necessárias no Currículo': receita automática cruzando exigências da JD com lacunas reais da Versão Mestre + Técnica do Espelho (#1 Cloud+FinOps, #2 Gestão/ITSM, #3 IA/Dados, #4 SAP) + lembretes de idioma e modelo de contratação por país.",
    "REALIDADE LATAM: a maioria das vagas remotas sul-americanas vem de empresas globais que exigem INGLÊS fluente; várias (AR/CL/CO/PE/UY/EC/BO/PY) pedem ESPANHOL. Sem versão EN do CV, boa parte dessas vagas fica inacessível — é a ação de maior retorno agora.",
    "Contratação fora do Brasil: normalmente contractor internacional via Deel/Remote.com/EOR, remuneração em US$. Verificar implicação fiscal (CNPJ/carnê-leão) antes de aceitar proposta.",
    f"FONTES NESTE ARQUIVO: {dict(Counter(x['_fonte'] for x in VAGAS))}. O LinkedIn entra pela coleta automática; o Indeed entra por IMPORTAÇÃO do seu arquivo exportado — este ambiente recebe HTTP 403 do Indeed (Cloudflare anti-bot, inclusive nos feeds /rss e /feeds/lcp), então não é possível raspá-lo daqui. Como adicionar as vagas do Indeed: (1) filtre no site (domínio br./ar./cl./co./pe. + q=arquiteto+cloud + 'Desde hace 15 días' + Remote), (2) exporte/cole as linhas num CSV ou XLSX com colunas Empresa | Cargo | Local | Data | Link | Descrição, (3) rode `python importar_indeed.py <arquivo>` (as notas são recalculadas junto com o lote do LinkedIn, sem contar a mesma vaga duas vezes), (4) rode `python gerar_remote.py`.",
    "Atualizar a planilha: cd remote_latam && python3 collect_remote.py && python3 prefilter.py && python3 pontuar_remote.py && python3 reclass.py && python3 gerar_remote.py",
]
ws3.append(["Como esta planilha foi feita"]); ws3.cell(row=1, column=1).font = Font(bold=True, size=12)
for i, t in enumerate(txt, start=2):
    ws3.cell(row=i, column=1, value=t).alignment = Alignment(wrap_text=True, vertical="top")
ws3.column_dimensions["A"].width = 140

wb.save(AP_ARGS.saida_xlsx)
with open(AP_ARGS.saida_csv, "w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f, delimiter=";"); w.writerow(HEADERS)
    for row in linhas:
        w.writerow(row)

print("OK — planilha gerada:", len(linhas), "vagas remotas LATAM")
print("\nTOP 20:")
for row in linhas[:20]:
    print(f'  {row[0]:>2} | {row[3]:<10} | {row[5]:<12} | {row[1][:24]:<24} | {row[2][:46]}')
print("\nAlta (>=80):", sum(1 for x in VAGAS if x["nota"] >= 80),
      "| Media (60-79):", sum(1 for x in VAGAS if 60 <= x["nota"] < 80),
      "| Baixa (<60):", sum(1 for x in VAGAS if x["nota"] < 60))
print("Remoto confirmado:", sum(1 for x in VAGAS if x["modo"] == "Remoto confirmado"))
print("Exigem ingles:", sum(1 for x in VAGAS if x["_lang_en"]),
      "| espanhol:", sum(1 for x in VAGAS if x["_lang_es"]))
print("Por pais:", dict(cnt.most_common()))
