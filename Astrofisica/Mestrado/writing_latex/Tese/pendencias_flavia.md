# Pendências da carta da banca (Dra. Flavia L. Rommel) após a aplicação automática

> **Situação em 01/10/2026.** As correções da Flavia que uma LLM podia fazer sem o autor, e que o painel (Feynman, Sagan, Simons) aprovou, **já estão nos `.tex`** (veja com `git diff`).
> Este arquivo lista só os **pontos da Flavia que continuam em aberto**, total ou parcialmente, agrupados pelo tipo de ação necessária.
> Os textos prontos de cada item estão em [`correcoes_banca.md`](correcoes_banca.md) (Partes A, B e C); a discussão do painel, em [`painel_memorias.md`](painel_memorias.md).

---

## 1. Exigem intervenção do autor nas figuras ou nos dados

| Item | O que falta |
|---|---|
| Geral i | Fonte (tamanho e tipo) de todas as figuras; traduzir para o português os textos dentro das imagens (eixos, legendas internas, títulos) |
| Geral j | Decidir se mantém ou troca a Fig. 2.1 (Chariklo). O texto de transição para Umbriel **já foi aplicado** |
| Cap2 mm | Fundir as Figs. 2.3 e 2.4 e marcar imersão e emersão com linha ou seta. As legendas **já foram corrigidas** |
| Cap3 24 | Substituir a Fig. 3.9 por um exemplo de astronomia (ex.: morfologia de galáxias) ou traduzi-la. A citação a Zhong et al. (2023) e a leitura dos 6 painéis **já foram aplicadas** |
| Cap5 6 | Inset com zoom na Fig. 5.2 e nas figuras semelhantes do apêndice. Trocar o título "Precisão-Revocação" dentro da imagem (o código gera esse texto em `train_model.py:847-849`). A legenda provisória já explica que revocação = sensibilidade |
| Cap5 8 | Fig. 5.5 (recortes de Quaoar): fonte e rótulos coerentes com o texto e a Tab. 5.8 (Q1R, *baseline*, etc.). Rodar RF e Regressão Logística nos recortes, se quiser os quatro modelos (o `.dat` de Quaoar não está no repositório) |
| Cap5 10 | Fig. 5.7: fonte e tradução. O reposicionamento do float **já foi aplicado** |
| Cap6 ii | Nova figura comparando uma curva de baixo SNR com uma de alto SNR. O número de *features* (11) **já foi informado** no texto |

## 2. Exigem confirmação de um fato que só o autor sabe

