# -*- coding: utf-8 -*-
"""
Etapa 3 — planilha final (XLSX + CSV) com vagas REAIS do LinkedIn (últimos 15 dias),
ordenadas da MAIS compatível para a MENOS compatível.

As "Mudanças necessárias no Currículo" são geradas cruzando a descrição REAL de cada
vaga com as lacunas conhecidas da Versão Mestre, e a Estratégia de Espelho (#1..#4)
é escolhida pelo eixo dominante da vaga.
"""
import csv, json, re
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

VAGAS = json.load(open("/workspace/vagas_enriquecidas.json"))

# ---------------------------------------------------------------------------
# Receitas de adaptação do CV, disparadas por keyword encontrada na JD
# ---------------------------------------------------------------------------
GAPS = {
    # --- FinOps / custo / financeiro
    "finops": "FinOps é seu ouro (FOCP): trazer FOCP para a 1ª linha de certificações e nomear ferramentas (Azure Cost Management, AWS Cost Explorer).",
    "custo": "Trocar placeholders [R$ X]/[X]% por números reais de economia — essa JD cobra métricas de custo.",
    "orçament": "Declarar orçamento gerenciado (R$ M); o CV atual não dimensiona budget.",
    "p&l": "Dimensionar o book de P&L da Nextios (nº de contas cloud/mês).",
    "cost center": "Citar estrutura de tagging/cost centers implementada (FinOps prático).",
    # --- Cloud / arquitetura
    "multicloud": "Manter 'Multi-Cloud (Azure/AWS/GCP/OCI)' como 1ª linha das Core Competencies — match direto.",
    "azure": "Abrir o resumo com AZ-305 / Azure Solutions Architect Expert (Azure-first).",
    "aws": "Reordenar stack com AWS SAAC02 na frente e traduzir termos Azure→AWS equivalentes.",
    "gcp": "Puxar GCP/BigQuery da Semad e CIMED para os dois primeiros bullets.",
    "oci": "Nomear serviços OCI usados (VCN, OKE, Autonomous) — diferencial raro no mercado BR.",
    "landing zone": "Citar landing zones desenhadas na Nexa/CIMED com nº de assinaturas/contas.",
    "vmware": "Manter VMware/Azure Stack HCI/AVS visível — é seu diferencial em ambientes híbridos.",
    "infraestrutura como código": "Especificar a ferramenta de IaC (Terraform/Bicep/ARM): o CV diz só 'IaC'.",
    "terraform": "Adicionar Terraform nominalmente ao bloco IaC + citar módulo/landing zone desenhado.",
    "bicep": "Citar Bicep/ARM templates como stack de IaC em Azure.",
    "ansible": "Nomear Ansible nas automações da CIMED.",
    "migra": "Quantificar migrações: nº de workloads, TB migrados, janelas de corte.",
    "moderniza": "Citar padrão de modernização aplicado (6Rs, lift-and-shift → refatoração).",
    "disponibilidad": "Substituir [X]% por SLA real (99,9%/99,99%) de alta disponibilidade.",
    "resili": "Detalhar DR/failover conduzido (active-passive, RTO/RPO) — hoje implícito.",
    "backup": "LACUNA REAL: políticas de backup/DR não documentadas no CV.",
    "network": "Aprofundar rede cloud: VNet/VCN/VPC, ExpressConnect/FastConnect.",
    "vpn": "Tornar explícita a conectividade híbrida/VPN (evidência existe na CIMED).",
    "microsservi": "Ligar microsserviços a DDD/C4 (você tem) + nº de serviços em produção.",
    "ddd": "DDD já no CV: manter no topo das competências — match direto com essa JD.",
    "c4": "Usar C4 Model como diferencial de documentação de arquitetura.",
    "api": "Citar governança de APIs (MuleSoft/Digibee da CIMED) com nº de APIs integradas.",
    # --- DevSecOps / SRE / observabilidade
    "devsecops": "Unir 'Security by Design' + CI/CD sob o termo DevSecOps (keyword ATS).",
    "ci/cd": "Dar alcance ao CI/CD: nº de pipelines e frequência de deploy.",
    "jenkins": "Manter Jenkins associado a métricas de automação (Semad).",
    "kubernetes": "LACUNA REAL: Kubernetes/CKA não aparecem na Versão Mestre — cite exposição real ou crie ponte antes de aplicar.",
    "openshift": "LACUNA REAL: OpenShift ausente do CV.",
    "docker": "Incluir Docker/containers no bloco DevOps.",
    "gitops": "LACUNA REAL: GitOps (ArgoCD/Flux) não documentado.",
    "sre": "Converter war-rooms/SRE em bullet com MTTR e volume de incidentes P1.",
    "observab": "Bloco 'Observabilidade' unificado (Datadog, Dynatrace, Zabbix, Grafana) com escopo 24x7.",
    "datadog": "Quantificar % de MTTR reduzido com Datadog (placeholder a preencher).",
    "dynatrace": "Nomear escopo do Dynatrace APM (nº de aplicações monitoradas).",
    "zabbix": "Transformar Zabbix/Grafana/SNMP (Union It) em bullet de resultado com SLA 24x7.",
    "grafana": "Manter Grafana junto de observabilidade ponta a ponta (Union It).",
    "prometheus": "LACUNA REAL: Prometheus não citado no CV.",
    "splunk": "LACUNA REAL: Splunk ausente (você tem Datadog/Zabbix/Dynatrace).",
    "mttr": "Preencher % real de redução de MTTR (Union It/CIMED).",
    "sla": "Substituir placeholders de SLA/OLA por percentuais reais de atingimento.",
    "war room": "Dar volume às war-rooms: nº de incidentes P1/mês conduzidos.",
    "monitoramento": "Agrupar stacks de monitoramento num bloco único com escopo 24x7.",
    # --- Segurança
    "segurança": "Criar bloco 'Security by Design' com CCSP/CCSK + caso concreto de remediação.",
    "security": "Vagas de security: elevar Fortinet/WAF/Akamai (Nextios) para evidência de AppSec.",
    "fortinet": "Transformar Fortinet/WAF/Akamai (Nextios) em bloco 'Network Security'.",
    "firewall": "Criar bloco 'Network Security' (Fortinet/WAF/Akamai/VPN) com caso e métrica.",
    "siem": "Converter a cert Datadog SRE/SIEM em bullet de conquista mensurável.",
    "pentest": "LACUNA REAL: pentest/resposta a incidentes de segurança não documentados.",
    "iam": "LACUNA REAL: IAM/Privileged Access não documentado no CV.",
    "active directory": "LACUNA REAL: AD/Entra ID não nomeados — crítico em vagas de infra.",
    "compliance": "Ligar compliance/auditoria a LGPD + CCSP (você cita auditoria sem nomear a lei).",
    "lgpd": "Nomear LGPD explicitamente em Governança/Compliance (combina com CCSP).",
    "governan": "Governança é forte no CV: abrir com FOCP+CCSP+PMP como tripé de governança.",
    # --- Dados / IA
    "inteligência artificial": "Aplicar Espelho #3: IA/Dados no topo do resumo.",
    "llm": "LLM/RAG (Semad) deve ir ao topo do resumo para essa JD.",
    "rag": "Descrever 1 caso RAG com base documental e ganho medido — sua história mais quente.",
    "genai": "Reforçar LangChain/Anthropic + projeto demonstrável (GitHub) para GenAI.",
    "machine learning": "Amarrar ML à acurácia [+X]% da Semad (preencher placeholder).",
    "databricks": "Databricks aparece em 3 empresas: consolidar num bloco 'Data & Analytics'.",
    "pyspark": "Citar volume processado em PySpark (TB/job diário).",
    "data lake": "Nomear camadas/capacidade do Data Lake e quem consome (BI/ML).",
    "dataops": "Formalizar o termo 'DataOps' no CV — você descreve a prática sem nomeá-la.",
    "etl": "Nomear a ferramenta de ETL/ELT (ADF, Databricks Workflows).",
    "airflow": "LACUNA REAL: Airflow fora do CV; cite equivalentes (ADF/Databricks Workflows).",
    "dbt": "LACUNA REAL: dbt ausente do stack de dados.",
    "snowflake": "LACUNA REAL: Snowflake ausente — priorize JDs com Databricks.",
    "big data": "Ligar Big Data à cert IBM + casos concretos da Indra.",
    "python": "Especificar libs Python usadas (pandas/pyspark) em vez de só 'Python'.",
    "power bi": "Power BI não consta do CV: citar dashboards sobre Databricks/ADF se houver.",
    # --- SAP / integração / ERP
    "sap": "SAP BTP/CPI/HANA/Fiori já forte: subir para a 1ª linha das competências.",
    "s/4hana": "Nomear migrações S/4HANA explicitamente (CV fala 'modernização SAP').",
    "btp": "Detalhar projetos SAP BTP (nº de integrações CPI, Fiori apps entregues).",
    "hana": "Detalhar HANA (on-prem/cloud) e dimensionamento conduzido na Nexa/Indra.",
    "mulesoft": "Expandir MuleSoft/Digibee (CIMED) com nº de APIs e sistemas legados.",
    "digibee": "Citar Digibee com volume de integrações/mês (CIMED).",
    "salesforce": "Expandir o bullet de Salesforce (Nexa) com volume/nº de integrações.",
    "dynamics": "Dynamics 365 não consta; use SAP/Salesforce como ponte de ERP/CRM.",
    "java": "Java não é destaque no CV — cuidado em arquitetura de aplicação Java.",
    ".net": "LACUNA REAL: .NET ausente do CV.",
    # --- ITSM / gestão
    "servicenow": "Subir ServiceNow/TopDesk (Nextios) para Core Competencies; hoje está diluído.",
    "itil": "Declarar versão/certificação ITIL (Foundation/Intermediate) — CV só cita ITIL como keyword.",
    "itsm": "Criar seção dedicada 'IT Service Management' agregando ITIL/ServiceNow/SLA/OLA/KPI.",
    "service desk": "Se for service desk: reduzir arquitetura técnica e ampliar volumes (chamados/mês, FCR).",
    "pmp": "PMP já no CV: garantir que apareça na 1ª linha de certs para vagas de gestão.",
    "pmbok": "Citar PMBOK + porte dos projetos (escopo/prazo/orçamento) na Indra.",
    "gest": "Colocar comitês executivos mensais (Indra) como primeiro bullet de gestão.",
    "lider": "Informar nº de pessoas lideradas (diretas/indiretas) — ausência notada nesse tipo de JD.",
    "stakeholder": "Especificar nível dos stakeholders (C-level, nº de áreas) — CV atual é genérico.",
    "nps": "Preencher o [X] pontos de NPS da Indra com número real — essa JD vai cobrar.",
    "scrum": "Declarar certificação/horas ágeis se possuir (PMI-ACP, CSM).",
    "agile": "Scrum/Kanban já listados; adicionar escala (SAFe) se houver experiência.",
    "pré vendas": "Pré-vendas: destacar propostas técnicas (Nextios) + comitês executivos (Indra).",
    "certifica": "Listar as certs exigidas pela JD logo abaixo do resumo, não no fim do CV.",
    "gradua": "Suas pós (UNIP/SENAC) cobrem o requisito — manter Education enxuta.",
    "inglês": "Preparar versão EN da Versão Mestre (sem placeholders) — a JD exige inglês.",
    "english": "Preparar versão EN da Versão Mestre — a JD exige inglês.",
    "latam": "Destacar atuação LATAM (Indra/clientes multinacionais) como prova de escopo regional.",
    "presencial": "Vaga presencial: confirmar deslocamento Bragança Paulista→SP/Campinas.",
}

