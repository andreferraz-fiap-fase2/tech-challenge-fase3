"""Leitura restrita dos artefatos congelados e dos contextos públicos da Gold 2023."""

import hashlib
import io
import json
from pathlib import Path
from typing import cast

import joblib
import pandas as pd
from sklearn.pipeline import Pipeline

from src.domain.contract import ContractError, ExperimentContract, JsonObject
from src.domain.prediction_demo import ProfileRequest

DEMO_GOLD = "data/gold/ml_aluno/ano=2023/alunos.parquet"
DEMO_DECISION = "config/modelo-final.json"
DEMO_MODEL = "artifacts/modelo_final.joblib"
DEMO_CONTRACT = "config/contrato-ml-aluno.json"
FROZEN_DIGESTS = {
    DEMO_GOLD: "a9bfd5749fbbf5cb52b2d3be34650f7021230139286ab95ed51accd127628241",
    DEMO_DECISION: "4458d9b2ed8c3d8fed0f4dca2f8604c661793dc58b9c8a7a860f31b05ae7df33",
    DEMO_MODEL: "af9c0953a472ef63edc8bae850c88a39c1814c881b87c53b15f6b37c57733331",
    DEMO_CONTRACT: "7af52859f26a330fa3a3b0cc7c24dc91c2c0a60861737556ed3fde21e1ff5496",
}
CONTEXT_COLUMNS = ("id_municipio", "nome_municipio", *ExperimentContract().features)


class FrozenProfileStore:
    """Concentra I/O; não aceita modelos externos ou arquivos individuais como entrada."""

    def __init__(self, root: Path) -> None:
        self.root = root.resolve()

    def _verified_bytes(self, relative: str) -> bytes:
        payload = (self.root / relative).read_bytes()
        if hashlib.sha256(payload).hexdigest() != FROZEN_DIGESTS[relative]:
            raise ContractError(f"SHA-256 divergente em {relative}; esperado artefato final 1.0")
        return payload

    def load_decision(self) -> JsonObject:
        contract = cast(JsonObject, json.loads(self._verified_bytes(DEMO_CONTRACT)))
        ExperimentContract().validate_definition(contract)
        return cast(JsonObject, json.loads(self._verified_bytes(DEMO_DECISION)))

    def load_pipeline(self) -> Pipeline:
        # Desserializar os mesmos bytes verificados evita troca entre a checagem e a leitura.
        pipeline = joblib.load(io.BytesIO(self._verified_bytes(DEMO_MODEL)))
        if not isinstance(pipeline, Pipeline):
            raise ContractError("Artefato inválido; esperado sklearn Pipeline completo")
        return pipeline

    def load_contexts(self, requests: list[ProfileRequest]) -> pd.DataFrame:
        with (self.root / DEMO_GOLD).open("rb") as stream:
            if hashlib.file_digest(stream, "sha256").hexdigest() != FROZEN_DIGESTS[DEMO_GOLD]:
                raise ContractError("SHA-256 divergente na Gold; esperado desenvolvimento de 2023")
            stream.seek(0)
            return pd.read_parquet(
                stream,
                engine="pyarrow",
                columns=list(CONTEXT_COLUMNS),
                filters=[("id_municipio", "in", [r.municipality for r in requests])],
            ).drop_duplicates()

    def read_requests(self, path: Path) -> list[ProfileRequest]:
        frame = pd.read_csv(path, dtype="string", encoding="utf-8-sig", keep_default_na=False)
        if list(frame.columns) != ["id_municipio", "rede_nome"]:
            raise ContractError("CSV deve conter apenas as colunas id_municipio,rede_nome")
        return [
            ProfileRequest(str(row.id_municipio), str(row.rede_nome)) for row in frame.itertuples()
        ]

    def write_result(self, path: Path, result: JsonObject) -> None:
        encoded = json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
        with path.open("x", encoding="utf-8") as stream:
            stream.write(encoded)
