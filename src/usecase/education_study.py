"""Executa uma comparação educacional de 2023 em saída privada nova e externa."""

import argparse
import importlib.metadata
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter
from typing import cast

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from threadpoolctl import threadpool_limits

from src.domain.contract import ContractError, ExperimentContract, JsonObject, JsonValue
from src.domain.education_study import (
    METRICS,
    PROTOCOL_COMMIT,
    PROTOCOL_HASHES,
    VARIANTS,
    EducationVariant,
    study_features,
    validate_output_root,
    validate_study_definition,
)
from src.evaluation.education_study import (
    education_eda,
    join_education,
    paired_results,
    probability_scores,
    require_study_development,
)
from src.infrastructure.files import FileStore
from src.infrastructure.models import ModelStore
from src.modeling.education_study import EducationStudyModel
from src.preprocessing.validation import require_unique

GOLD = "data/gold/ml_aluno/ano=2023/alunos.parquet"
MANIFEST = "config/fontes-educacionais.json"


def verify_hashes(store: FileStore, expected: dict[str, str]) -> None:
    """Confere bytes; arquivos temporais são verificados por hash, sem carga analítica."""
    for relative, digest in expected.items():
        if store.digest(relative) != digest:
            raise ContractError(f"SHA-256 divergente: {relative}")


def study_fold(
    frame: pd.DataFrame, variant: EducationVariant, fold: int, models: ModelStore | None = None
) -> tuple[JsonObject, pd.Series]:
    """Ajusta dois folds municipais e prevê somente o terceiro."""
    require_study_development(frame)
    if fold not in (0, 1, 2):
        raise ContractError("Fold inválido; esperado 0, 1 ou 2")
    validation = frame["fold_validacao"].eq(fold)
    model = EducationStudyModel(variant)
    started = perf_counter()
    model.fit(frame.loc[~validation], frame.loc[~validation, "alfabetizado"])
    fitted = perf_counter()
    risk = model.predict_risk(frame.loc[validation])
    predicted = perf_counter()
    restored_verified = False
    if models is not None:
        path = f"artifacts/estudo_educacional/{variant}/fold_{fold}.joblib"
        models.save(path, model.pipeline)
        restored = models.load(path)
        sample = frame.loc[validation, list(study_features(variant))].iloc[:100]
        with threadpool_limits(limits=1):
            repeated = restored.predict_proba(sample)[:, list(restored.classes_).index(0)]
        if not np.array_equal(repeated, risk[: len(sample)]):
            raise ContractError("Pipeline persistida não reproduziu suas probabilidades")
        restored_verified = True
    return {
        "variant": variant,
        "fold": fold,
        "training_rows": int((~validation).sum()),
        "validation_rows": int(validation.sum()),
        "fit_seconds": fitted - started,
        "predict_seconds": predicted - fitted,
        "persisted_predictions_verified": restored_verified,
        **probability_scores(frame.loc[validation, "alfabetizado"], risk),
    }, pd.Series(risk, index=frame.index[validation])


def _plot_comparison(scores: pd.DataFrame, target: FileStore) -> None:
    figure, axes = plt.subplots(1, 2, figsize=(10.5, 4.2), layout="constrained")
    labels = {"ibge": "IBGE + rede/UF", "ibge_inep": "IBGE + rede/UF + Inep"}
    for axis, metric, title in zip(
        axes,
        ("average_precision_risk", "brier_risk"),
        ("AP de não alfabetização · maior é melhor", "Brier · menor é melhor"),
        strict=True,
    ):
        for variant, color in zip(VARIANTS, ("#65758b", "#147d79"), strict=True):
            rows = scores.loc[scores["variant"].eq(variant)].sort_values("fold")
            axis.plot(rows["fold"], rows[metric], marker="o", color=color, label=labels[variant])
        axis.set(title=title, xlabel="Fold municipal de validação", xticks=[0, 1, 2])
        axis.grid(axis="y", alpha=0.25)
        axis.legend(fontsize=8)
    figure.suptitle("Estudo exploratório · mesmos três folds de 2023", fontsize=13)
    for extension in ("png", "pdf"):
        figure.savefig(
            target.destination(f"images/15_estudo_educacional_2023.{extension}"), dpi=180
        )
    plt.close(figure)


