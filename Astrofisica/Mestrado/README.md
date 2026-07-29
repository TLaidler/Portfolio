# Mestrado — Detecção automática de ocultações estelares com ML

**Dissertação (Observatório Nacional):** *Pipeline para Detecção Automatizada de
Ocultações Estelares em Curvas de Luz com Técnicas de Machine Learning.*

## O problema

Uma ocultação estelar dura segundos e vale ouro: os anéis de Quaoar, por exemplo,
foram descobertos numa *revisita* de dados antigos. Milhares de curvas de luz dormem
em arquivos esperando um olho humano. Este pipeline faz a triagem automaticamente —
transforma ruído de milhares de curvas em uma lista priorizada para o astrônomo.

## Resultados principais

- **F1 ≈ 0,98–0,99** (RF/XGBoost/CatBoost) em teste — sempre reportado **junto com o
  baseline trivial** (um limiar em `Occ_depth` já faz F1 0,90; o ML corta o erro ~10×).
- **Validação adversarial em dado real:** aplicado à curva de Quaoar (Gemini/Alopeke),
  o modelo separa o anel real de um recorte de ruído que imita ocultação por **~86×**
  na probabilidade, recuperando os dois anéis sem falso positivo.
- **[AUDITORIA_PIPELINE.md](./AUDITORIA_PIPELINE.md)** — auditoria crítica do meu
  próprio pipeline (10 achados, com arquivo e linha), escrita antes de qualquer revisor.

## Estrutura

| Pasta | Conteúdo |
|---|---|
| [`pipeline/`](./pipeline/) | Código completo: geração de sintéticas, extração de features (com "motivação física" em cada docstring), treino e aplicação ([README](./pipeline/README.md)) |
| [`writing_latex/`](./writing_latex/) | Fonte LaTeX da dissertação |
| [`slides/`](./slides/) | Slides da defesa |
