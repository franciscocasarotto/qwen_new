# -*- coding: utf-8 -*-
"""Gera HTML + CSV apenas com as vagas que NAO exigem ingles avancado/fluente."""
import json, csv, html, re, unicodedata

SRC = "/workspace/remote_latam/vagas_remote_idiomas.json"
V   = json.load(open(SRC))
OK  = [x for x in V if not x["_idioma_remover"]]
REM = [x for x in V if x["_idioma_remover"]]
OK.sort(key=lambda x: -x["nota"]); REM.sort(key=lambda x: -x["nota"])

def norm(s): return re.sub(r"\s+"," ",unicodedata.normalize("NFKD",s)).strip()
FAIXA = lambda n: "90+" if n>=90 else "80-89" if n>=80 else "70-79" if n>=70 else "60-69" if n>=60 else "50-59" if n>=50 else "<50"
PCT = lambda a,b: f"{100*a/b:.1f}%"

with open("/workspace/remote_latam/vagas_sem_ingles_avancado.csv","w",newline="",encoding="utf-8-sig") as f:
    w=csv.writer(f); w.writerow(["Nota","Faixa","Escala","Sugestao","Pais","Empresa","Titulo","Link","Origem","Status_idioma","Evidencia_idioma"])
    for x in OK:
        w.writerow([x["nota"],FAIXA(x["nota"]),x.get("escala",""),x.get("sugestao",""),x["pais"],x["empresa"],x["titulo"],x["link"],x.get("fonte",""),"MANTER",x["_idioma_classe"]])
    w.writerow([]); w.writerow(["--- REMOVIDAS: EXIGIAM INGLS AVANADO/FLUENTE ---"])
    for x in REM:
        w.writerow([x["nota"],FAIXA(x["nota"]),x.get("escala",""),x.get("sugestao",""),x["pais"],x["empresa"],x["titulo"],x["link"],x.get("fonte",""),"REMOVIDA",x["_idioma_evidencia"]])

CARDS = """<a class="card" href="{link}" target="_blank"><div class="top"><span class="nota">{nota}</span><span class="fx {fxc}">{faixa}</span></div>
<div class="emp">{empresa}</div><div class="tit">{titulo}</div>
<div class="row"><span class="pais">{pais}</span>{badge}<span class="ver">Ver vaga →</span></div></a>"""

def cards(lst):
    out=[]
    for x in lst:
        n=x["nota"]; fxc="fx1" if n>=90 else "fx2" if n>=80 else "fx3"
        badge=f'<span class="tag">{html.escape(x.get("escala",""))}</span>' if x.get("escala") else ""
        out.append(CARDS.format(link=html.escape(x["link"]),nota=n,fxc=fxc,faixa=FAIXA(n),
                    empresa=html.escape(x["empresa"]),titulo=html.escape(x["titulo"]),pais=x["pais"],badge=badge))
    return "\n".join(out)

def filtros(prefixo,lst):
    paises=sorted({x["pais"] for x in lst}); faixas=["90+","80-89","70-79","60-69","50-59","<50"]
    esc=sorted({x["escala"] for x in lst if x.get("escala")})
    h=f'<select id="{prefixo}-p" onchange="fil(\'{prefixo}\')"><option value="">Todos os países</option>'
    h+="".join(f'<option value="{p}">{p}</option>' for p in paises)+'</select>'
    h+=f'<select id="{prefixo}-f" onchange="fil(\'{prefixo}\')"><option value="">Todas as notas</option>'
    h+="".join(f'<option value="{x}">{x}</option>' for x in faixas)+'</select>'
    h+=f'<select id="{prefixo}-e" onchange="fil(\'{prefixo}\')"><option value="">Todas as escalas</option>'
    h+="".join(f'<option value="{html.escape(s)}">{html.escape(s)}</option>' for s in esc)+'</select>'
    h+=f'<input id="{prefixo}-q" type="search" placeholder="buscar cargo ou empresa…" oninput="fil(\'{prefixo}\')">'
    return h