def _markdown(summary: pd.DataFrame, delta: pd.DataFrame, coverage: pd.DataFrame) -> str:
    lines = [
        "# Estudo complementar — contexto educacional em 2023",
        "",
        "**Autor: André Mohallem Ferraz · Protocolo 1.0 exploratório**",
        "",
        "Comparação de seis atributos originais com nove atributos, acrescentando três",
        "indicadores educacionais históricos do Inep. Foram mantidos os mesmos alunos,",
        "três folds municipais e hiperparâmetros. Não houve busca, ajuste de calibração",
        "nem escolha de limiar. As medianas e categorias foram aprendidas apenas no treino.",
        "",
        "## Cobertura anterior ao ajuste",
        "",
        "| Atributo | Cobertura de alunos | Cobertura de contextos município × rede |",
        "| --- | ---: | ---: |",
    ]
    for row in coverage.to_dict("records"):
        lines.append(
            f"| {row['attribute']} | {100 * row['student_coverage']:.4f}% | "
            f"{100 * row['context_coverage']:.4f}% |"
        )
    lines.extend(
        [
            "",
            "A EDA registra uma observação por município × rede nas distribuições e",
            "correlações com a taxa observada de alfabetização. A cobertura estudantil",
            "é apresentada separadamente. Ausências residuais são imputadas no treino.",
            "",
            "## Validação cruzada exploratória",
            "",
            "| Variante | AP média ± desvio | ROC-AUC média ± desvio | Brier média ± desvio |",
            "| --- | ---: | ---: | ---: |",
        ]
    )
    for row in summary.to_dict("records"):
        values = [f"{row[name + '_mean']:.6f} ± {row[name + '_std']:.6f}" for name in METRICS]
        lines.append(f"| {row['variant']} | {' | '.join(values)} |")
    lines.extend(
        [
            "",
            "| Fold | Δ AP | Δ ROC-AUC | Δ Brier |",
            "| --- | ---: | ---: | ---: |",
        ]
    )
    for row in delta.to_dict("records"):
        values = [f"{row['delta_' + name]:+.6f}" for name in METRICS]
        lines.append(f"| {int(row['fold'])} | {' | '.join(values)} |")
    mean_ap = delta["delta_average_precision_risk"].mean()
    mean_brier = delta["delta_brier_risk"].mean()
    lines.extend(
        [
            "",
            f"A diferença média da expansão foi {mean_ap:+.6f} em AP e {mean_brier:+.6f}",
            "em Brier. As diferenças são calculadas como expansão menos referência;",
            "AP maior e Brier menor representam melhora nas respectivas métricas.",
            "O desvio é amostral entre três folds, não um intervalo de confiança.",
            "",
            "![Comparação por fold](../images/15_estudo_educacional_2023.png)",
            "",
            "## Limites e preservação da entrega",
            "",
            "**Significância estatística não foi demonstrada.** Correlações e diferenças",
            "preditivas não demonstram causalidade. O estudo utiliza dados de desenvolvimento",
            "já conhecidos e permanece sujeito às escolhas adaptativas do projeto.",
            "O teste de 2024 já havia sido observado no experimento 1.0 e não foi carregado",
            "para esta comparação. A integridade de artefatos existentes é conferida somente",
            "por hash. Não existe um novo teste independente nesta análise.",
            "",
            "A expansão não é promovida a modelo final. Permanecem válidos o modelo 1.0,",
            "seu limiar e sua avaliação temporal. Uma promoção exige novo protocolo e",
            "avaliação independente. A informação acrescentada é contextual por município",
            "e rede; não identifica características da escola ou trajetória de cada aluno.",
            "",
            "[Métricas por fold](estudo_educacional_folds_2023.csv) ·",
            "[Distribuições](estudo_educacional_distribuicoes_2023.csv) ·",
            "[Correlações descritivas](estudo_educacional_correlacoes_2023.csv) ·",
            "[Registro completo](estudo_educacional_2023.json).",
            "",
        ]
    )
    return "\n".join(lines)


def _frozen_hashes(source: FileStore, config: JsonObject) -> dict[str, str]:
    frozen = cast(
        dict[str, str],
        source.read_json("reports/revisao_documental_1.1.json")["frozen_files_verified"],
    ).copy()
    frozen.update(cast(dict[str, str], config["expected_sha256"]))
    frozen.update(PROTOCOL_HASHES)
    frozen["config/modelo-final.json"] = source.digest("config/modelo-final.json")
    return frozen


def _reference_predictions_identical(source: FileStore, predictions: pd.DataFrame) -> bool:
    original = source.read_parquet("artifacts/boosting_oof_2023.parquet")
    require_unique(original, ["ano", "id_aluno"], "OOF original")
    if len(original) != len(predictions) or set(original["ano"]) != {2023}:
        raise ContractError("OOF original divergente da população de 2023")
    index = pd.MultiIndex.from_frame(predictions[["ano", "id_aluno"]])
    aligned = original.set_index(["ano", "id_aluno"])["p_risco_completa"].reindex(index)
    if aligned.isna().any() or not np.array_equal(
        aligned.to_numpy(), predictions["p_risco_ibge"].to_numpy()
    ):
        raise ContractError("Referência de seis atributos não reproduziu o OOF congelado")
    return True


