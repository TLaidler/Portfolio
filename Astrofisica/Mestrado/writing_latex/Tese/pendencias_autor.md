# Pendências para o autor — em ordem, uma de cada vez

> **Situação em 21/10/2026.** Foi feito tudo o que podia ser feito sem você:
> - a reanálise completa pedida pela banca (`pipeline/model_training/reanalise_banca.py`), auditada por um agente verificador independente;
> - a renomeação dos experimentos;
> - a reescrita dos Caps. 5 e 6, do resumo e do Apêndice A;
> - as correções de Lillian e Flavia nos Caps. 1 a 4 e nos Apêndices B e C.
>
> Todas as mudanças estão marcadas em **`teseon_diff.pdf`**: vermelho é texto novo, riscado é texto antigo. Este arquivo lista o que ficou com você, na ordem em que recomendo fazer.
> Os itens mais antigos da Flavia continuam detalhados em [`pendencias_flavia.md`](pendencias_flavia.md); os textos prontos estão em [`correcoes_banca.md`](correcoes_banca.md).

---

## 1. Ler o PDF marcado com o orientador e aprovar a mudança de conclusão

**Arquivos:** há dois PDFs marcados.
- **`teseon_diff_rodada2.pdf`**: só o que mudou desde o último *commit* (`099daf2`). Use este se o orientador já leu a rodada da Flavia.
- **`teseon_diff.pdf`**: tudo o que mudou desde a versão apresentada à banca (`eca76fc`).

Nos dois:
- As tabelas reescritas aparecem inteiras na versão nova; as antigas, com os resultados substituídos, foram omitidas.
- Os "??" que aparecem **dentro do texto riscado** são referências a figuras e tabelas antigas que deixaram de existir. São esperados.

A reanálise mudou um resultado central.

- **O que mudou.** A configuração escolhida agora é a **1.2b (12 *features*, sem `kmeans_centroid_dist`)**, e não a de 11 *features*. Quando a comparação é feita por validação cruzada, retirar `Feature_Savgol_Min` piora o F1 em ~0,5 pp e dobra os falsos positivos nas negativas reais.
- **Ressalva já declarada no texto.** A regra de um desvio padrão escolhe a 1.2b por uma margem de 0,0009. Com outras sementes da validação cruzada, a mesma regra escolheria a configuração 2 (Cap. 5, §"Comparação das configurações", e Apêndice A). O texto mantém a 1.2b porque o ganho de `Feature_Savgol_Min` aparece em 18–19 das 25 dobras, em todos os modelos.
- **Decisão.** (a) manter assim (**recomendado**); ou (b) declarar empate e ficar com a configuração 2 por simplicidade. Na opção (b), me peça e eu refaço figuras, tabelas e texto.
- **Conferir também:**
  - a hipótese agora está "corroborada nos termos em que foi testada" (Cap. 6);
  - o resumo e o *abstract* foram reescritos com os números novos;
  - o "58/58 de baixo SNR" deixou de ser apresentado como evidência de robustez, porque essas curvas são quedas profundas com o ruído superestimado (Cap. 6).

## 2. Publicar o repositório `github.com/TLaidler/pipeline_occ_ml`

A tese agora cita esse endereço (Cap. 6, Contribuições; Apêndice C). Hoje o código está em `TLaidler/Portfolio` (`Astrofisica/Mestrado/pipeline`).

1. Criar o repositório e copiar a pasta `pipeline/` inteira, com `reanalise_banca.py` e o banco `data_warehouse/stellar_occultations.db` (11 MB, já versionado no Portfolio).
2. **Atenção: `*.csv` está no `.gitignore`.** Por isso não vão junto:
   - o `dataset_final.csv`, de que a reanálise precisa para rodar;
   - as tabelas em `outputs/reanalise_banca/`.

   Adicione esses arquivos com `git add -f <arquivo>` ou retire a regra do `.gitignore`.
3. As **702 curvas simuladas (`.dat`) não existem no disco nem no repositório**; há só os PNGs. As *features* delas estão no `dataset_final.csv`, o que basta para reproduzir a reanálise, mas não para regenerar o *dataset* do zero. Escolha uma opção:
   - regerar as `.dat` e versioná-las;
   - dizer no README que apenas as *features* das simuladas estão disponíveis.
