#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
reclass_remote.py — Funções reutilizáveis de pontuação/idioma (importável).

Consolida em funções a lógica que antes vivia solta em pontuar_remote.py /
reclass.py / validar_idioma.py, para que QUALQUER fonte (LinkedIn, Indeed, Gupy,
arquivo externo) passe exatamente pelo mesmo cálculo de nota e pelo mesmo filtro
de idioma. Nada aqui faz rede ou login.
"""
import re
import unicodedata

# ---------------------------------------------------------------- PERFIL (CV)
PERFIL = {
    "azure": 6, "aws": 6, "gcp": 5, "oci": 6, "multicloud": 7, "multi-cloud": 7, "multi cloud": 7,
    "hibrida": 3, "híbrida": 3, "landing zone": 4, "infraestructura como codigo": 4,
    "infraestrutura como código": 4, "terraform": 4, "iac": 3, "ansible": 2, "bicep": 2,
    "arquitetur": 8, "arquitectur": 8, "solucoes": 4, "soluções": 4,
    "integracion": 3, "integração": 3, "api": 3, "sap": 8, "btp": 6, "hana": 4, "cpi": 4,
    "fiori": 3, "s/4hana": 4, "finops": 10, "costo": 4, "custo": 4, "optimiz": 3, "otimiz": 3,
    "gobernan": 5, "governan": 5, "compliance": 3, "seguridad": 4, "segurança": 4,
    "security": 4, "ccsp": 5, "itil": 5, "servicenow": 6, "itsm": 6, "sla": 3, "mttr": 4,
    "observab": 5, "datadog": 5, "zabbix": 4, "dynatrace": 4, "grafana": 3, "sre": 5,
    "site reliability": 5, "kubernetes": 3, "devops": 4, "ci/cd": 4, "pipeline": 3,
    "inteligencia artificial": 7, "inteligência artificial": 7, "machine learning": 6,
    "llm": 5, "rag": 6, "genai": 5, "generativa": 4, "databricks": 7, "pyspark": 5, "spark": 3,
    "data lake": 5, "datalake": 4, "lakehouse": 4, "dataops": 6, "etl": 3, "big data": 4,
    "python": 3, "nps": 3, "presupuesto": 3, "orçament": 3, "p&l": 3, "lideraz": 6, "lideran": 6,
    "lider ": 4, "gest": 5, "gerente": 4, "jefe": 2, "stakeholder": 4, "pmi": 3, "pmp": 5,
    "scrum": 3, "kanban": 2, "migracion": 4, "migra": 4, "moderniz": 4, "disponibilidad": 4,
    "alta disponibilidad": 5, "resili": 3, "microservicios": 3, "microsservi": 3,
    "salesforce": 3, "mulesoft": 5, "digibee": 5, "fortinet": 3, "akamai": 3, "waf": 2,
    "cloud": 5, "certificacion": 3, "certifica": 3, "linux": 1, "vmware": 3, "avs": 3,
    "pre-sales": 4, "preventa": 4, "pré-venda": 4, "cotizaci": 3,
}
SENIOR = {"sr": 8, "senior": 8, "sênior": 8, "especialista": 8, "head": 6, "principal": 6,
          "lead": 6, "iii": 4, "arquiteto": 6, "arquiteta": 6, "arquitecto": 6, "arquitecta": 6,
          "gerente": 5, "coordenador": 2, "analista": -6, "pleno": -8}
BR_PTS = 12
FUSO_OK = ("brazil", "brasil", "argentina", "uruguay", "paraguay", "chile")

GAP_PENALTY = {
    "kubernetes": 7, "cks": 8, "openshift": 5, "helm": 4, "argo": 5, "gitops": 5,
    "airflow": 4, "dbt": 4, "snowflake": 5, "splunk": 4, "prometheus": 3, "grafana": 0,
    "active directory": 5, "entra id": 5, "privileged access": 4, "pentest": 5,
    "penetration test": 5, "threat modeling": 5, "terraform": 2, "java": 3, ".net": 4,
    "power bi": 3, "dynamics": 4, "sap hana migration": 2, "servicenow": 0, "c2pa": 6,
}


def score(texto, pais, local):
    t = texto.lower()
    pts, hits = 0, []
    for kw, w in PERFIL.items():
        n = t.count(kw)
        if n:
            add = w * min(n, 3)
            pts += add
            hits.append((kw, add))
    bonus = 0
    for k, b in SENIOR.items():
        if re.search(r"\b" + re.escape(k), t):
            bonus += b
    if pais == "BR":
        bonus += BR_PTS
    if not any(f in (local or "").lower() for f in FUSO_OK) and pais != "BR":
        bonus -= 5
    hits.sort(key=lambda x: -x[1])
    return pts, bonus, hits[:10]


def gap_penalidade(texto):
    t = texto.lower()
    return min(sum(w for k, w in GAP_PENALTY.items() if k in t), 28)


def repontuar(vagas):
    """Nota 0-100 por percentil do próprio lote (mesma fórmula usada no LinkedIn)."""
    adj = lambda v: v["_pts"] + v["_bonus"] - v["_gap_pen"]
    raws = sorted(adj(v) for v in vagas)
    n = len(raws) or 1

    def percentile(val):
        lo, hi = 0, n - 1
        while lo < hi:
            mid = (lo + hi) // 2
            if raws[mid] < val:
                lo = mid + 1
            else:
                hi = mid
        return lo / max(n - 1, 1)

    for v in vagas:
        v["nota"] = max(25, min(99, round(25 + percentile(adj(v)) * 74)))
    return vagas


def pontuar_lote(vagas):
    """Passo único: calcula _pts/_bonus/_hits/_gap_pen e depois a nota."""
    for v in vagas:
        base = v.get("titulo", "")
        pts, bonus, hits = score(base + " " + v.get("descricao", ""), v.get("pais", ""), v.get("local", ""))
        v["_pts"], v["_bonus"], v["_hits"] = pts, bonus, hits
        v["_gap_pen"] = gap_penalidade(base + " " + v.get("descricao", ""))
    return repontuar(vagas)


# ------------------------------------------------------------- IDIOMA (inglês)
def norm(s):
    s = unicodedata.normalize("NFKD", str(s)).replace("&amp;", " ").replace("&nbsp;", " ")
    return re.sub(r"\s+", " ", s)


EN = r"(?:ingl[eê]s|english)"
ADV_LEVEL = [r"advanced", r"avanzad", r"fluent", r"fluency", r"fluente", r"native",
             r"business[- ]level", r"professional proficiency", r"full professional",
             r"upper[- ]intermediate", r"near[- ]native", r"c1\b", r"\bc2\b", r"b2\+?",
             r"conversacional", r"conversational", r"highly proficient", r"outstanding",
             r"excellent (?:verbal|written|communication|command|skills|knowledge)",
             r"strong (?:spoken|written|verbal|communication|command)",
             r"proficien\w+ in (?:written and spoken|both)",
             r"required to be fluent", r"good communicative level"]
SPOKEN_REQ = [r"spoken english", r"english.{0,25}spoken", r"verbal and written",
              r"written and verbal", r"oral and written", r"both written and (?:spoken|verbal)",
              r"spoken and written", r"ingl[eê]s falad", r"reuni[oõ]es em ingl",
              r"meetings? in english", r"presentations? in english",
              r"discuss\w*.{0,45}in english", r"communicate\w*.{0,35}in english",
              r"stakeholders?.{0,45}in english", r"workshops?.{0,60}in english",
              r"client engagement.{0,40}english", r"essential for effective communication"]
SELECAO_EN = [r"resume[s]?[^\.]{0,60}in english", r"cv[^\.]{0,45}in english",
              r"submitted in english", r"send your[^\.]{0,55}in english",
              r"cover letter[^\.]{0,45}in english", r"curr[íi]culo.{0,35}em ingl",
              r"application instructions[^\.]{0,90}english"]
BAIXO = [r"reading", r"leitura", r"read technical", r"documentation", r"documenta[çc]",
         r"async", r"written only", r"basic", r"b[áa]sico", r"beginner", r"elementary",
         r"\ba1\b", r"\ba2\b", r"intermedi", r"working knowledge", r"working level",
         r"familiarity with english", r"comunica[çc]ão escrita b[áa]sica"]
ATENUA = [r"desejable", r"desej[áa]vel", r"a plus", r"diferencial", r"nice to have",
          r"preferible", r"preferred", r"preferred qualifications", r"optional",
          r"would be", r"bonus", r"se consider", r"is valued", r"not required",
          r"no es requerido", r"n[ãa]o (?:[eé] )?(?:obrigat|requer|exig)", r"training provided"]
BENEFICIO = [r"english classes", r"classes? de ingl", r"open english", r"cui para",
             r"beneficios?[^\n]{0,70}ingl", r"parceria com", r"subsidi(?:ed|y)",
             r"learning development team", r"clube da four", r"wellbeing", r"well-being",
             r"educa[cç][ãa]o e carreira", r"franc[eê]s e portugu", r"conv[eê]nio", r"vantagens"]
ALT_OK = [r"espa[nñ]ol o ingl", r"ingl[eê]s o espa[nñ]ol", r"english or spanish",
          r"spanish or english", r"y/o ingl", r"\bo ingl[eê]s\b",
          r"one of the following languages", r"any of these languages",
          r"english, french, spanish", r"french or spanish", r"spanish,? english or"]

_RX = lambda p: [re.compile(norm(x), re.I) for x in p]
AL_, SP, SEL, BX, AT, BE, ALT = map(_RX, (ADV_LEVEL, SPOKEN_REQ, SELECAO_EN, BAIXO,
                                          ATENUA, BENEFICIO, ALT_OK))
_hit = lambda rxs, s: any(r.search(s) for r in rxs)
FRASE = re.compile(r"[^.;\n|•–—()\[\]]{0,150}\b(?:" + EN + r")\b[^.;\n|•–—()\[\]]{0,120}", re.I)
MAPA = {"REMOVER": ("REMOVER_INGLES_AVANCADO", "Requisito literal de inglês avançado/fluente → “"),
        "DESEJAVEL": ("MANTER_DESEJAVEL", "Atenuado como desejável/diferencial/preferido → “"),
        "SEM_NIVEL": ("MANTER_CITACAO_SOLTA", "Inglês citado sem nível obrigatório → “"),
        "BAIXO_NIVEL": ("MANTER_LEITURA_OU_BAICO", "Só leitura técnica / básico / intermediário → “"),
        "ESPANHOL_BASTA": ("MANTER_ESPANHOL_BASTA", "Idioma alternativo aceito → “"),
        "BENEFICIO": ("MANTER_BENEFICIO", "Curso/convênio de inglês oferecido pela empresa → “")}
PESO = {"REMOVER": 5, "SEM_NIVEL": 2, "ESPANHOL_BASTA": 2, "DESEJAVEL": 1,
        "BAIXO_NIVEL": 1, "BENEFICIO": 0}


def classificar(texto):
    """Retorna (classe, evidencia). Classe REMOVER_* => exige inglês avançado/fluente."""
    t = norm(texto)
    frases = [f.strip() for f in FRASE.findall(t) if len(f.strip()) > 4]
    decisoes = []
    for f in sorted(set(frases), key=len, reverse=True):
        atenua, baix = _hit(AT, f), _hit(BX, f)
        if _hit(BE, f) and not (_hit(SEL, f) or _hit(SP, f)):
            decisoes.append(("BENEFICIO", f))
            continue
        if _hit(SEL, f):
            decisoes.append(("REMOVER", f))
            continue
        alt = _hit(ALT, f)
        adv = (_hit(AL_, f) or _hit(SP, f)) and not baix
        decisoes.append(("DESEJAVEL" if adv and atenua else
                         "ESPANHOL_BASTA" if adv and alt else
                         "REMOVER" if adv else
                         "BAIXO_NIVEL" if baix else
                         "ESPANHOL_BASTA" if alt else "SEM_NIVEL", f))
    if not decisoes:
        return "MANTER_SEM_MENCION", "JD não cita inglês — nenhum filtro aplicado."
    raw, base = max(decisoes, key=lambda d: PESO[d[0]])
    cls, pre = MAPA[raw]
    return cls, (pre + base[:150] + "”")[:240]


def filtrar_idioma(vagas):
    """Aplica classificar() em cada vaga; marca _idioma_remover. Retorna (mantidas, removidas)."""
    mantidas, removidas = [], []
    for v in vagas:
        cls, ev = classificar(v.get("titulo", "") + "\n" + v.get("descricao", ""))
        v["_idioma_classe"], v["_idioma_evidencia"] = cls, ev
        v["_idioma_remover"] = (cls == "REMOVER_INGLES_AVANCADO")
        (removidas if v["_idioma_remover"] else mantidas).append(v)
    return mantidas, removidas