PESO = {"finops": 10, "sap": 9, "s/4hana": 9, "btp": 9, "multicloud": 8, "oci": 8, "rag": 8,
        "inteligência artificial": 8, "databricks": 8, "servicenow": 8, "itsm": 8, "itil": 7,
        "azure": 7, "aws": 7, "gcp": 7, "kubernetes": 7, "terraform": 7, "custo": 7, "nps": 7,
        "mttr": 7, "sla": 7, "orçament": 6, "lider": 6, "pmp": 6, "pré vendas": 6, "lgpd": 6,
        "iam": 6, "active directory": 6, "gitops": 6, "snowflake": 6, "airflow": 6, "dbt": 6,
        "splunk": 6, "prometheus": 6, "pentest": 6, "backup": 5, "inglês": 5, "english": 5,
        "power bi": 5, "dynamics": 5, ".net": 5, "java": 4, "openshift": 5, "docker": 4}
for k in GAPS:
    PESO.setdefault(k, 3)

def mudancas(v):
    t = (v["titulo"] + " " + v["descricao"]).lower()
    achadas = sorted([k for k in GAPS if k in t], key=lambda k: -PESO[k])
    receitas, vistos_txt = [], set()
    for k in achadas:
        txt = GAPS[k]
        if txt in vistos_txt:
            continue
        vistos_txt.add(txt); receitas.append(txt)
        if len(receitas) >= 5:
            break
    # Espelho dominante
    def pontu(*keys):
        return sum(t.count(k) for k in keys)
    scores = {
        "#1 Cloud+FinOps": pontu("finops", "custo", "cloud", "migra", "disponibilidad"),
        "#2 Gestão/ITSM": pontu("gest", "itsm", "servicenow", "itil", "nps", "stakeholder", "pmp", "coordena"),
        "#3 IA/Dados": pontu("inteligência artificial", "llm", "rag", "genai", "machine learning", "databricks", "data lake", "etl"),
        "#4 SAP/Integração": pontu("sap", "btp", "hana", "mulesoft", "digibee", "s/4hana"),
    }
    esp = max(scores, key=scores.get)
    titulos = {
        "#1 Cloud+FinOps": "ESPELHO #1 (Cloud+FinOps) → título do CV: 'Arquiteto de Soluções Cloud & FinOps (FOCP, AZ-305, AWS SA)'; Nexa/CIMED como evidência principal.",
        "#2 Gestão/ITSM": "ESPELHO #2 (Gestão/ITSM) → título: 'Líder de TI & Gestão de Serviços (PMP, ITIL, FinOps)'; subir Indra/Nextios e reduzir jargão de arquitetura.",
        "#3 IA/Dados": "ESPELHO #3 (IA/Dados) → título: 'Arquiteto de IA & Dados (RAG, LLM, Databricks)'; Semad como 1ª experiência.",
        "#4 SAP/Integração": "ESPELHO SAP → título: 'Arquiteto de Soluções SAP BTP & Integração Híbrida'; Indra/Nexa como evidência principal.",
    }
    out = [titulos[esp]] + receitas
    if v["nota"] < 60:
        out.append("PRIORIDADE BAIXA: não adapte seu CV-mestre para esta vaga agora — dilui a narrativa sênior.")
    return " • ".join(out)

