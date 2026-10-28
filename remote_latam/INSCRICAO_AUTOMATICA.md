# Inscrição automática no LinkedIn — o que é possível e como fazer com segurança

## Resposta direta
**Sim, dá para automatizar — mas NÃO aqui nesta ferramenta, e NÃO com sua senha.**
Eu não executo ações em seu nome no LinkedIn (risco de banimento da SUA conta) e você
não deve me enviar credenciais. O caminho seguro é rodar um script **na sua máquina**,
com suas credenciais locais, usando a fila que já deixei pronta.

---

## 1. Por que não receber sua senha / não logar por você
| Risco | Consequência |
|---|---|
| Credencial em chat/servidor de terceiros | Sequestro de conta; violação da LGPD/GDPR |
| Login via automação detectado pelo LinkedIn | Restrição temporária → **ban permanente** (é TOS do LinkedIn) |
| Requisições em massa sem padrão humano | Captcha infinito, conta "flagged for review" |
| Candidatura errada em escala | Dano reputacional: recrutadores veem CVs enviados fora do perfil |

Regra prática: se um robô envia 300 candidaturas idênticas, o algoritmo marca a conta,
e as próximas candidaturas podem nem chegar ao recrutador.

---

## 2. Ferramentas maduras que fazem isso na SUA máquina
| Ferramenta | Como funciona | Quando usar |
|---|---|---|
| **JobSpy** (`linkedin-jobs-api`, Python + Playwright) | Autentica com cookie `li_at` seu (sem senha no código), filtra Easy Apply, preenche e envia | Melhor opção técnica; integra com a fila daqui |
| **LinkedIn Easy Apply nativo** | Botão "Candidatura fácil" + respostas salvas | Manual, mais seguro, ótimo p/ top 50 |
| **AutoApply / apply-bot (open source)** | Playwright + perguntas pré-configuradas em YAML | Bom meio-termo, exige ajuste fino |
| **Extensões "auto-apply"** | Plugin no navegador | ⚠️ Muitas vendem seus dados; evite |

### Setup recomendado (JobSpy)
```bash
python -m venv .venv && source .venv/bin/activate
pip install -U jobspy            # inclui linkedin-jobs-api
playwright install chromium
cp .example.env .env             # cole seu cookie li_at AQUI (nunca em chat)
python -c "from jobspy import scrape; scrape(
    sites=['linkedin'],
    linkedin_description_results='none',
    location='Argentina|Chile|Colombia|Brazil',
    remote=True, easy_apply=True,
    keywords='arquiteto de solucoes cloud', results_wanted=25)"
```
O cookie `li_at` você obtém assim: login no LinkedIn no navegador → F12 → Application →
Cookies → copie o valor de `li_at`. Ele expira sozinho em ~1 ano e pode ser revogado.

---

## 3. A fila que já preparei para você (neste repositório)
Arquivos gerados agora:

- `remote_latam/fila_inscricao.py` — pré-processador (re-executável)
- `remote_latam/fila_top50.csv` — **as 50 primeiras candidaturas**, ordenadas por nota
- `remote_latam/fila_completa.csv` — 172 vagas com nota ≥ 80 (das 657 validadas sem inglês avançado)

Colunas: `prioridade | nota | empresa | cargo | pais | local | modo | publicada |
easy_apply_provavel | facilitated_keywords | link | status`

Filtros de segurança embutidos no script:
- remove vagas marcadas **"Presencial (revisar)"** fora do Brasil (não são remotas);
- mantém apenas nota ≥ 80 (compatibilidade alta com sua Versão Mestre);
- separa lote de 50 para começar (≈2 dias no limite seguro).

Regenerar com outro corte:
```bash
cd remote_latam
python fila_inscricao.py --min-nota 90     # só as 40+ melhores
```

---

## 4. Protocolo anti-ban (limites que recomendo respeitar)
```
Máximo 25 candidaturas/dia          (top 150 = ~6 dias corridos)
Pausa aleatória 45–120 s entre cada envio
Nunca rodar 24/7: 1 sessão/dia, horário comercial
Rode a partir da SUA rede/IP normal (nunca proxy compartilhado)
Revise as 10 primeiras manualmente antes de liberar o lote
Pare imediatamente se aparecer captcha ou "conta temporariamente restrita"
```

## 5. Antes de apertar "go": checklist obrigatório
1. **Preencher os `[X]%` e `[R$ Y]`** da Versão Mestre — Easy Apply com métricas vazias mata taxa de entrevista.
2. Salvar **respostas padrão** nas perguntas do Easy Apply (anos de experiência, autorização de trabalho, pretensão salarial, disponibilidade para viajar).
3. Decidir **CV por eixo**: nuvem/FinOps vs. Dados/IA vs. Gestão ITSM — use a Técnica do Espelho (3 PDFs nomeados, ex.: `CV_Francisco_CloudFinOps.pdf`). Para vagas em ES/EN, gerar variações traduzidas.
4. Verificar **autorização de trabalho**: muitas vagas AR/CL/CO/PE pedem contrato local ("freelance internacional" ou cidadania). Isso não é barreira de idioma, mas é barreira legal — vale filtrar por "latam remote / contractor".
5. Manter planilha de controle (`status`: PENDENTE → ENVIADA → ENTREVISTA → DESCARTADA) para não duplicar candidatura na mesma empresa.

---

## Próximo passo sugerido
Você roda o JobSpy localmente com o cookie `li_at` e a `fila_top50.csv` como input.
Se quiser, eu escrevo o **driver pronto** (`auto_apply.py`) que lê essa fila, monta os
parâmetros do JobSpy e aplica pausas/limite diário — sem nunca tocar em suas credenciais.
