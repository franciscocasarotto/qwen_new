# -*- coding: utf-8 -*-
"""VALIDACAO DE IDIOMA - remove vagas que exigem ingles AVANCADO/FLUENTE.

Metodo auditavel: extrai a FRASE onde 'ingles/english' aparece (separadores usados pela JD:
pipe |, bullet •, travessao, parenteses, ponto) e le o nivel declarado NA MESMA frase.

REMOVER_INGLES_AVANCADO : avancado/fluido/nativo/C1/C2/B2+/upper-intermediate/business-level/
                          outstand/conversacional, fluencia falada exigida, "required to be
                          fluent", ou selecao em ingles ("resume in English") = barreira real
MANTER_SEM_MENCION      : JD nao cita ingles
MANTER_LEITURA_OU_BAICO : so leitura tecnica / basico / intermediario / working knowledge
MANTER_DESEJAVEL        : desejable / diferencial / a plus / nice to have / preferred
MANTER_BENEFICIO        : curso ou convenio de ingles oferecido pela empresa
MANTER_ESPANHOL_BASTA   : ingles citado apenas como alternativa ao espanhol
MANTER_CITACAO_SOLTA    : menciona ingles sem declarar nivel obrigatorio
"""
import json, re, unicodedata
from collections import Counter

VAGAS = json.load(open("/workspace/remote_latam/vagas_remote_final.json"))

def norm(s):
    s = unicodedata.normalize("NFKD", s).replace("&amp;", " ").replace("&nbsp;", " ")
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

RX = lambda p: [re.compile(norm(x), re.I) for x in p]
AL_, SP, SEL, BX, AT, BE, ALT = map(RX, (ADV_LEVEL, SPOKEN_REQ, SELECAO_EN, BAIXO, ATENUA, BENEFICIO, ALT_OK))
hit = lambda rxs, s: any(r.search(s) for r in rxs)

FRASE = re.compile(r"[^.;\n|•–—()\[\]]{0,150}\b(?:" + EN + r")\b[^.;\n|•–—()\[\]]{0,120}", re.I)

MAPA = {"REMOVER": ("REMOVER_INGLES_AVANCADO", "Requisito literal de inglês avançado/fluente → “"),
        "DESEJAVEL": ("MANTER_DESEJAVEL", "Atenuado como desejável/diferencial/preferido → “"),
        "SEM_NIVEL": ("MANTER_CITACAO_SOLTA", "Inglês citado sem nível obrigatório → “"),
        "BAIXO_NIVEL": ("MANTER_LEITURA_OU_BAICO", "Só leitura técnica / básico / intermediário → “"),
        "ESPANHOL_BASTA": ("MANTER_ESPANHOL_BASTA", "Idioma alternativo aceito → “"),
        "BENEFICIO": ("MANTER_BENEFICIO", "Curso/convênio de inglês oferecido pela empresa → “")}
PESO = {"REMOVER": 5, "SEM_NIVEL": 2, "ESPANHOL_BASTA": 2, "DESEJAVEL": 1, "BAIXO_NIVEL": 1, "BENEFICIO": 0}

for x in VAGAS:
    t = norm(x["titulo"] + "\n" + x["descricao"])
    frases = [f.strip() for f in FRASE.findall(t) if len(f.strip()) > 4]
    decisoes = []
    for f in sorted(set(frases), key=len, reverse=True):
        atenua, baix = hit(AT, f), hit(BX, f)
        if hit(BE, f) and not (hit(SEL, f) or hit(SP, f)):   decisoes.append(("BENEFICIO", f)); continue
        if hit(SEL, f):                                      decisoes.append(("REMOVER", f)); continue
        alt = hit(ALT, f)
        adv = (hit(AL_, f) or hit(SP, f)) and not baix
        decisoes.append(("DESEJAVEL" if adv and atenua else
                         "ESPANHOL_BASTA" if adv and alt else
                         "REMOVER" if adv else
                         "BAIXO_NIVEL" if baix else
                         "ESPANHOL_BASTA" if alt else "SEM_NIVEL", f))
    if not decisoes:
        cls, ev = "MANTER_SEM_MENCION", "JD não cita inglês — nenhum filtro aplicado."
    else:
        raw, base = max(decisoes, key=lambda d: PESO[d[0]])
        cls, pre = MAPA[raw]
        ev = pre + base[:150] + "”"
    x["_idioma_classe"] = cls
    x["_idioma_evidencia"] = ev[:240]
    x["_idioma_remover"] = (cls == "REMOVER_INGLES_AVANCADO")


if __name__ == "__main__":
    mantenidas = [x for x in VAGAS if not x["_idioma_remover"]]
    json.dump(mantenidas, open("/workspace/remote_latam/vagas_remote_final_sem_ingles_avancado.json", "w"), ensure_ascii=False, indent=1)
    json.dump(VAGAS, open("/workspace/remote_latam/vagas_remote_idiomas.json", "w"), ensure_ascii=False, indent=1)

    print("TOTAL analisadas :", len(VAGAS))
    for k, n in Counter(x["_idioma_classe"] for x in VAGAS).most_common(): print(f"   {k:<30} {n:>4}")
    print("REMOVIDAS        :", sum(x['_idioma_remover'] for x in VAGAS))
    print("LISTA FINAL      :", len(mantenidas))