| Item | Pergunta da banca | O que o painel encontrou (para você confirmar) | Texto pronto em |
|---|---|---|---|
| Cap1 v | "...coletados nos últimos ~X anos (REF)" | Sugestão: "desde a publicação do Gaia DR2, em 2018", citando Herald et al. (2020) ou Sicardy et al. (2024) | Parte A, Cap1 v |
| Cap1 z | "a bordo de telescópios": espaciais ou em solo? | Duas redações prontas, uma para cada intenção | Parte A, Cap1 z |
| Cap2 cc.iv | Referência do Gaia | Citados Gaia2016 + GaiaDR3 (genérico). Se a frase se refere à previsão de Umbriel (set/2020), a *release* usada foi provavelmente a DR2 | Parte B, cc.iv |
| Cap2 mm | Legenda da Fig. 2.4b | As linhas verdes tracejadas são cordas negativas? Se sim, vale dizer isso na legenda | Parte B, mm |
| Cap3 2 | Mencionar o teorema conjecturado com ML e depois demonstrado | Gryak et al. (2018) trata de *decidir* conjugação em grupos, não de conjecturar teoremas. O exemplo canônico é Davies et al. (2021, *Nature*). Qual você tinha em mente? | Parte C, Cap3 2 |
| Cap3 21 | Título da Seção 3.6 | Opcional: "Características dos dados e validação dos modelos" | Parte C, Cap3 21 |
| Cap4 2 | Quantas curvas foram baixadas; licença CC-BY-4.0 | Pelos artefatos: 923 prévias baixadas, 912 inseridas no banco, 931 observações (928 positivas, 3 negativas). A licença não foi verificada no ReadMe do CDS. **Falta também a data de acesso** no `\bibitem{HeraldBocc2016}` (a ABNT exige em documento online) | Parte B, Cap4 2 |
| Cap4 4 | O que eram as "curvas defeituosas"? | O código não marca defeitos: a triagem foi visual (11 de 923 descartadas). Duas curvas inseridas têm o tempo fora de ordem | Parte B, Cap4 4 |
| Cap4 5 | Como e por que se checou o alinhamento temporal | O código **não** faz checagem nem conversão: as 18 curvas do Grupo do Rio estão em dias julianos e as do VizieR em segundos. Houve checagem manual? | Parte B, Cap4 5 |
| Cap4 17 | Os fóruns são da IOTA? | Se sim, citar a IOTA e explicar brevemente quem é | Parte B, Cap4 17 |
| Cap6 iii | Onde o código está disponível | github.com/TLaidler/Portfolio (`Astrofisica/Mestrado/pipeline`), público. Mas `*.csv` está no `.gitignore`: dataset, resultados e `.dat` simulados não estão versionados. Confirme o URL e considere tag, DOI (Zenodo) e licença | Parte C, Cap6 iii |
| Cap6 iv | "orientando futuras decisões sobre coleta de dados": imagens ou curvas? | Proposta: coleta de **novas curvas rotuladas para treino**, não aquisição de imagens | Parte C, Cap6 iv |
| Geral p | Apêndice C sem chamada no texto | A chamada no Cap. 4 **já foi aplicada**. Ficam com você: a chamada no Cap. 6 com o URL (ligada a Cap6 iii), a frase-TODO no fim do Apêndice C ("A data de geração do ambiente ... deve ser registrada pelo autor") e a versão exata do Python ("3.x") | Parte A, Geral p |

## 3. Decisões do autor com o orientador

| Item | Decisão | Estado atual / proposta |
|---|---|---|
| **Cap5 1** | Renomear os experimentos para seguir a ordem de execução | Nomes intocados. Proposta: 1, 1.1, 1.2a, 1.2b, 2, 3, 3.1, com tabela de correspondência. **Atenção:** ao renomear, corrija também as contagens. O Exp. 4 tem 13 *features* (não 14) e o Exp. 5 tem 12 (não 13), conforme o `feature_names.pkl`; o Exp. 6 **mantém** `Feature_Savgol_Min` (Parte C, Cap5 1) |
| Geral c | Política de estrangeirismos | Já aplicados: itálico, `\texttt` para código, tradução na 1ª ocorrência. Em aberto: (ii) trocar por termo em português onde ele existe (*overfitting* → sobreajuste, *frames* → quadros, *dataset* → conjunto de dados); (iii) nomes de métodos e métricas (Random Forest, F1-score) em fonte normal ou itálico; o termo "Machine Learning" no **título da dissertação** e nas palavras-chave |
| Geral d | Estender "curva de luz de ocultação" | A definição está na Introdução. Em aberto: usar a forma completa na 1ª ocorrência de cada capítulo, nos títulos e no resumo |
| Geral h | Lista de abreviaturas e siglas (e glossário) | Rascunho pronto (Parte A, Geral h) |
| Geral m | Notação | Aplicada a versão mínima: L_F (Fresnel), n (exemplos), f̂_m (*boosting*), K (K-means), q (dobras), f\* (viés–variância), s_MAD, F (fluxo, Cap. 5), θ_j (Cap. 5). Opcionais em aberto: sigmoide σ(z) × desvio padrão σ; J da inércia do K-means; ΔI(n) × ΔG; ativar a lista de símbolos da classe |
| Geral o | Dar mais ênfase à motivação de Centauros e TNOs | A abertura do §5 da Seção 1.1 já foi reescrita (item q). Em aberto: o parágrafo sobre o que as ocultações já revelaram (anéis de Chariklo, Haumea e Quaoar além do limite de Roche), com texto e referências prontos (Parte A, Cap1 q, 2º parágrafo) |
| Cap3 8 | Fundir as Figs. 3.2 e 3.3 numa só | As legendas já são descritivas; a fusão é opcional (a própria banca deixa a seu critério) |
| Cap3 22 | VP/VN em vez de TP/TN | Aplicada a alternativa da própria banca: mantidas as siglas em inglês, com o significado. A troca por VP/VN em toda a tese segue em aberto |
| Cap4 1 | Padronizar *features* × características | Hoje o texto mistura os dois. Opção mais barata: *features* (em itálico) em todo o texto |
| Cap4 6 | Reestruturar a Seção 4.4 | O link do simulador **já foi corrigido** (DOI). Em aberto: fundir 4.4.2 e 4.4.3 numa subseção "Curvas reais...". O painel recomenda fundir, não apagar, para não perder a descrição do recorte |