4. Opcional: licença, *tag* da versão da tese e DOI pelo Zenodo (item Cap6 iii da Flavia).
5. Abrir o link no navegador para conferir.

## 3. Refazer o estudo de caso de Quaoar com os modelos da configuração 1.2b

Hoje a Seção 5.x usa os modelos antigos (configuração 2, `outputs/resultado5`) e o texto avisa isso ("Nota sobre os modelos utilizados"). Não pude refazer porque os `.dat` de Quaoar não estão no repositório.

1. Os modelos finais da 1.2b estão salvos em `pipeline/model_training/outputs/reanalise_banca/modelos/modelos_config_1.2b.joblib`. É um dicionário com `"features"` (a lista das 12) e `"modelos"` (os quatro *pipelines*, já com o *imputer*). Para carregar:
   ```python
   import joblib
   d = joblib.load("outputs/reanalise_banca/modelos/modelos_config_1.2b.joblib")
   p = d["modelos"]["XGBoost"].predict_proba(X[d["features"]])[:, 1]
   ```
2. Em `pipeline/model_in_practice/test_quaoar.py`, troque o carregamento de `resultado5` por esse arquivo.
3. Rode a curva inteira e os 6 recortes com os quatro modelos (a Flavia pediu RF e RL também).
4. Atualize no Cap. 5:
   - a Tab. `tab:quaoar_recortes`;
   - a figura `quaoar_recorte_tau_ajustado.png`;
   - os números do texto: 86×, 72×, 12×, 2× e τ = 0,03;
   - e apague a "Nota sobre os modelos utilizados".

   Se preferir, mande-me os números novos e eu atualizo o texto.
5. Opcional, mas valioso: uma **varredura cega**, com janelas de mesma duração percorrendo a curva inteira, para medir quantos alarmes falsos aparecem por janela.

## 4. Figuras que dependem de você

As figuras novas, geradas pelo *script*, já têm fonte grande e vírgula decimal. Ficam as figuras antigas e as de artigos:

1. Fonte maior e textos traduzidos nas figuras dos Caps. 2–4 e de Quaoar (Lillian; Flavia "Geral i").
2. Recortar a parte da legenda que sobra na Fig. 2.2(d) (Lillian).
3. Fig. 3.9: trocar por um exemplo astronômico ou traduzir (Flavia Cap3 24).
4. Fig. 5.5 de Quaoar: rótulos coerentes com a tabela (Flavia Cap5 8). Faça junto com o item 3.
5. Opcional: fundir as Figs. 2.3 e 2.4, marcando imersão e emersão (Flavia Cap2 mm).
6. Já resolvido, só conferir: a Flavia (Cap6 ii) pediu uma figura comparando baixo e alto SNR. O Cap. 6 agora remete à Fig. `fig:exemplos_curvas` (Cap. 4), painéis (a) e (b). Se o orientador achar suficiente, não é preciso fazer uma figura nova.

## 5. Confirmar fatos que só você sabe

Os textos prontos para cada item estão em `correcoes_banca.md`, e a tabela completa, em `pendencias_flavia.md`, seção 2.

| # | Onde | Pergunta |
|---|---|---|
| 1 | Cap. 1 | "~X anos": desde quando os dados vêm sendo coletados? (sugestão: desde o Gaia DR2, 2018) |
| 2 | Cap. 1 | "a bordo de telescópios": espaciais ou em solo? |
| 3 | Cap. 2 | Qual *release* do Gaia foi usada na previsão de Umbriel (DR2?) |
| 4 | Cap. 2, Fig. 2.4b | As linhas verdes tracejadas são cordas negativas? |
| 5 | Cap. 2 | O texto que contextualiza o "Grupo do Rio" (escrito agora) está correto? |
| 6 | Cap. 3 | Qual teorema "conjecturado com ML" você tinha em mente? (Davies et al. 2021?) |
| 7 | Cap. 4 | Número de curvas baixadas do VizieR, licença do catálogo e **data de acesso** no `\bibitem{HeraldBocc2016}` (exigência da ABNT) |
| 8 | Cap. 4 | O que eram as "curvas defeituosas" descartadas? |
| 9 | Cap. 4 | Alinhamento temporal: as 18 cordas de Umbriel estavam em dias julianos, e isso foi corrigido na reanálise. Houve alguma checagem manual antes? |
| 10 | Cap. 4 | Os fóruns citados são da IOTA? |
| 11 | Cap. 4 | **Chiron:** a observação está no banco, mas sem nenhum ponto de curva (o texto agora diz que ela não entrou no conjunto). A importação falhou? **Não reimporte antes do depósito**: isso mudaria o *dataset* e exigiria rodar tudo de novo. |
| 12 | Cap. 6 | "coleta de dados" significa novas curvas rotuladas (proposta da Flavia, Cap6 iv)? |