def justificativa(v):
    fortes = ", ".join(h[0] for h in v["hits"][:6]) or "-"
    t = (v["titulo"] + " " + v["descricao"]).lower()
    gaps_txt = []
    for kw, rot in [("kubernetes", "Kubernetes"), ("airflow", "Airflow"), ("snowflake", "Snowflake"),
                    ("active directory", "IAM/AD"), ("iam", "IAM"), ("splunk", "Splunk"),
                    ("gitops", "GitOps"), ("prometheus", "Prometheus")]:
        if kw in t and not any(h[0] == kw for h in v["hits"]):
            gaps_txt.append(rot)
    if ("inglês" in t or "english" in t):
        gaps_txt.append("inglês (versão EN)")
    base = f"Sobreposição forte com a Versão Mestre: {fortes}."
    if gaps_txt:
        base += " Gap a neutralizar: " + ", ".join(dict.fromkeys(gaps_txt)) + "."
    if v["bonus_cliente"]:
        base += " BÔNUS: empresa é ex-cliente/ex-casa do seu histórico."
    if v["pts"] < 90:
        base += " Score de keywords baixo: a JD fala pouco a língua do seu perfil."
    return base

HEADERS = ["Nota", "Empresa", "Cargo", "Publicada em", "Local", "Link da vaga",
           "Justificativa da Compatibilidade", "Mudanças necessárias no Currículo"]

