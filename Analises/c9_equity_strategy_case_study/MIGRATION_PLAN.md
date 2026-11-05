# Plano de migração — publicar código de apoio do case study

> **Para quem executa:** este documento é autocontido. Você não precisa de contexto prévio.
> **Objetivo:** adicionar código e figuras a este case study, extraindo trechos do repositório privado `finance-utils`, **sem publicar a estratégia proprietária**.

---

## 1. Contexto mínimo

Este diretório (`Portfolio/Analises/c9_equity_strategy_case_study/`) contém hoje apenas um `README.md`: um estudo de processo sobre pesquisa de estratégia sistemática em ações brasileiras (~43 experimentos pré-registrados, vieses medidos e publicados contra o próprio resultado, PSR/Deflated Sharpe reportados). **Não há código**, e o link aparece em currículos enviados a vagas técnicas — a ausência de código é a lacuna que este plano resolve.

O código-fonte está no repositório **privado** `TLaidler/finance-utils`, na branch **`origin/apostila`** (também existe em `fable_dev`; `apostila` é o estado mais completo).

Caminho local do repositório de origem: `C:\Users\thiag\Documents\GitHub\finance-utils`

Para ler arquivos sem trocar de branch (preserva o working tree):
```bash
git show origin/apostila:mechroom/<arquivo>.py
```

---

## 2. Regra de ouro

**A estratégia roda com capital próprio do autor.** Publica-se o *método*, nunca a *receita*.

### ❌ NUNCA publicar

| Item | Onde está |
|---|---|
| `ports_final()` — as ~14 linhas que **são** a estratégia C9 | `mechroom/backtest_lab.py`, linha ~426 |
| Constantes de corte: `MOM_CUT = -0.15`, `DL_CUT = 1.0`, `CUT = 0.60`, `exit_cut`, peso ⅓ do momentum | `backtest_lab.py` (~415-416), `backtest_estrategia_final.py` |
| `build_features()` com a composição exata dos scores (q_norm, cheap) | `backtest_estrategia_final.py` |
| `sem_queda_alavancada()` (a guarda da C9) | `backtest_lab.py` ~419 |
| `WINNER_FINAL`, `REGIME_JUL`, `HIST_SHARPES` | `backtest_lab.py` ~398-414 |
| Carteira viva | `estrategia_anual/carteiras/carteira_2026.csv` |
| Qualquer `ports_l*` / `round2_ideas` / `ports_mom_hysteresis` (variantes testadas) | `backtest_lab.py` |
| Arquivo `backtest_estrategia_final.py` inteiro | — |

### ✅ Publicável

Tudo abaixo é (a) ingestão de **dados públicos brasileiros** ou (b) implementação de **metodologia de literatura aberta** (Bailey & López de Prado). Nada revela a regra da estratégia.

---

## 3. Estrutura a criar

```
c9_equity_strategy_case_study/
├── README.md                 (já existe — atualizar seção final, ver passo 6)
├── NOTE.md                   (novo — ver passo 5)
├── code/
│   ├── README.md             mapa do código
│   ├── data_sources/
│   │   ├── cvm.py            DFP da CVM (inclui deslistadas)
│   │   ├── cotahist.py       preços oficiais B3
│   │   └── macro.py          séries do BCB/SGS
│   ├── validation/
│   │   ├── metrics.py        PSR + Deflated Sharpe
│   │   └── null_models.py    nulo pareado (carteiras aleatórias)
│   └── bias/
│       └── survivorship.py   reintegração de deslistadas
└── figures/                  (opcional — ver passo 7)
```

---

## 4. Extração — arquivo por arquivo

### 4.1 `code/data_sources/` — risco zero

Copiar praticamente como estão (são ingestão de dados públicos):

| Origem (branch `apostila`) | Destino | Observação |
|---|---|---|
| `mechroom/data_center/cvm.py` (216 linhas) | `code/data_sources/cvm.py` | Baixa DFP anual da CVM; inclui deslistadas e `DT_RECEB` |
| `mechroom/data_center/cotahist.py` (102 linhas) | `code/data_sources/cotahist.py` | Preços COTAHIST da B3, as-traded |
| `mechroom/data_center/macro.py` | `code/data_sources/macro.py` | Séries BCB/SGS (Selic etc.) |

**Checagem antes de salvar:** remover qualquer caminho local absoluto, credencial, ou `import` que puxe módulo proprietário. Substituir caminhos por variável de configuração no topo do arquivo.

### 4.2 `code/validation/metrics.py`

Extrair **apenas estas duas funções**:

- `psr()` — de `mechroom/backtest_sweetspot.py`, linha ~104
- `dsr()` — de `mechroom/backtest_lab.py`, linha ~272

Ambas são implementação de Bailey & López de Prado (2014). **Atenção:** `dsr()` recebe `trial_sharpes_ann` como argumento — mantenha o parâmetro, mas **não copie a lista `HIST_SHARPES`**, que revela a família de tentativas. No docstring, explicar que a lista de Sharpes dos trials é entrada do usuário.

Adicionar docstring citando a referência:
> Bailey, D. & López de Prado, M. (2014). *The Deflated Sharpe Ratio: Correcting for Selection Bias, Backtest Overfitting and Non-Normality.*