HTML=f"""<!doctype html><html lang="pt-br"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Vagas remotas LATAM · sem inglês avançado</title>
<style>
*{{box-sizing:border-box}}body{{margin:0;font-family:-apple-system,'Segoe UI',Roboto,sans-serif;background:#eef1f5;color:#141b2d}}
header{{background:linear-gradient(135deg,#0b3b5c,#0e7c6b);color:#fff;padding:30px 22px}}
h1{{margin:0 0 6px;font-size:25px}}.sub{{opacity:.85;font-size:13px;line-height:1.55;max-width:1000px}}
.strip{{display:flex;flex-wrap:wrap;gap:10px;margin-top:16px}}
.pill{{background:rgba(255,255,255,.14);border-radius:999px;padding:7px 13px;font-size:12.5px}}.pill b{{font-size:15px}}
main{{padding:22px;max-width:1400px;margin:auto}}
.filters{{display:flex;flex-wrap:wrap;gap:10px;background:#fff;border-radius:12px;padding:14px;margin-bottom:18px;box-shadow:0 1px 4px rgba(0,0,0,.07);position:sticky;top:0;z-index:5}}
select,input[type=search]{{padding:9px 11px;border:1px solid #ccd5e0;border-radius:8px;font-size:14px;background:#fff}}
input[type=search]{{flex:1;min-width:210px}}
.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(310px,1fr));gap:14px}}
.card{{background:#fff;border-radius:12px;padding:16px;text-decoration:none;color:inherit;box-shadow:0 1px 4px rgba(0,0,0,.07);border-left:4px solid #0e7c6b;transition:.15s;display:block}}
.card:hover{{transform:translateY(-2px);box-shadow:0 6px 18px rgba(0,0,0,.12)}}
.top{{display:flex;align-items:center;gap:8px;margin-bottom:8px}}
.nota{{background:#0b3b5c;color:#fff;font-weight:700;border-radius:8px;padding:3px 10px;font-size:14px}}
.fx{{font-size:11px;font-weight:700;border-radius:6px;padding:3px 8px}}.fx1{{background:#d9f2e6;color:#0b6b3a}}.fx2{{background:#fff2cc;color:#8a6100}}.fx3{{background:#fde2e1;color:#9c2b25}}
.emp{{font-size:12px;color:#5a6b85;font-weight:600;text-transform:uppercase;letter-spacing:.03em}}
.tit{{font-size:16px;font-weight:600;margin:4px 0 12px;line-height:1.3}}
.row{{display:flex;align-items:center;gap:8px}}.pais{{font-size:11.5px;color:#7b8aa5;font-weight:600}}
.tag{{font-size:11px;background:#eef4ff;color:#2a5fbf;border-radius:6px;padding:2px 7px}}
.ver{{margin-left:auto;color:#0e7c6b;font-size:13px;font-weight:600}}
.secao{{margin:34px 0 14px;font-size:19px}}.aviso{{font-size:13px;color:#6b7a94;margin:-6px 0 16px;line-height:1.6}}
details summary{{cursor:pointer;font-weight:600;color:#8a2b25;margin-bottom:10px}}
.rem .card{{border-left-color:#c94b45;opacity:.85}}
footer{{text-align:center;color:#7b8aa5;font-size:12px;padding:26px}}
.cnt{{font-size:13px;color:#5a6b85;margin-bottom:10px}}
</style></head><body>
<header><h1>☁️ Vagas remotas em Cloud &amp; Dados na América Latina — <u>sem exigir inglês avançado</u></h1>
<div class="sub">Validação frase a frase de todas as {len(V)} descrições: cada menção a “inglês/english” foi lida no contexto do próprio requisito.
Exigências de nível avançado/fluente/C1/C2/B2+/conversacional foram <b>removidas</b>. Também não são barreira: leitura técnica,
nível básico/intermediário, “desejável/diferencial”, curso de inglês oferecido pela empresa e casos em que o espanhol basta.</div>
<div class="strip">
<span class="pill"><b>{len(OK)}</b> vagas mantidas ({PCT(len(OK),len(V))})</span>
<span class="pill"><b>{len(REM)}</b> removidas por inglês avançado ({PCT(len(REM),len(V))})</span>
<span class="pill"><b>{sum(1 for x in OK if x['nota']>=90)}</b> nota 90+</span>
<span class="pill"><b>{sum(1 for x in OK if 80<=x['nota']<90)}</b> nota 80–89</span>
<span class="pill"><b>{len(set(x['empresa'] for x in OK))}</b> empresas</span>
<span class="pill"><b>{len(set(x['pais'] for x in OK))}</b> países</span>
</div></header>
<main>
<section class="filtros">{filtros("k",OK)}<button onclick="lim('k')">Limpar</button></section>
<div class="cnt" id="k-n"></div><div class="grid" id="k-g">{cards(OK)}</div>
<h2 class="secao">🚫 Removidas por exigir inglês avançado/fluente ({len(REM)})</h2>
<div class="aviso">Clique para conferir a frase exata da descrição que motivou a remoção (coluna Evidência_idioma do CSV).</div>
<details><summary>Mostrar lista removida</summary>
<section class="filtros rem">{filtros("r",REM)}<button onclick="lim('r')">Limpar</button></section>
<div class="cnt" id="r-n"></div><div class="grid rem" id="r-g">{cards(REM)}</div></details>
</main><footer>Fonte: {len(V)} descrições validadas frase a frase · gerado automaticamente · {FAIXA(99)} filtro aplicado</footer>
<script>
const D={{"k":{json.dumps([[x['pais'],x['nota'],x.get('escala',''),(x['empresa']+' '+x['titulo']).lower()] for x in OK])},
      "r":{json.dumps([[x['pais'],x['nota'],x.get('escala',''),(x['empresa']+' '+x['titulo']).lower()] for x in REM])}}};
function fil(p){{const P=document.getElementById(p+'-p').value,F=document.getElementById(p+'-f').value,
 E=document.getElementById(p+'-e').value,Q=document.getElementById(p+'-q').value.toLowerCase().trim();
 let n=0;D[p].forEach((d,i)=>{{let ok=(!P||d[0]==P)&&(!E||d[2]==E)&&(!Q||d[3].includes(Q));
  if(F){{const v=d[1];ok=ok&&(F=='90+'?v>=90:F=='80-89'?(v>=80&&v<90):F=='70-79'?(v>=70&&v<80):F=='60-69'?(v>=60&&v<70):F=='50-59'?(v>=50&&v<60):v<50);}}
  const c=document.getElementById(p+'-g').children[i];if(c)c.style.display=ok?'':'none';if(ok)n++;}});
 document.getElementById(p+'-n').textContent=n+' vagas exibidas';}}
function lim(p){{['p','f','e','q'].forEach(s=>document.getElementById(p+'-'+s).value='');fil(p);}}
fil('k');fil('r');
</script></body></html>"""
open("/workspace/remote_latam/vagas_sem_ingles_avancado.html","w",encoding="utf-8").write(HTML)
print(f"MANTIDAS {len(OK)} | REMOVIDAS {len(REM)} | TOTAL {len(V)}")
print("Top 15 mantidas:")
for x in OK[:15]: print(f'  {x["nota"]:>2} | {x["pais"]} | {x["empresa"][:26]:<26} {x["titulo"][:52]:<52} [{x["_idioma_classe"]}]')