wb = Workbook(); ws = wb.active; ws.title = "Vagas (ordenadas)"
hdr_fill = PatternFill("solid", fgColor="1F3864"); hdr_font = Font(color="FFFFFF", bold=True)
thin = Side(style="thin", color="BFBFBF"); border = Border(thin, thin, thin, thin)

for c, h in enumerate(HEADERS, 1):
    cell = ws.cell(row=1, column=c, value=h)
    cell.fill, cell.font, cell.border = hdr_fill, hdr_font, border
    cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)

def cor(n):
    if n >= 85: return PatternFill("solid", fgColor="C6EFCE")
    if n >= 70: return PatternFill("solid", fgColor="FFEB9C")
    return PatternFill("solid", fgColor="FFC7CE")

linhas = []
for v in VAGAS:
    row = [v["nota"], v["empresa"], v["titulo"], v["data"], v["local"], v["link"],
           justificativa(v), mudancas(v)]
    linhas.append(row)
    r = ws.max_row + 1
    for c, val in enumerate(row, 1):
        cell = ws.cell(row=r, column=c, value=val)
        cell.border = border
        cell.alignment = Alignment(vertical="top", wrap_text=(c != 1))
        if c == 1:
            cell.fill, cell.font = cor(val), Font(bold=True)
            cell.alignment = Alignment(horizontal="center", vertical="center")
        if c == 6:
            cell.hyperlink = val; cell.font = Font(color="0563C1", underline="single")