## 6. Decisões de estilo com o orientador

Todas estão listadas em `pendencias_flavia.md`, seção 3:
- política de estrangeirismos (*overfitting* → sobreajuste? "Machine Learning" no título?);
- "curva de luz de ocultação" por extenso;
- lista de siglas;
- notação opcional;
- motivação de Centauros e TNOs;
- VP/VN × TP/TN;
- *features* × características;
- fusão das subseções 4.4.2 e 4.4.3.

## 7. Elementos pré-textuais (`teseon.tex`, linhas 60–78)

- Nomes e instituições da **banca** (`\examiner{...}{Nome Sobrenome}{Instituicao}`, hoje com espaços reservados).
- **CDU** (`\cducode{000.000.000}`) e código *cutter*, fornecidos pela biblioteca.

## 8. Compilar no Overleaf e conferir

1. Suba a pasta nova **`Tese/pngs/reanalise/`** (10 figuras).
2. Compile com pdfLaTeX.
3. Confira os pontos que só você pode decidir. A compilação local (tectonic, motor XeTeX) passou sem erros e sem referências indefinidas, e as tabelas do Apêndice A cabem na página.
   - Se as figuras novas têm tamanho adequado. A matriz de correlação (Fig. 5.1) tem rótulos pequenos; se incomodar, vale passá-la para uma página inteira.
   - Se a Fig. 2.4(b) continua boa: ela invadia a margem em ~1 cm desde a versão da banca e agora ocupa a largura da sua coluna (`width=\linewidth` no lugar de `scale=0.28`).
   - A lista da seção 5 de `pendencias_flavia.md`.
   - Ajustes de composição que fiz no preâmbulo e no texto:
     - `\emergencystretch` (linhas com nomes longos em `\texttt` invadindo a margem);
     - `\belowcaptionskip` (legendas de tabela encostadas no filete);
     - `\sectionmark` curto na Seção 4.4 (cabeçalho de página longo demais);
     - travessões e acentos que sumiam no PDF (`---`, `Cali\'nski`, `\text{início}`).
4. Os arquivos `teseon_diff*.tex` e `teseon_diff*.pdf` já estão atualizados. Se você mudar o texto depois disso, há duas opções para gerar de novo o PDF marcado: me pedir, ou rodar `latexdiff --flatten --type=UNDERLINE <teseon.tex de eca76fc> teseon.tex > teseon_diff.tex`. O `latexdiff` vem com o TeX Live e o MiKTeX; a versão antiga pode ser extraída com `git worktree add ../tese_antiga eca76fc`.

## 9. Commit

Nada desta rodada foi commitado. Quando o orientador aprovar:

```
git add writing_latex/Tese pipeline/model_training/reanalise_banca.py pipeline/model_training/gerar_apendice_a.py
git add -f pipeline/model_training/outputs/reanalise_banca   # os .csv estão no .gitignore
git commit -m "Reanálise pós-banca: validação cruzada agrupada, teste reservado, Caps. 5 e 6 reescritos"
```

---

## Opcional (não bloqueia o depósito)

- **Qualidade dos dados:** 126 das 801 positivas (16%) têm fluxo normalizado improvável (máximo suavizado > 1,5 ou mínimo < −0,5). O fato está registrado nas Limitações. Investigar essas curvas é trabalho futuro.
- **Duplicata:** `Euphrosyne_2018-02-01_BoninsegnaRoland` e `Euphrosyne_2018-02-01_RBoninsegna` são a mesma série. Não há vazamento, porque caem no mesmo grupo, mas vale remover do banco no futuro.
- **Datas do banco:** todas as datas têm dia "01" (resolução mensal). Se for corrigir no futuro, refaça o agrupamento por evento.
