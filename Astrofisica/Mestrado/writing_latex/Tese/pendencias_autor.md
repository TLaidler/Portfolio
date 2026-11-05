# Pendências para o autor — em ordem, uma de cada vez

> **Situação em 05/11/2026 (rodada 3).** Esta rodada fez o que estava bloqueado por falta de dados e aplicou as decisões
> do autor de 05/11. Nada desta rodada foi commitado no Portfolio (ver item 9). O histórico das rodadas anteriores está
> no `git log`; os itens antigos da Flavia continuam em [`pendencias_flavia.md`](pendencias_flavia.md) e os textos
> prontos em [`correcoes_banca.md`](correcoes_banca.md).

---

## 0. Feito nesta rodada

**Decisões do autor aplicadas**
- Conclusão da rodada 2 aprovada: fica a configuração 1.2b (opção a).
- **Estrangeirismos:** termo em português na 1ª ocorrência com o original entre parênteses, depois só o português.
  O título da dissertação e as palavras-chave mantêm os termos originais. Glossário principal: características
  (*features*), cadeia de processamento (*pipeline*), linha de base (*baseline*), queda (*dip*), conjunto de dados
  (*dataset*), sobreajuste/subajuste, valores atípicos, programas (*scripts*), comitês (*ensembles*), divisões
  (*splits*), agrupamento. Nomes de métodos, métricas e softwares (Random Forest, XGBoost, *boosting*, F1, *gain*…)
  ficam no original. São ~300 trocas em 10 arquivos; o backup dos `.tex` anteriores está no histórico do git.
- **TP/TN/FP/FN:** siglas em inglês, com o significado em inglês e português na 1ª ocorrência (Cap. 3, matriz de
  confusão). A repetição no Cap. 5 foi retirada.
- IOTA continua sem menção no Cap. 4; a citação a Gryak et al. (2018) foi mantida; "coleta de dados" foi restaurada no
  Cap. 6 (tinha saído na rodada 2), no sentido de novas curvas rotuladas.

**Itens que estavam bloqueados**
- **Tabelas da reanálise recuperadas.** O `dataset_final.csv` lido pela reanálise (`resultado1_.../`, colunas `Occ_*`)
  não existia nesta máquina. É o `outputs/dataset_final.csv` com as colunas `IOTA_*` renomeadas. Prova: rodando
  `reanalise_banca.py` com ele e as versões do Apêndice B, as 10 figuras saem idênticas byte a byte e o `resumo.json` só
  difere na 16ª casa decimal. As tabelas `.csv` estão de volta em `outputs/reanalise_banca/`.
- **Curvas simuladas:** as 702 `.dat` existem (`synthetic_curve/output/`, no disco e no repositório público).
- **Quaoar refeito com os modelos da 1.2b** (`pipeline/model_in_practice/quaoar_reanalise.py`, resultados em
  `outputs_quaoar_1.2b/`). Cap. 5, Cap. 6, resumo e *abstract* atualizados; a "Nota sobre os modelos" saiu.
  - Curvas inteiras: as três recebem p̂ ≥ 0,985 dos quatro modelos.
  - Recortes (agora com os quatro modelos, como a Flavia pediu): Q2R fica abaixo do limiar da validação cruzada em
    todos; no XGBoost, Q2R recebe ~190× a probabilidade do ruído (antes: 86×) e ~250× a do controle.
  - Janelas ampliadas: no XGBoost as probabilidades caem; no CatBoost sobem um pouco; em nenhum modelo chegam ao
    limiar. A conclusão ("a janela curta não é a causa") se mantém.
  - **Varredura cega (nova):** com τ = 0,03, 3–6 % de alarmes falsos por janela nessa curva. A janela escolhida sobre
    o Q2R(1) fica acima de todas as 123 janelas sem evento de 15 s; com janelas não alinhadas, até 2 janelas sem
    evento ficam acima da melhor janela sobre cada anel (flutuação rasa em +611 s).
  - Figura nova: `Tese/pngs/reanalise/quaoar_recortes.png` (português, fonte grande, rótulos iguais aos da tabela).

**Fatos verificados (pesquisa em 05/11; evidências no relatório da sessão)**
- **Gaia (Cap. 2):** na análise de Umbriel (Assafin et al. 2023, Tab. 1), a posição da estrela vem do Gaia DR3 e o
  diâmetro angular do Gaia DR2. A previsão (IOTA, abr/2020) não informa o catálogo. Frase acrescentada no Cap. 2.
- **Chiron (Cap. 4):** a curva do banco é da ocultação de **10/09/2023** (Pereira et al. 2025, ApJL 992, L19), e não
  da de 15/12/2022 (Ortiz et al. 2023). A citação foi trocada (`Chiron2025`) e o `\bibitem{Chiron2023}` saiu. Causa da
  observação sem pontos: o arquivo é CSV com cabeçalho; o programa de importação registra a observação antes de ler a
  curva, a leitura falha e o `commit` grava a observação vazia. **Continua valendo: não reimportar antes do depósito.**
