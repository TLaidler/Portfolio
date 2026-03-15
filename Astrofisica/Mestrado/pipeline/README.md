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

## Estrutura do Repositório

### 📁 data_warehouse/
Contém scripts e ferramentas para coleta, limpeza e armazenamento de curvas de luz provenientes de bases de dados públicas de ocultações. As principais fontes incluem:
- IOTA (International Occultation Timing Association)
- DAMIT (Database of Asteroid Models from Inversion Techniques)
- ALCDEF (Asteroid Lightcurve Database)

Os dados são organizados em um banco SQLite local, mantendo informações sobre o objeto observado, data da observação, portal de origem e metadados adicionais.

### 📁 model_training/
Scripts para extração de características e treinamento dos modelos de machine learning. Cada curva de luz é tratada independentemente, e um conjunto de features descritivas é computado. Implementações incluem:
- Random Forest
- XGBoost
- CatBoost
- Regressão Logística

#### Etapa de feature engineering IOTA
Foi adicionada uma etapa modular de feature engineering inspirada nos critérios observacionais da **International Occultation Timing Association (IOTA)** para validação de eventos. O módulo `model_training/iota_features.py` calcula as métricas **apenas a partir das séries de tempo e fluxo** (ou fluxo normalizado) de cada curva, sem alterar a ingestão de dados nem o pré-processamento existente. O dataset final (`outputs/dataset_final.csv`) passa a incluir as novas colunas, utilizadas automaticamente no treino junto com as demais features.

**Novas features (documentadas em `iota_features.py`):**
- **IOTA_depth** — profundidade do dip (baseline − flux_min)
- **IOTA_SNR_dip** — signal-to-noise ratio da queda (depth / baseline_std)
- **IOTA_duration_s** — duração da queda em segundos (maior run abaixo do baseline)
- **IOTA_n_frames_below_baseline** — maior número de frames consecutivos abaixo do baseline
- **IOTA_baseline_std** — desvio padrão do baseline (pontos fora do dip)
- **IOTA_flux_min** — fluxo mínimo observado
- **IOTA_flux_min_over_baseline** — razão flux_min / baseline
- **IOTA_chi2_constant** — χ² do modelo constante (sem evento)
- **IOTA_chi2_square_well** — χ² do modelo “square well” (poço retangular)
- **IOTA_chi2_ratio** — razão chi2_constant/chi2_square_well (> 1 indica que o dip explica melhor os dados)

A pipeline de construção do dataset (leitura do banco, recorte, curvas sintéticas e extração de features originais) permanece inalterada; as features IOTA são incorporadas após cada chamada a `extract_features` e o resultado é salvo no mesmo CSV para treino.

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