for i, w in enumerate([6, 26, 34, 12, 22, 40, 46, 86], 1):
    ws.column_dimensions[get_column_letter(i)].width = w
ws.freeze_panes = "A2"; ws.auto_filter.ref = f"A1:H{ws.max_row}"

# ---- Aba TOP 20 -------------------------------------------------------------
ws2 = wb.create_sheet("TOP 20 — Priorizar")
ws2.append(["#", "Nota", "Empresa", "Cargo", "Por que priorizar"])
for c in range(1, 6):
    cell = ws2.cell(row=1, column=c); cell.fill, cell.font = hdr_fill, hdr_font
motivos = {
    "Grupo Think": "JD praticamente escrita para o seu CV: Azure+OCI+GCP, FinOps, landing zones, alta disponibilidade.",
    "Stefanini Brasil": "Pré-vendas: une seu lado cliente-facing (Indra/Nextios) a FinOps e multi-cloud.",
    "Embraer": "Grande corporação industrial (paralelo Nexa/Votorantim), IaC, governança e custo-benefício de nuvem.",
    "AGGRANDIZE": "Azure + microsserviços + segurança: AZ-305/DDD/C4 fecham o core; presencial em Campinas.",
    "XP Inc.": "Especialista com governança/observabilidade em instituição financeira — combo CCSP + Porto Seguro.",
    "Extreme Digital Solutions - EDS": "OCI + alta disponibilidade + observabilidade: sua passagem pela CIMED repetida.",
    "AllEasy": "Infraestrutura & Cloud com FinOps explícito e ambiente multinacional complexo.",
    "Extractta": "Azure + Databricks com peso alto; papel mais operacional — usar como fallback.",
    "INDT Innovation": "Cloud + Dados + IA na mesma vaga: cobre seus três eixos simultaneamente.",
    "EY": "Cloud Manager/Azure em big4, forte em dados; exige formalização de certificações.",
    "Itaú Unibanco": "Distinguished Engineer Cyber Security: teto técnico sênior; gap = threat modeling profundo.",
    "Banco Bradesco": "Arquiteto de Soluções SR: banco grande + sua experiência com Digio ajuda na narrativa.",
    "Oracle": "Arquiteto de Soluções Cloud: OCI é diferencial raro no mercado BR.",
    "Amazon Web Services (AWS)": "Hyperscaler: AWS SA + cenário enterprise; exige versão EN do CV.",
    "Microsoft": "Solution Engineer Apps & AI: AZ-305 + GenAI alinham perfeitamente.",
    "Deloitte": "Consultoria sênior de Arquitetura e IA de Negócios: casa com seu posicionamento estratégico.",
    "Kyndryl": "SRE + AI Platform: junção de observabilidade e IA, ambas presentes no CV.",
    "LKM Tecnologia": "Gerente de Projetos SAP: PMP + BTP/CPI/HANA é match direto.",
    "Digio": "Coordenação de Governança de TI: você atendeu o Digio na Nextios + FinOps/governança.",
    "Accenture Brasil": "Cloud Governance Specialist: governança multi-cloud + compliance (CCSP).",
}
for i, row in enumerate(linhas[:20], 1):
    ws2.append([i, row[0], row[1], row[2], motivos.get(row[1], row[6][:190])])
