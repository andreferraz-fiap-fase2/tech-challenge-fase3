"""Validação interna do baseline, sem ler a partição de 2024."""

from typing import cast

import numpy as np
import pandas as pd
from numpy.typing import NDArray

from src.domain.contract import ExperimentContract, JsonObject, JsonValue
from src.evaluation.development import require_development
from src.evaluation.metrics import risk_metrics
from src.evaluation.summary import summarize_folds
from src.infrastructure.files import FileStore
from src.modeling.baseline import PriorBaseline
from src.preprocessing.gold import select_predictors


def evaluate_baseline(
    frame: pd.DataFrame, contract: ExperimentContract
) -> tuple[JsonObject, pd.DataFrame]:
    """Gera previsões fora de fold; exemplo: `evaluate_baseline(development, contract)`."""
    require_development(frame)
    predictors = select_predictors(frame, contract)
    predictions = frame[["ano", "id_aluno", "id_municipio", "fold_validacao"]].copy()
    predictions["p_nao_alfabetizado"] = np.nan
    results: list[JsonValue] = []
    for fold in (0, 1, 2):
        validation = frame["fold_validacao"].eq(fold)
        risk = PriorBaseline().fit_predict(
            predictors.loc[~validation],
            frame.loc[~validation, "alfabetizado"],
            predictors.loc[validation],
        )
        predictions.loc[validation, "p_nao_alfabetizado"] = risk
        results.append(_fold_metrics(frame.loc[validation], risk, fold, int((~validation).sum())))
    report: JsonObject = {
        "model": "DummyClassifier(strategy=prior)",
        "development_year": 2023,
        "threshold_risk": 0.5,
        "test_2024_evaluated": False,
        "folds": results,
        "summary": summarize_folds(results),
    }
    return report, predictions


def _fold_metrics(
    frame: pd.DataFrame, risk: NDArray[np.float64], fold: int, training_rows: int
) -> JsonObject:
    labels = frame["alfabetizado"].to_numpy(dtype=np.int8)
    weights = frame["peso_aluno"].to_numpy(dtype=float)
    return {
        "fold": fold,
        "training_rows": training_rows,
        "validation_rows": len(frame),
        "training_risk_prior": float(risk[0]),
        "unweighted": risk_metrics(labels, risk),
        "weighted_evaluation_only": risk_metrics(labels, risk, weights),
    }


def run_baseline(store: FileStore) -> JsonObject:
    """A única leitura analítica é 2023; exemplo: `run_baseline(store)`."""
    contract = ExperimentContract()
    contract.validate_definition(store.read_json("config/contrato-ml-aluno.json"))
    frame = store.load_development()
    report, predictions = evaluate_baseline(frame, contract)
    store.write_json("reports/baseline_development.json", report)
    store.write_parquet("artifacts/dummy_prior_oof_2023.parquet", predictions)
    store.write_text("reports/baseline_development.md", baseline_markdown(report))
    return report


def baseline_markdown(report: JsonObject) -> str:
    """Explica o referencial sem confundir acurácia com utilidade; exemplo: `baseline_markdown(report)`."""
    metrics = cast(JsonObject, cast(JsonObject, report["summary"])["unweighted"])
    auc = cast(JsonObject, metrics["roc_auc_risk"])["mean"]
    ap = float(cast(JsonObject, metrics["average_precision_risk"])["mean"])
    accuracy = float(cast(JsonObject, metrics["accuracy"])["mean"])
    recall = float(cast(JsonObject, metrics["recall_risk"])["mean"])
    return f"""# Primeiro baseline — desenvolvimento de 2023

DummyClassifier com a frequência das classes **dos municípios de treino de cada fold**.
Validação em três folds por município; pesos não usados no ajuste. Resultados principais
são médias das métricas de cada fold, com igual peso entre folds.

| Métrica, classe de risco = não alfabetizado | Média nos folds |
| --- | ---: |
| ROC-AUC | {auc:.4f} |
| Average precision | {ap:.4f} |
| Acurácia no limiar 0,5 | {accuracy:.2%} |
| Recall de não alfabetizado no limiar 0,5 | {recall:.2%} |

O baseline não distingue alunos: atribui a todos os casos de validação a mesma
probabilidade aprendida no respectivo treino. A average precision acompanha a
prevalência da classe de risco. A acurácia reflete a classe majoritária e, isoladamente,
não comprova utilidade para detectar não alfabetização.

O JSON contém métricas por fold, desvio entre folds, Brier, matriz de confusão e uma
visão de avaliação ponderada por peso_aluno, cuja representatividade requer discussão
da fonte. Não agregar probabilidades constantes diferentes dos folds em uma única
ROC-AUC para comparar os modelos: isso introduz um efeito da partição. Comparar as
métricas por fold sob o mesmo protocolo.

**2024 permanece reservado, sem avaliação de modelo.** Não foi escolhido um modelo
final nem ajustado um limiar operacional nesta etapa. Próxima comparação: Regressão
Logística com rede/UF e com os seis atributos, seguida de Gradient Boosting.
"""
