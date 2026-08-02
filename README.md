<h1 align="center">Thiago Laidler Vidal Cunha</h1>

<p align="center">
  <img alt="Foto" src="./imgs/TLaidler.png" width="180" />
</p>

<p align="center">
  <b>Analista Quantitativo</b> na Transfero Asset Management ·
  Bacharel em Astronomia/Astrofísica (UFRJ) ·
  Mestre em Astronomia/Astrofísica (Observatório Nacional – MCTI) ·
  CEA (ANBIMA)
</p>

<p align="center">
  <a href="https://www.linkedin.com/in/thiago-laidler">LinkedIn</a> ·
  <a href="mailto:thiagolaidler@gmail.com">thiagolaidler@gmail.com</a> ·
  <a href="./pdfs/CV_ThiagoLaidler.pdf">Currículo (PDF)</a>
</p>

---

## Sobre mim

Sou bacharel em Astronomia/Astrofísica pela UFRJ e mestre pelo Observatório Nacional (MCTI),
onde trabalhei com detecção de ocultações estelares — ainda na iniciação científica, fui coautor
de [artigo no MNRAS](https://academic.oup.com/mnras) medindo a lua Umbriel com precisão de
quilômetros. Hoje sou analista quantitativo na Transfero Asset Management, aplicando estatística,
programação e machine learning a dados de mercado.

**Stack principal:** Python · SQL · Estatística · ML (scikit-learn, XGBoost, CatBoost) · Azure · Excel/VBA

---

## Como navegar este repositório

O repositório é meu laboratório aberto: cada pasta tem os **scripts completos** e, nos
projetos principais, um **README próprio** explicando motivação, método e resultados.
Se você tem 10 minutos, veja os ⭐ abaixo. Se tem 2, leia só esta tabela:

### ⭐ Projetos-destaque

| Projeto | O que é | Por que vale ler |
|---|---|---|
| [Pipeline do Mestrado](./Astrofisica/Mestrado/) | ML (RF/XGBoost/CatBoost) para detectar ocultações estelares em curvas de luz | Validação adversarial em dado real (anéis de Quaoar, separação de 86× entre anel e ruído-sósia) + [auditoria crítica do próprio pipeline](./Astrofisica/Mestrado/AUDITORIA_PIPELINE.md) |
| [Case study — estratégia sistemática em ações BR](./Analises/c9_equity_strategy_case_study/) | Research de fatores na B3 (qualidade + valor + momentum), documentado como estudo de processo | ~43 trials pré-registrados, vieses medidos **contra o próprio resultado** (20,0% → 14,8% a.a.), PSR/Deflated Sharpe — o processo, não a receita |
| [USDBRL Open Nowcast](./Analises/usdbrl-open-nowcast/) | Nowcast do dólar de abertura (9:00 BRT) a partir do futuro da CME, via paridade coberta de juros | Pipeline point-in-time à prova de lookahead, validação walk-forward honesta |
| [ML Pipeline for Trading](./Analises/ml_pipeline_for_trading/) | Pesquisa de estratégias no padrão *Advances in Financial ML* (triple-barrier, purged CV, Deflated Sharpe) | Termina num **resultado nulo documentado com orgulho** — "when it says no, it means no" |
| [Regime Detection Study](./Analises/regime_detection_study/) | Detecção de regimes de mercado com features causais | Null models duplos + feature-placebo de controle; caça um falso positivo do PSR |
| [Apostila de Estatística](./Analises/Apostila_Estatistica/) | Apostila completa escrita do zero (200+ células) | Estatística explicada com analogias físicas — da pipoca (distribuição normal) ao amigo rico no bar (média × mediana) |

### 🗺️ Mapa das pastas

| Pasta | Conteúdo |
|---|---|
| [`Astrofisica/`](./Astrofisica/) | Da iniciação científica (UFRJ) ao mestrado (ON): mecânica celeste, astroestatística e o pipeline de ocultações |
| [`Analises/`](./Analises/) | Projetos quant e de dados: finanças (FIIs, câmbio, backtests), ML, estatística aplicada — e projetos lúdicos (WoW, xadrez, Yu-Gi-Oh) |
| [`Estudo/`](./Estudo/) | Cadernos de autodidatismo: POO em Python, Bitcoin (*Mastering Bitcoin*), simulações estatísticas |
| [`morning-call-bot/`](./morning-call-bot/) | Bot que raspa, resume (NLP) e envia por e-mail as notícias do dia (G1, Yahoo Finance, CoinDesk) |
| [`Bootcamp_SDW2023/`](./Bootcamp_SDW2023/) | Projeto do bootcamp Santander Dev Week 2023 |
| [`pdfs/`](./pdfs/) | Currículo em PDF |

> 📄 **Currículos detalhados** (versões por vaga) ficam na branch [`curriculos`](../../tree/curriculos/CVs), fora da main.

---

## Meu jeito de trabalhar (o que os projetos têm em comum)

1. **Ceticismo primeiro.** Número bom demais é tratado como suspeito até prova em
   contrário: baselines triviais, null models, features-placebo e auditorias do meu
   próprio código aparecem em quase todo projeto.
2. **Sem lookahead.** Nos projetos financeiros, tudo é point-in-time: purged CV com
   embargo, validação walk-forward, features causais.
3. **Didática como método.** Eu aprendo escrevendo material que ensina — apostilas,
   aulas com exercícios e gabarito, READMEs que explicam o *porquê*, não só o *como*.
4. **Curiosidade sem fronteira.** O mesmo rigor vale para curvas de luz, dólar de
   abertura e a taxa de drop de uma montaria no World of Warcraft.
