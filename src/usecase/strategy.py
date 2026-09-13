"""Leitura estratégica das previsões congeladas e da Gold municipal da Fase 2."""

from typing import cast

from src.domain.contract import ContractError, JsonObject
from src.evaluation.territory import goal_scenarios, regional_patterns, territory_summary
from src.infrastructure.files import FileStore
from src.usecase.freeze import TEST_GOLD
from src.usecase.temporal import PREDICTIONS, TEMPORAL_REPORT


def run_strategy(store: FileStore) -> JsonObject:
    """Não ajusta nem escolhe modelos; exemplo: `run_strategy(store)`."""
    report = store.read_json(TEMPORAL_REPORT)
    if (
        store.digest(PREDICTIONS) != report["predictions_sha256"]
        or store.digest(TEST_GOLD) != report["test_gold_sha256"]
    ):
        raise ContractError("Previsões/Gold mudaram; esperado hashes do teste concluído")
    frame = store.read_parquet(TEST_GOLD)
    predictions = store.read_parquet(PREDICTIONS)
    keys = ["ano", "id_aluno", "id_municipio"]
    if not frame[keys].equals(predictions[keys]):
        raise ContractError("Chaves de teste divergentes; esperado correspondência exata")
    frame = frame.assign(p_risco=predictions["p_nao_alfabetizado"])
    municipalities = territory_summary(
        frame, ["id_municipio", "nome_municipio", "sigla_uf", "regiao"]
    )
    public = municipalities.loc[municipalities["avaliacoes"].ge(100)].sort_values(
        ["risco_medio", "avaliacoes"], ascending=False
    )
    store.write_csv("reports/municipios_risco_2024.csv", public)
    store.write_csv("reports/regioes_teste_2024.csv", territory_summary(frame, ["regiao"]))
    reference_path = "data/input/fase2/ml_features.parquet"
    manifest = store.read_json("config/snapshot.json")
    expected = next(
        e["sha256"]
        for e in cast(list[JsonObject], manifest["files"])
        if e["destination"] == "fase2/ml_features.parquet"
    )
    if store.digest(reference_path) != expected:
        raise ContractError("Gold Fase 2 divergente; esperado snapshot de referência")
    goals = goal_scenarios(public, store.read_parquet(reference_path))
    store.write_csv("reports/cenarios_metas_2024.csv", goals)
    development = store.load_development()
    profiles, pairs = regional_patterns(development)
    store.write_csv("reports/perfis_regionais_2023.csv", profiles)
    store.write_csv("reports/regioes_semelhantes_2023.csv", pairs)
    novelty = frame.assign(uf_inedita=~frame["sigla_uf"].isin(development["sigla_uf"].unique()))
    store.write_csv(
        "reports/novidade_ufs_2024.csv",
        novelty.groupby(["sigla_uf", "uf_inedita"])
        .agg(
            avaliacoes=("id_aluno", "size"),
            municipios=("id_municipio", "nunique"),
            risco_min=("p_risco", "min"),
            risco_max=("p_risco", "max"),
        )
        .reset_index(),
    )
    summary: JsonObject = {
        "municipalities_total": len(municipalities),
        "municipalities_public_min100": len(public),
        "minimum_evaluations_for_public_municipality": 100,
        "municipalities_with_2024_target": int(goals["meta_alfabetizacao"].notna().sum()),
        "conditional_below_reference_2024": int(goals["gap_referencia_meta_2024_pp"].lt(0).sum()),
        "conditional_below_80pct": int(goals["gap_cenario_80pct_pp"].lt(0).sum()),
        "unseen_state_students": int(novelty["uf_inedita"].sum()),
        "reference_gold_fase2_sha256": str(expected),
        "target_gap_is_probability": False,
        "future_year_forecast_performed": False,
    }
    store.write_json("reports/analise_territorial.json", summary)
    return summary
