"""Garantias da demonstração: contexto conhecido, orientação do risco e integridade."""

import hashlib
from pathlib import Path
from typing import cast

import numpy as np
import pandas as pd
import pytest
from sklearn.pipeline import Pipeline

from src.domain.contract import ContractError, ExperimentContract, JsonObject
from src.domain.prediction_demo import ProfileRequest, probability_decision
from src.infrastructure.profile_store import (
    CONTEXT_COLUMNS,
    DEMO_GOLD,
    DEMO_MODEL,
    FROZEN_DIGESTS,
    FrozenProfileStore,
)
from src.usecase.predict_profiles import main, predict_profiles


class ReversedClassPipeline:
    """A coluna zero é alfabetização; selecionar por posição fixa inverteria a resposta."""

    feature_names_in_ = np.array(ExperimentContract().features)
    classes_ = np.array([1, 0])

    def predict_proba(self, frame: pd.DataFrame) -> np.ndarray:
        assert tuple(frame.columns) == ExperimentContract().features
        return np.tile([0.8, 0.2], (len(frame), 1))


class MemoryProfiles:
    def __init__(self, contexts: pd.DataFrame) -> None:
        self.contexts = contexts
        self.model_loads = 0

    def load_decision(self) -> JsonObject:
        return {"features": list(ExperimentContract().features), "risk_threshold": 0.15}

    def load_pipeline(self) -> Pipeline:
        self.model_loads += 1
        return cast(Pipeline, ReversedClassPipeline())

    def load_contexts(self, requests: list[ProfileRequest]) -> pd.DataFrame:
        return self.contexts.copy()


@pytest.fixture
def public_context() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "id_municipio": "3106200",
                "nome_municipio": "Belo Horizonte",
                "rede_nome": "Municipal",
                "sigla_uf": "MG",
                "populacao_2021": 2530701,
                "pib_per_capita_2020": 38670.4,
                "participacao_agropecuaria_2020": 0.0036318973,
                "participacao_servicos_publicos_2020": 14.3661208237,
            }
        ]
    )


@pytest.mark.parametrize(
    ("municipality", "network"),
    [("310620", "Municipal"), ("31.06200", "Municipal"), ("3106200", "Federal")],
)
def test_request_rejects_invalid_code_or_network(municipality: str, network: str) -> None:
    with pytest.raises(ContractError):
        ProfileRequest(municipality, network)


def test_probability_orientation_and_policy_are_explicit(public_context: pd.DataFrame) -> None:
    result = predict_profiles(
        MemoryProfiles(public_context), [ProfileRequest("3106200", "Municipal")]
    )
    prediction = cast(list[JsonObject], result["previsoes"])[0]
    assert prediction["p_alfabetizado"] == 0.8
    assert prediction["p_nao_alfabetizado"] == 0.2
    assert cast(JsonObject, prediction["decisao_f2"])["classificacao"] == "não alfabetizado"
    assert cast(JsonObject, prediction["referencia_0_5"])["classificacao"] == "alfabetizado"
    assert result["modelo_versao"] == "1.0"


@pytest.mark.parametrize("risk", [float("nan"), -0.1, 1.01])
def test_invalid_probability_is_not_published(risk: float) -> None:
    with pytest.raises(ContractError, match="Probabilidade"):
        probability_decision(risk, 0.15)


def test_threshold_tie_is_flagged() -> None:
    result = probability_decision(0.15, 0.15)
    assert cast(JsonObject, result["decisao_f2"])["sinalizado_para_atencao"] is True


@pytest.mark.parametrize("kind", ["missing", "ambiguous", "label", "null"])
def test_invalid_context_is_rejected_before_model_load(
    public_context: pd.DataFrame, kind: str
) -> None:
    if kind == "missing":
        public_context["rede_nome"] = "Estadual"
    elif kind == "ambiguous":
        public_context = pd.concat(
            [public_context, public_context.assign(pib_per_capita_2020=1)], ignore_index=True
        )
    elif kind == "label":
        public_context["alfabetizado"] = 1
    else:
        public_context["pib_per_capita_2020"] = np.nan
    store = MemoryProfiles(public_context)
    with pytest.raises(ContractError):
        predict_profiles(store, [ProfileRequest("3106200", "Municipal")])
    assert store.model_loads == 0


def test_repeated_requests_are_not_silently_duplicated(public_context: pd.DataFrame) -> None:
    request = ProfileRequest("3106200", "Municipal")
    with pytest.raises(ContractError, match="repetido"):
        predict_profiles(MemoryProfiles(public_context), [request, request])


def test_model_hash_is_checked_before_deserialization(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / DEMO_MODEL
    path.parent.mkdir(parents=True)
    path.write_bytes(b"untrusted pickle")

    def fail_deserialization(*args: object, **kwargs: object) -> None:
        pytest.fail("Conteúdo com SHA-256 divergente não pode chegar ao joblib.load")

    monkeypatch.setattr("src.infrastructure.profile_store.joblib.load", fail_deserialization)
    with pytest.raises(ContractError, match="SHA-256"):
        FrozenProfileStore(tmp_path).load_pipeline()


def test_gold_reader_projects_only_public_columns(
    tmp_path: Path, public_context: pd.DataFrame, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / DEMO_GOLD
    path.parent.mkdir(parents=True)
    public_context.assign(id_aluno="privado", alfabetizado=1, proficiencia=800).to_parquet(path)
    monkeypatch.setitem(FROZEN_DIGESTS, DEMO_GOLD, hashlib.sha256(path.read_bytes()).hexdigest())
    result = FrozenProfileStore(tmp_path).load_contexts([ProfileRequest("3106200", "Municipal")])
    assert tuple(result.columns) == CONTEXT_COLUMNS
    assert len(result) == 1


def test_csv_cannot_supply_extra_predictors(tmp_path: Path) -> None:
    path = tmp_path / "input.csv"
    path.write_text("id_municipio,rede_nome,alfabetizado\n3106200,Municipal,1\n", encoding="utf-8")
    with pytest.raises(ContractError, match="apenas as colunas"):
        FrozenProfileStore(tmp_path).read_requests(path)


def test_output_is_never_overwritten(tmp_path: Path) -> None:
    path = tmp_path / "result.json"
    path.write_text("original", encoding="utf-8")
    with pytest.raises(FileExistsError):
        FrozenProfileStore(tmp_path).write_result(path, {"new": True})
    assert path.read_text(encoding="utf-8") == "original"


def test_cli_checks_existing_output_before_reading_private_files(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    output = tmp_path / "result.json"
    output.write_text("original", encoding="utf-8")
    monkeypatch.setattr(
        "sys.argv",
        [
            "predict_profiles",
            "--root",
            str(tmp_path),
            "--municipio",
            "3106200",
            "--rede",
            "Municipal",
            "--output",
            str(output),
        ],
    )
    with pytest.raises(SystemExit) as error:
        main()
    assert error.value.code == 2
    assert output.read_text(encoding="utf-8") == "original"