### 4.3 `code/validation/null_models.py`

Extrair:
- `random_null()` — de `backtest_sweetspot.py`, linha ~74
- `null_blended()` — de `backtest_lab.py`, linha ~515

⚠️ `null_blended()` chama `blend_regime()` e usa a estrutura de pesos da estratégia. **Generalizar:** reescrever para receber a função de construção de carteira como parâmetro (`portfolio_fn`), em vez de chamar a estratégia internamente. O valor publicado é o *método do nulo pareado* (mesmo n por ano, mesmo universo, mesmos custos), não a carteira que ele compara.

### 4.4 `code/bias/survivorship.py`

Extrair de `mechroom/backtest_v3_sobrevivencia.py` (99 linhas) **apenas a parte de reintegração**: o mapeamento ticker↔CVM e a recolocação das ~210 empresas deslistadas no universo e nos retornos.

❌ **Remover** a parte que roda a estratégia V3 sobre o universo corrigido (isto é, qualquer chamada a `v3()` ou filtros de elegibilidade com cortes).

Esta é a peça **mais importante** do pacote: é o código por trás do número central do case study (viés de sobrevivência = −1,6 p.p./ano).

### 4.5 `code/README.md`

Escrever um mapa curto (~30 linhas) explicando:
- o que cada subpasta faz;
- que os dados usados são públicos (CVM, B3, BCB);
- que o código é de apoio metodológico, não um sistema executável de ponta a ponta;
- como rodar cada módulo isoladamente.

---

## 5. `NOTE.md` — declarar a omissão

Criar na raiz do case study. Conteúdo (ajustar a redação, manter o espírito):

> ## O que não está publicado aqui — e por quê
>
> Este repositório traz o código de **apoio metodológico** do estudo: ingestão dos dados públicos, implementação das métricas de validação (PSR, Deflated Sharpe), geração do nulo pareado e a medição do viés de sobrevivência.
>
> Não estão aqui a regra final de seleção da carteira, os parâmetros de corte, a composição exata dos scores nem a carteira em uso. A estratégia opera com capital próprio, e o objetivo deste material é mostrar **como o resultado foi construído e auditado** — não distribuir a receita.
>
> Todos os métodos usados estão em literatura aberta: Bailey & López de Prado (2014) para PSR/DSR, e López de Prado, *Advances in Financial Machine Learning*, para o desenho de validação.

**Tom:** declarar a omissão abertamente vale mais que omitir em silêncio — e é coerente com o resto do documento.

---

## 6. Atualizar o `README.md` existente

Na seção **"7. O que não está aqui — e por quê"**, acrescentar um parágrafo apontando para o código:

> O código de apoio metodológico está em [`code/`](./code): ingestão dos dados públicos, PSR e Deflated Sharpe, nulo pareado e a medição do viés de sobrevivência. Ver [`NOTE.md`](./NOTE.md) para o que ficou de fora.

---

## 7. Figuras (opcional, só se houver tempo)

Se os artefatos estiverem disponíveis (`origin/finance_study_room` é a única branch que comita `reports/` e `data/*.parquet`), gerar duas imagens para `figures/`:

1. **Arco de correção de vieses**: barras mostrando 20,0% → 18,4% → 16,0% → 14,8% a.a.;
2. **Distribuição do nulo pareado**: histograma das 500 carteiras aleatórias com a posição do resultado real.

Se os dados não estiverem acessíveis, **pular** — o texto do README já carrega os números.

---

## 8. Verificação antes do commit

Rodar na pasta `code/` e conferir que **não há nenhuma ocorrência**:

```bash
grep -rniE "0\.60|-0\.15|MOM_CUT|DL_CUT|exit_cut|ports_final|WINNER_FINAL|HIST_SHARPES|sem_queda_alavancada|tri-score" code/
```

Esperado: **nenhum resultado**. Se algum aparecer, remover antes de prosseguir.

Conferir também:
- [ ] Nenhum caminho local absoluto (`C:\Users\...`)
- [ ] Nenhuma credencial ou token
- [ ] Nenhum nome de ticker da carteira viva
- [ ] Todo módulo roda ou falha com mensagem clara (sem depender de arquivo que não existe no repositório)

---

## 9. Commit

```bash
cd "C:/Users/thiag/Documents/GitHub/Portfolio"
git add Analises/c9_equity_strategy_case_study/
git commit -m "Add supporting code to C9 case study (methodology only)

Public data ingestion (CVM, B3 COTAHIST, BCB), validation metrics
(PSR, Deflated Sharpe), paired null models and survivorship-bias
measurement. Strategy rule and parameters intentionally excluded."
git push origin main
```

⚠️ A `main` local pode estar atrás do `origin` — rodar `git pull` antes.

---

## 10. Aviso separado, não relacionado a este plano

O repositório `finance-utils` contém, na branch `finance_study_room`, as pastas `nubank_case/` e `yipitdata_case/` com material de processos seletivos que era **explicitamente confidencial**. Enquanto o repositório permanecer privado, não há exposição. **Nunca torná-lo público sem remover essas pastas antes.**
