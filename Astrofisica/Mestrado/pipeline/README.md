# Detecção de Ocultações Estelares usando Machine Learning

## Sobre o Projeto

Este repositório contém o código e recursos desenvolvidos durante meu projeto de mestrado em Astronomia, focado na detecção automática de ocultações estelares usando técnicas de machine learning.

### O que são Ocultações Estelares?

Ocultações estelares são eventos astronômicos onde um objeto do Sistema Solar (como um asteroide) passa na frente de uma estrela, bloqueando temporariamente sua luz. Estes eventos são extremamente valiosos cientificamente, pois permitem:
- Determinar o tamanho e forma precisa dos objetos
- Detectar possíveis atmosferas ou anéis
- Refinar as órbitas dos objetos observados
- Descobrir sistemas binários

## Configuração

### Reprodutibilidade
- **Instalação:** `pip install -r requirements.txt`
- **Ambiente exato:** `pip install -r requirements_frozen.txt` (ou `pip freeze > requirements_frozen.txt` para regenerar)
- **Seeds:** Os scripts fixam `RANDOM_STATE=42` para numpy, random e modelos sklearn

### Resultados da versão final da dissertação (reanálise pós-banca)

Os números e figuras do Capítulo 5 e do Apêndice A da versão final vêm de dois programas, que usam um ambiente
próprio (Python 3.14):

```bash
pip install -r requirements_reanalise.txt

cd model_training
python reanalise_banca.py      # ~5 min; validação cruzada agrupada, teste reservado, limiares, McNemar
python gerar_apendice_a.py     # reescreve ../../writing_latex/Tese/apendice_experimentos.tex a partir do resumo.json

cd ../model_in_practice
python quaoar_reanalise.py     # estudo de caso de Quaoar com os modelos finais (configuração 1.2b)
```

| Entrada / saída | Caminho |
|---|---|
| Conjunto de dados (1693 curvas, 28 características) | `model_training/outputs/resultado1_split0.8-0.2_all-features/dataset_final.csv` |
| Banco de curvas de luz | `data_warehouse/stellar_occultations.db` |
| Curvas simuladas (702 arquivos `.dat`) | `model_training/synthetic_curve/output/` |
| Tabelas e resumo da reanálise | `model_training/outputs/reanalise_banca/` (`resumo.json`, `cv_*.csv`, `teste_final.csv`, ...) |
| Modelos finais (12 características) | `model_training/outputs/reanalise_banca/modelos/modelos_config_1.2b.joblib` |
| Resultados de Quaoar | `model_in_practice/outputs_quaoar_1.2b/` |
| Figuras do Cap. 5 | `../writing_latex/Tese/pngs/reanalise/` (criada pelos programas) |

O arquivo `model_training/outputs/dataset_final.csv` contém os mesmos dados com os nomes antigos das colunas
observacionais (prefixo `IOTA_`, depois renomeado para `Occ_`); a reanálise usa a cópia em `resultado1_...`.
Os modelos finais podem ser usados diretamente:

```python
import joblib
d = joblib.load("model_training/outputs/reanalise_banca/modelos/modelos_config_1.2b.joblib")
p = d["modelos"]["XGBoost"].predict_proba(X[d["features"]])[:, 1]   # cada modelo já inclui o imputador
```

## Estrutura do Repositório

### 📁 data_warehouse/
Contém scripts e ferramentas para coleta, limpeza e armazenamento de curvas de luz provenientes de bases de dados públicas de ocultações. As principais fontes incluem:
- DAMIT (Database of Asteroid Models from Inversion Techniques)
- ALCDEF (Asteroid Lightcurve Database)

Os dados são organizados em um banco SQLite local, mantendo informações sobre o objeto observado, data da observação, portal de origem e metadados adicionais.

### 📁 model_training/
Scripts para extração de características e treinamento dos modelos de machine learning. Cada curva de luz é tratada independentemente, e um conjunto de features descritivas é computado. Implementações incluem:
- Random Forest
- XGBoost
- CatBoost
- Regressão Logística

#### Métricas observacionais de ocultação
O módulo `model_training/occ_features.py` calcula métricas observacionais **apenas a partir das séries de tempo e fluxo** (ou fluxo normalizado) de cada curva, sem alterar a ingestão de dados nem o pré-processamento existente. O dataset final (`outputs/dataset_final.csv`) passa a incluir as novas colunas, utilizadas automaticamente no treino junto com as demais features.

**Features observacionais (documentadas em `occ_features.py`):**
- **Occ_depth** — profundidade do dip (baseline − flux_min)
- **Occ_SNR_dip** — signal-to-noise ratio da queda (depth / baseline_std)
- **Occ_duration_s** — duração da queda em segundos (maior run abaixo do baseline)
- **Occ_n_frames_below_baseline** — maior número de frames consecutivos abaixo do baseline
- **Occ_baseline_std** — desvio padrão do baseline (pontos fora do dip)
- **Occ_flux_min** — fluxo mínimo observado
- **Occ_flux_min_over_baseline** — razão flux_min / baseline
- **Occ_chi2_constant** — χ² do modelo constante (sem evento)
- **Occ_chi2_square_well** — χ² do modelo “square well” (poço retangular)
- **Occ_chi2_ratio** — razão chi2_constant/chi2_square_well (> 1 indica que o dip explica melhor os dados)

A pipeline de construção do dataset (leitura do banco, recorte, curvas sintéticas e extração de features originais) permanece inalterada; as features observacionais são incorporadas após cada chamada a `extract_features` e o resultado é salvo no mesmo CSV para treino.

### 📁 model_in_practice/
Código para aplicação dos modelos treinados em dados observacionais reais ou não vistos durante o treinamento. Inclui ferramentas para:
- Pré-processamento de novas curvas de luz
- Aplicação do modelo treinado
- Avaliação e validação dos resultados

### 📁 drafts/
Notebooks e scripts exploratórios, incluindo:
- Simulações de curvas de luz sintéticas
- Notas sobre desenvolvimento dos modelos
- Planejamento e documentação do processo

## Geração de Dados Sintéticos

Para aumentar o conjunto de treinamento, desenvolvemos um pipeline de geração de curvas de luz sintéticas que simula:
- Diferentes geometrias de ocultação
- Variações de SNR (Signal-to-Noise Ratio)
- Diversos perfis de queda de luz
- Efeitos de difração (quando relevantes)

## Objetivos Futuros

- 🎯 Disponibilização pública da base de dados de curvas de luz
- 🎯 Generalização do modelo para diferentes tipos de ocultações
- 🎯 Implementação de interface web para uso da comunidade
- 🎯 Integração com pipelines existentes de redução de dados
- 🎯 Publicação dos resultados em revista especializada

## Contribuições

Contribuições são bem-vindas! Por favor, sinta-se à vontade para abrir issues ou pull requests.

## Contato
📧  thiagolaidler@gmail.com

📧  thiagocunha@on.br