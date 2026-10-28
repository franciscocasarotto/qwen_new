# Job Search Pipeline — Francisco Casarotto

Automação de coleta, pontuação e curadoria de vagas (LinkedIn) para o perfil
**Arquiteto de Soluções Cloud / FinOps / IA & Dados** (15+ anos).

## Estrutura

```
/workspace
├── coletar_vagas_linkedin.py      # Coleta inicial (foco BR presencial+híbrido)
├── pontuar_vagas.py               # Motor de scoring por keywords do CV
├── gerar_planilha_vagas.py        # Planilha v1 (vagas_compativeis.xlsx/csv)
├── vagas_brutos.json              # Raw da 1ª coleta (115 vagas)
├── vagas_enriquecidas.json        # Com descrição completa
├── vagas_compativeis.{xlsx,csv}   # Entregável v1
├── vagas_remotas_sul_america.{xlsx,csv}  # Entregável LATAM (958 vagas, 10 países)
└── remote_latam/                  # Pipeline principal (remoto · Brasil)
    ├── coletar_br_remoto.py       # Coleta API pública LinkedIn (f_TPR=r1296000 + remoto)
    ├── baixar_validar_br.py       # Baixa descrição das 1.003 vagas (validação de links)
    ├── pipeline_br.py             # Classifica modo (remoto/híbrido) + remove inglês avançado
    ├── gerar_planilha_br.py       # → vagas_remotas_brasil_validadas.xlsx
    ├── gerar_lista_links.py       # → lista_links_linkedin.{csv,txt,html} + TOP50 md
    ├── TOP50_links_para_validar.md
    ├── lista_links_linkedin.html  # Validação interativa (checkbox + busca)
    ├── fila_inscricao.py          # Monta fila de candidatura segura (máx 25/dia)
    ├── INSCRICAO_AUTOMATICA.md    # Guia anti-ban + setup local com cookie li_at
    ├── importar_indeed.py         # Import manual do Indeed (anti-bot 403)
    ├── consolidar_fontes.py       # Dedupe LinkedIn × Indeed
    ├── br_remoto_final.json       # Base validada: 761 vagas remotas BR sem inglês obrigatório
    └── *.log                      # Logs de execução (gitignored)
```

## Fluxo de atualização

```bash
cd remote_latam
python coletar_br_remoto.py        # nova coleta (últimos 15 dias)
python baixar_validar_br.py       # baixa descrições + valida HTTP dos links
python pipeline_br.py             # filtra remoto + remove inglês avançado obrigatório
python gerar_planilha_br.py       # regenera planilha final
python gerar_lista_links.py       # regenera listas de links p/ validação manual
```

## Regras de curadoria aplicadas

- Janela: **últimos 15 dias** (`f_TPR=r1296000`), ordenado por data.
- **Remoto Brasil**: classificação frase-a-frase (desc > filtro do LinkedIn).
- **Inglês**: removidas 301 vagas (~31%) que exigem avançado/fluente obrigatório;
  mantidas as com desejável/básico/leitura técnica.
- **Scoring**: keywords ponderadas do CV mestre (FinOps=10, SAP/BTP=9,
  Multi-cloud/OCI/RAG/Databricks/ITSM=8...) + senioridade (Sr/Especialista/Lead +)
  e penalização para júnior/analista assistente.

## Segurança / ToS

Nenhuma automação de login ou candidatura é executada neste repo.
As inscrições são manuais pelos links, ou via driver local opcional descrito em
`remote_latam/INSCRICAO_AUTOMATICA.md` (limite 25/dia, jitter 45–120 s, cookie `li_at`
nunca commitado).