- **Curvas "defeituosas" (Cap. 4):** o código não marca nem descarta curvas defeituosas. A consulta ao `B/occ/asteroid`
  retornou 6765 entradas; 923 viraram arquivo (transferências que falharam sem nova tentativa + arquivos sobrescritos
  por terem o mesmo objeto, observador e mês); 11 das 923 foram descartadas na importação como duplicatas aparentes
  (observador com ponto ou hífen vira `Unknown`). O campo de origem é `Manual Import` nas 931 observações. Texto
  reescrito.
- **Alinhamento temporal (Cap. 4):** não existe checagem de alinhamento no código; a única ordenação é o
  `ORDER BY time` na leitura (corrige a curva `Toni_2014-03`, gravada em ordem decrescente). Unidades confirmadas;
  datas com resolução de mês. Texto reescrito.
- Umbriel: o banco tem 18 das 24 cordas publicadas (15 de 19 positivas, 3 de 5 negativas). Acrescentado no Cap. 4.

---

## 1. ⚠️ Contradição registrada: dados de Quaoar públicos (decisão adiada pelo autor em 05/11)

- O Cap. 5 diz que os dados de Quaoar foram **"gentilmente cedidos pelo autor principal"** de Pereira et al. (2023).
- O repositório público `github.com/TLaidler/pipeline_occ_ml` contém esses dados em
  `Mestrado/pipeline/model_in_practice/quaoar/` (`CFHT_Wircam_Ks_cor-time.dat`, `Gemini-Alopeke_Blue-r.dat`,
  `Gemini-Alopeke_Red-z.dat`) e ainda um `WhatsApp Image 2026-03-03 at 12.16.31.jpeg`, desde o primeiro push (20/08).
- Até a rodada 2, a "Nota sobre os modelos" dizia que os dados "não fazem parte do repositório". A nota saiu nesta
  rodada (o estudo foi refeito), então o texto não afirma mais isso, mas a questão de fundo continua: **dados cedidos
  estão públicos.**