for col, w in zip("ABCDE", [5, 7, 26, 40, 74]):
    ws2.column_dimensions[col].width = w
for r in range(2, ws2.max_row + 1):
    for c in range(1, 6):
        ws2.cell(row=r, column=c).alignment = Alignment(vertical="top", wrap_text=True)

# ---- Aba Metodologia -------------------------------------------------------
ws3 = wb.create_sheet("Metodologia")
datas = [v["data"] for v in VAGAS if v["data"]]
txt = [
    f"Fonte: LinkedIn Jobs (API pública guest). Janela: últimos 15 dias (f_TPR=r1296000), publicadas entre {min(datas)} e {max(datas)}. Coleta em 28/10/2026.",
    f"Escopo geográfico: região de Bragança Paulista + São Paulo e cidades próximas (Campinas, Osasco, Barueri, SJC) + Brasil. {len(VAGAS)} vagas únicas após dedupe e filtro anti-EUA.",
    "NOTA DE COMPATIBILIDADE: score ponderado das keywords da DESCRIÇÃO REAL de cada vaga contra a sua Versão Mestre (FinOps=10, SAP/BTP=9, Multi-cloud/OCI/RAG/Databricks/ITSM=8, Azure/AWS/GCP/Terraform/Kubernetes=7 etc.), + bônus de senioridade (Sr/Especialista/Lead/Head positivo; Analista/Assistente/Pleno/Júnior negativo) + bônus de ex-cliente (+6: Locaweb, Vivo, Heineken, Bauducco, Porto Seguro, Digio). Normalizado em 40–100.",
    "'Mudanças necessárias no Currículo': receita automática que cruza as exigências da JD com lacunas reais da Versão Mestre (Kubernetes, IAM/AD, Airflow, dbt, Snowflake, GitOps, Splunk, Prometheus, backup/DR, inglês) e aplica a Técnica do Espelho (#1 Cloud+FinOps, #2 Gestão/ITSM, #3 IA/Dados, #4 SAP).",
    "Indeed NÃO pôde ser raspado (HTTP 403 anti-bot). Para completar com vagas Indeed dos últimos 15 dias, abra manualmente: https://br.indeed.com/jobs?q=arquiteto+de+solucoes+cloud&fromage=15&sort=date",
    "Antes de enviar qualquer CV: preencha todos os [X]% e [R$ Y]. As JDs do TOP 10 pedem explicitamente métricas de custo, SLA, NPS e MTTR.",
    "Atualizar a planilha: python3 coletar_vagas_linkedin.py && python3 pontuar_vagas.py && python3 gerar_planilha_vagas.py",
]
ws3.append(["Como esta planilha foi feita"]); ws3.cell(row=1, column=1).font = Font(bold=True, size=12)
for i, t in enumerate(txt, start=2):
    ws3.cell(row=i, column=1, value=t).alignment = Alignment(wrap_text=True, vertical="top")
ws3.column_dimensions["A"].width = 135

wb.save("/workspace/vagas_compativeis.xlsx")

with open("/workspace/vagas_compativeis.csv", "w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f, delimiter=";")
    w.writerow(HEADERS)
    for row in linhas:
        w.writerow(row)

print("Planilha gerada:", len(linhas), "vagas reais, ordenadas da mais compatível para a menos.")
for row in linhas[:12]:
    print(f"  {row[0]:>3} | {row[1][:26]:26} | {row[2][:46]}")