## 4. Pontos em que o painel discorda da sugestão literal (não aplicados)

| Item | Sugestão da banca | Por que não foi aplicada | Alternativa |
|---|---|---|---|
| Cap4 17a | Retirar "ruído de fótons" | O ruído de Poisson é a fonte fundamental de ruído do sinal estelar, e o próprio simulador o inclui | Manter e definir (Parte B, Cap4 17a) |
| Cap4 19 | "...representativo da realidade das campanhas observacionais" | Os dados contradizem: 79% das negativas são simuladas, com ruído cerca de 3× menor (σ_base 0,021 × 0,058) | Redação alternativa (Parte B, Cap4 19) |

**Aplicados com ajuste em relação à sugestão literal** (vale conferir):
- **Cap2 bb:** a ressalva sobre asteroides próximos foi trocada pela condição física (tamanho do corpo × escala de Fresnel e diâmetro estelar).
- **Cap2 cc:** V_S inclui o movimento orbital da Terra, o termo dominante para TNOs.
- **Cap2 jj.iv:** o SORA já estava definido; a forma foi harmonizada.
- **Cap4 9:** "posição ao longo da corda" foi mantida e explicada (x = V_S·(t − t₀)).
- **Cap5 9:** 0,7 pp em vez de "~2 pp", tratado como hipótese.
- **Cap5 11:** o desvio padrão já estava na Tab. 5.10; o texto passou a usá-lo.
- **Cap3 10:** gradiente corrigido para −0,125; sem mínimo finito em dados separáveis.
- **Cap3 16:** "competições" explicadas sem número.

## 5. Para conferir na primeira compilação (Overleaf)

- **Pacotes novos:** `indentfirst`, `upquote` e `\raggedbottom`.
- **Títulos com `\texorpdfstring`:** capítulos 3 e 4; Seções 3.1, 3.3, 3.6.3 e 4.1; Subseção 3.3.4.
- **Bibliografia:** `\href` no `\bibitem{Simulator}`; acentos por macro (`\'{n}`, `\H{O}`).
- **Floats e tabelas:**
  - largura nova da Tab. 3.2, 14 cm (confira se cabe);
  - Tab. "13 *features*" agora em ambiente `table` com legenda;
  - Fig. 5.3 com dois painéis;
  - Fig. 5.7 com `[!htbp]`.
- **Espaçamento:** o vão entre os parágrafos 5 e 6 da Seção 1.1 (Cap1 s). Se continuar depois do `\raggedbottom`, a causa é outra.
- **Rótulo novo:** a coordenação acrescentou o rótulo ASCII `sec:construcao_dataset` ao lado de `sec:construção_dataset` (rótulos com acento podem falhar no `\ref`). O novo `\ref` usa o ASCII.

---

*Fora do escopo deste arquivo:* as correções que o painel encontrou e a banca **não** pediu (Extras P0: vazamento entre recortes-irmãos, limiar escolhido no teste, falsos alarmes com τ = 0,03, faixas de F1, 802 → 927, *gain*/*weight*, "trânsito", "perpendicular à corda", Fresnel estrela–corpo, `SNR_dip`, etc.) **não foram aplicadas** e estão descritas em `correcoes_banca.md`, Seção 5.