def run_education_study(source: FileStore, output_root: Path) -> JsonObject:
    """Escreve somente em diretório externo; exemplo: `run_education_study(source, target)`."""
    from src.infrastructure.education_sources import load_education_context

    output = validate_output_root(source.root, output_root)
    config = source.read_json("config/estudo-educacional.json")
    validate_study_definition(config)
    frozen = _frozen_hashes(source, config)
    verify_hashes(source, frozen)
    input_paths = [MANIFEST] + [
        str(path.relative_to(source.root))
        for path in sorted((source.root / "data/input/inep").rglob("*"))
        if path.is_file()
    ]
    inputs = {relative: source.digest(relative) for relative in input_paths}
    context = load_education_context(source, manifest_relative=MANIFEST)
    frame = source.load_development()
    if len(frame) != ExperimentContract().expected_rows(2023):
        raise ContractError("Número de alunos divergente do desenvolvimento congelado")
    require_study_development(frame, source.read_csv("config/folds-municipios-2023.csv"))
    enriched, coverage = join_education(frame, context)
    distribution, correlations = education_eda(enriched)
    verify_hashes(source, frozen | inputs)
    target = FileStore(validate_output_root(source.root, output))
    target.write_json("config/estudo-educacional.json", config)
    target.copy_verified(source.root / MANIFEST, MANIFEST, inputs[MANIFEST])
    target.write_parquet("data/gold/estudo_educacional/ano=2023/alunos.parquet", enriched)
    target.write_csv("reports/estudo_educacional_cobertura_2023.csv", coverage)
    target.write_csv("reports/estudo_educacional_distribuicoes_2023.csv", distribution)
    target.write_csv("reports/estudo_educacional_correlacoes_2023.csv", correlations)
    target.write_json(
        "reports/estudo_educacional_eda_2023.json",
        {
            "completed_at_utc": datetime.now(UTC).isoformat(),
            "before_model_fit": True,
            "year": 2023,
            "students": len(enriched),
            "contexts": len(enriched[["id_municipio", "rede_nome"]].drop_duplicates()),
            "distribution_unit": "município × rede, sem ponderação pelo número de alunos",
            "correlation": "Pearson contextual com taxa de alfabetização; associação não causal",
            "coverage_minimum_passed": True,
        },
    )
    predictions = enriched[
        ["ano", "id_aluno", "id_municipio", "fold_validacao", "alfabetizado"]
    ].copy()
    rows = []
    try:
        for variant in VARIANTS:
            parts = []
            for fold in (0, 1, 2):
                print(f"Ajustando {variant}, fold {fold}, exclusivamente 2023", flush=True)
                scores, risk = study_fold(enriched, variant, fold, ModelStore(target.root))
                rows.append(scores)
                parts.append(risk)
                print(
                    f"Concluído: AP={scores['average_precision_risk']:.6f}; "
                    f"Brier={scores['brier_risk']:.6f}",
                    flush=True,
                )
            predictions[f"p_risco_{variant}"] = pd.concat(parts).reindex(enriched.index)
        identical = _reference_predictions_identical(source, predictions)
    finally:
        verify_hashes(source, frozen | inputs)
    scores = pd.DataFrame(rows)
    summary, delta = paired_results(scores)
    target.write_parquet("artifacts/estudo_educacional_oof_2023.parquet", predictions)
    for suffix, table in (("folds", scores), ("resumo", summary), ("deltas", delta)):
        target.write_csv(f"reports/estudo_educacional_{suffix}_2023.csv", table)
    _plot_comparison(scores, target)
    target.write_text("reports/estudo_educacional_2023.md", _markdown(summary, delta, coverage))
    generated = {
        str(path.relative_to(target.root)): target.digest(str(path.relative_to(target.root)))
        for path in sorted(target.root.rglob("*"))
        if path.is_file()
    }
    report: JsonObject = {
        "author": "André Mohallem Ferraz",
        "version": "1.0-exploratorio",
        "completed_at_utc": datetime.now(UTC).isoformat(),
        "protocol_commit": PROTOCOL_COMMIT,
        "development_year": 2023,
        "students": len(enriched),
        "municipalities": int(enriched["id_municipio"].nunique()),
        "configuration": config,
        "new_independent_test": False,
        "test_2024_loaded_for_analysis": False,
        "existing_test_artifacts_checked_by_hash_only": True,
        "statistical_significance_demonstrated": False,
        "causal_interpretation": False,
        "final_model_promoted_or_modified": False,
        "original_six_feature_oof_reproduced_exactly": identical,
        "summary": cast(list[JsonValue], summary.to_dict("records")),
        "paired_deltas": cast(list[JsonValue], delta.to_dict("records")),
        "frozen_files_verified_before_and_after": cast(JsonObject, frozen),
        "input_sha256": cast(JsonObject, inputs),
        "generated_sha256": cast(JsonObject, generated),
        "dependencies": {
            name: importlib.metadata.version(name)
            for name in ("numpy", "pandas", "pyarrow", "scikit-learn", "openpyxl", "joblib")
        },
    }
    target.write_json("reports/estudo_educacional_2023.json", report)
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--output-root", type=Path, required=True)
    args = parser.parse_args()
    report = run_education_study(FileStore(args.root), args.output_root)
    print(
        f"Estudo concluído: {report['students']} alunos; seis pipelines; "
        "arquivos congelados preservados; sem novo teste independente.",
        flush=True,
    )


if __name__ == "__main__":
    main()
