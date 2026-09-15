# Rotinas auxiliares da análise

**Autor: André Mohallem Ferraz**

Duas rotinas que consolidam artefatos citados pelo README a partir de resultados já
produzidos por `src.pipeline`. Nenhuma delas ajusta modelos, lê a Gold de 2024 ou altera
`config/modelo-final.json`.

## `gerar_eda_enriquecida.py`

Consolida a análise exploratória de 2023 com IBGE e Inep em `reports/eda_enriquecida_2023`,
nas formas `.md`, `.json` e nos CSV de cobertura, distribuições e correlações. Lê os
resultados do estudo educacional e as correlações municipais já versionadas.

## `gerar_linhagem.py`

Exporta `images/15_linhagem_gold.png` e `.svg`, o diagrama da origem das bases analíticas,
da Silver da Fase 2 até a Gold por aluno e o ramo educacional complementar.

## Ambiente

As duas usam matplotlib e pandas, já fixados em `pyproject.toml` e `uv.lock`:

```bash
uv run python tools/gerar_eda_enriquecida.py
uv run python tools/gerar_linhagem.py
```
