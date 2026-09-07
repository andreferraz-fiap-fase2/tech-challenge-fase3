"""Narrativa gerada diretamente das métricas e da comparação pareada."""

import pandas as pd

from src.evaluation.logistic import enrichment_deltas


def logistic_markdown(comparison: pd.DataFrame) -> str:
    """Descreve ganho e limites sem escolher o modelo final; exemplo: `logistic_markdown(table)`."""
    labels = {
        "dummy_prior": "Baseline constante",
        "rede_uf": "Logística: rede/UF",
        "completa": "Logística: seis atributos",
    }
    means = comparison.groupby("model").mean(numeric_only=True).reindex(labels)
    rows = [
        f"| {label} | {means.loc[model, 'average_precision_risk']:.4f} | {means.loc[model, 'roc_auc_risk']:.4f} | {means.loc[model, 'brier_risk']:.4f} | {means.loc[model, 'recall_risk']:.2%} | {means.loc[model, 'precision_risk']:.2%} |"
        for model, label in labels.items()
    ]
    deltas = enrichment_deltas(comparison)
    paired = "\n".join(
        f"| {int(r.fold)} | {r.delta_average_precision_risk:+.6f} | {r.delta_roc_auc_risk:+.6f} | {r.delta_brier_risk:+.6f} |"
        for r in deltas.itertuples()
    )
    delta_ap = deltas["delta_average_precision_risk"].mean()
    return _report_body("\n".join(rows), paired, delta_ap)


def _report_body(rows: str, paired: str, delta_ap: float) -> str:
    return f"""# Regressão Logística — comparação no desenvolvimento de 2023

Foram treinadas duas variantes nos mesmos três folds por município e nas
1.502.809 avaliações de 2023: rede/UF e todos os seis preditores. Os parâmetros
foram fixados antes da execução: L2, C=1, solver lbfgs, tolerância 1e-6 e máximo
de 1.000 iterações. Não houve busca de parâmetros, ponderação do ajuste ou balanceamento de classes.

Cada fold contém uma pipeline independente: padronização das representações de ausência,
imputação categórica constante, one-hot com categoria desconhecida ignorada, mediana
numérica no treino, log1p de população/PIB e StandardScaler nas quatro numéricas.
Nenhuma transformação aprende com o fold de validação. Colunas inteiramente ausentes
no treino são mantidas (fallback numérico zero); esse caso não ocorreu no snapshot real.

## Resultados

Médias simples dos três folds; classe positiva de avaliação = não alfabetizado.
Recall e precisão usam limiar de risco 0,5, sem otimização.

| Modelo | Average precision | ROC-AUC | Brier ↓ | Recall | Precisão |
| --- | ---: | ---: | ---: | ---: | ---: |
{rows}

![Comparação nos folds](../images/05_comparacao_logistica_2023.png)

## Contribuição do enriquecimento

Diferença **seis atributos menos rede/UF**, calculada em cada fold:

| Fold | Delta AP | Delta ROC-AUC | Delta Brier |
| --- | ---: | ---: | ---: |
{paired}

Delta médio de AP: **{delta_ap:+.6f}**, ou **{delta_ap * 100:+.3f} pontos percentuais**.
Esse resultado mede a contribuição dos quatro atributos numéricos dentro deste modelo
linear e deste protocolo. Não mede um efeito causal nem comprova significância estatística.
O desvio entre três folds não é um intervalo de confiança.

## Interpretação inicial

Os coeficientes foram exportados por variante/fold. Para ler risco de não alfabetização,
o sinal é o inverso do coeficiente do alvo alfabetizado. Nas numéricas, a unidade é
um desvio-padrão da variável após a transformação do respectivo treino. Nos indicadores
categóricos, a comparação entre duas categorias usa a diferença dos coeficientes;
não comparar sua magnitude diretamente com a das numéricas como ranking de importância.

![Coeficientes numéricos](../images/06_coeficientes_numericos_2023.png)

Uma associação ajustada pode ter sinal diferente de uma correlação descritiva por
causa dos outros atributos incluídos e das dependências entre eles. PIB per capita
não é renda familiar; a participação dos serviços públicos no VAB não é gasto educacional.
Os 5.881 perfis de entrada continuam limitando a diferenciação individual.

## Artefatos e limites desta rodada

- `logistica_development.json`: configurações, fontes congeladas, convergência,
  iterações, tempos e métricas ponderadas/não ponderadas por fold.
- `logistica_comparacao_2023.csv` e `logistica_delta_enriquecimento_2023.csv`: comparação pareada.
- `logistica_coeficientes_2023.csv`: coeficientes completos; intercepto identificado separadamente.
- `artifacts/logistica/`: seis pipelines serializadas, uma por variante/fold, para auditoria.
- `artifacts/logistica_oof_2023.parquet`: previsões de validação para cada aluno de 2023.

**Não houve ajuste final em todo 2023 nem avaliação de 2024.** Os artefatos são modelos
de validação. Calibração, escolha de limiar e interpretação final ainda dependem da
comparação com Gradient Boosting e da seleção usando somente desenvolvimento.
As métricas suplementares ponderadas não demonstram representatividade nacional.

Próximo experimento: Gradient Boosting com busca limitada em 2023, mantendo os folds
e a avaliação temporal reservada.
"""