- Decidir com o orientador e com quem cedeu os dados:
  - (a) pedir autorização para mantê-los públicos e dizer isso no texto (ex.: "cedidos e disponibilizados com
    autorização"); ou
  - (b) retirá-los do repositório **inclusive do histórico** (`git filter-repo`) e acrescentar ao README que o estudo
    de Quaoar exige os dados, disponíveis sob pedido. Nesse caso, `quaoar_reanalise.py` deixa de ser reproduzível por
    terceiros.
- Em qualquer caso, a imagem do WhatsApp não deveria estar no repositório.

## 2. Bloqueado por permissão nesta sessão (precisa de você)

1. **Push do repositório público.** O clone `C:\Users\thiag\Documents\GitHub\pipeline_occ_ml` tem 2 commits locais
   (`3354905`, `9ae5ccc`) com `reanalise_banca.py`, `gerar_apendice_a.py`, as tabelas e os modelos da reanálise, o
   `dataset_final.csv` de entrada, `quaoar_reanalise.py` e seus resultados, `requirements_reanalise.txt` e o README
   atualizado. Falta `git push origin main` (resolva antes o item 1, se escolher a opção b).
2. **PDF marcado (diff) da rodada 3.** Esta máquina não tem LaTeX nem `latexdiff`, e o download do tectonic/latexdiff foi
   bloqueado. Com permissão, gero:
   - `teseon_diff_rodada3.pdf`: só o que mudou desde o último commit (`fc77553`);
   - `teseon_diff_lillian_v2.pdf`: rodada Lillian completa (desde `099daf2`), com as correções desta rodada;
   - `teseon_diff.pdf` atualizado (desde a versão da banca, `eca76fc`).

   Sem permissão: `latexdiff --flatten --type=UNDERLINE <teseon.tex antigo> teseon.tex > teseon_diff_rodada3.tex`
   numa máquina com TeX Live/MiKTeX (a versão antiga sai de `git worktree add ../tese_antiga fc77553`).

## 3. Confirmar (fatos inferidos ou textos novos que dependem de você)

| # | Onde | O que confirmar |
|---|---|---|
| 1 | `\bibitem{HeraldBocc2016}` | **"Acesso em: 1 jun. 2025"** foi inferido dos commits `2294af8`/`fdfc4e0` (consulta e banco de 01/06/2025). O catálogo é atualizado (hoje 12558 linhas, contra 6765 na consulta), então a data importa. |
| 2 | Cap. 4, rótulos | O texto dizia que, no VizieR, o rótulo "provém dos curadores". No código, **todas** as curvas do VizieR vão para `positive` e nenhuma é negativa no banco. O texto agora diz que o rótulo positivo é uma suposição, conferida pela triagem visual. Confirme se o `B/occ` pode conter cordas negativas e se a triagem visual de fato aconteceu. |
| 3 | Cap. 4, Chiron | Troca de Ortiz et al. (2023) por Pereira et al. (2025). Se quiser manter Ortiz et al. (2023) como contexto, a referência correta é A&A 676, **L12**. |
| 4 | Licença do `B/occ` | Não foi possível confirmar CC-BY-4.0 (o CDS não respondeu; o DataCite diz "Refer to CDS usage"). O texto não afirma licença. |
| 5 | Cap. 1 | "~X anos": desde quando os dados vêm sendo coletados? (sugestão: desde o Gaia DR2, 2018) |
| 6 | Cap. 1 | "a bordo de telescópios": espaciais ou em solo? |
| 7 | Cap. 2, Fig. 2.4b | As linhas verdes tracejadas são cordas negativas? |
| 8 | Cap. 2 | O texto que contextualiza o "Grupo do Rio" está correto? |
| 9 | Folha de rosto | `\date{10}{06}{2026}`: os slides oficiais da defesa são de 14/08/2026. Confirme a data da defesa. |

## 4. Figuras que dependem de você

1. Fonte maior e textos traduzidos nas figuras antigas dos Caps. 2–4 (Lillian; Flavia "Geral i").
2. Recortar a parte da legenda que sobra na Fig. 2.2(d) (Lillian).
3. Fig. 3.9: trocar por um exemplo astronômico ou traduzir (Flavia Cap3 24).
4. Opcional: fundir as Figs. 2.3 e 2.4, marcando imersão e emersão (Flavia Cap2 mm).
5. ~~Fig. 5.5 de Quaoar~~ — feita nesta rodada.

## 5. Decisões de estilo ainda abertas (`pendencias_flavia.md`, seção 3)

- "curva de luz de ocultação" por extenso na 1ª ocorrência de cada capítulo;
- lista de siglas;
- notação opcional;
- motivação de Centauros e TNOs;
- fusão das subseções 4.4.2 e 4.4.3.

(Estrangeirismos, TP/TN e *features* × características foram decididos em 05/11.)

## 6. Elementos pré-textuais (`teseon.tex`, linhas 60–78)

- Nomes e instituições da **banca** (`\examiner{...}{Nome Sobrenome}{Instituicao}`, hoje com espaços reservados).
- **CDU** (`\cducode{000.000.000}`) e código *cutter*, fornecidos pela biblioteca.

## 7. Compilar no Overleaf e conferir

1. Suba as figuras novas de `Tese/pngs/reanalise/` — inclusive **`quaoar_recortes.png`**, nova nesta rodada.
2. Compile com pdfLaTeX. Nesta rodada não houve compilação; a checagem estrutural passou (chaves balanceadas, todo
   `\ref` com `\label`, toda citação com `\bibitem`).
3. Confira os títulos dos Caps. 3 e 4, que mudaram ("Modelos e algoritmos de aprendizado de máquina";
   "Metodologia: Cadeia de Processamento para Detecção"), e a tabela de Quaoar, agora com 6 colunas.
4. A lista da seção 5 de `pendencias_flavia.md` continua valendo.

## 8. Reprodutibilidade (para não desfazer correções)

- `gerar_apendice_a.py` **reescreve** `apendice_experimentos.tex`. O programa foi ajustado aos termos novos e, rodado
  hoje, gera um arquivo idêntico ao da tese. Se editar o Apêndice A à mão, edite também o programa (ou não o rode).
- Ambiente da reanálise: `pipeline/requirements_reanalise.txt` (Python 3.14; scikit-learn 1.9.0 etc.). O README do
  pipeline tem a seção "Resultados da versão final da dissertação".

## 9. Commit (Portfolio)

Quando o orientador aprovar:

```
git add writing_latex/Tese pipeline/README.md pipeline/requirements_reanalise.txt \
        pipeline/model_training/gerar_apendice_a.py pipeline/model_in_practice/quaoar_reanalise.py
git add -f pipeline/model_in_practice/outputs_quaoar_1.2b pipeline/model_training/outputs/reanalise_banca
git commit -m "Rodada 3: Quaoar com a configuração 1.2b, estrangeirismos, fatos verificados (Chiron, VizieR, tempo)"
```

---

## Opcional (não bloqueia o depósito)

- **Qualidade dos dados:** 126 das 801 positivas (16%) têm fluxo normalizado improvável (máximo suavizado > 1,5 ou mínimo < −0,5). Registrado nas Limitações.
- **Duplicata:** `Euphrosyne_2018-02-01_BoninsegnaRoland` e `Euphrosyne_2018-02-01_RBoninsegna` são a mesma série. Sem vazamento (mesmo grupo).
- **Importação:** o programa de importação grava a observação antes de ler a curva (caso Chiron) e transforma em `Unknown` observadores com ponto ou hífen (11 curvas perdidas). Corrigir só depois do depósito, porque reimportar muda o conjunto de dados.
- **Datas do banco:** resolução mensal (dia "01"). Se corrigir, refaça o agrupamento por evento.
- **Repositório:** licença, *tag* da versão da tese e DOI pelo Zenodo (Flavia Cap6 iii).
