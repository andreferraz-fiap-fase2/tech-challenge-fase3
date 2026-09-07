"""Persistência de pipelines produzidas pelo próprio experimento."""

from pathlib import Path

import joblib
from sklearn.pipeline import Pipeline

from src.domain.contract import ContractError


class ModelStore:
    """Salva e relê artefatos locais confiáveis; exemplo: `ModelStore(root).save(path, pipeline)`."""

    def __init__(self, root: Path) -> None:
        self.root = root

    def save(self, relative: str, pipeline: Pipeline) -> None:
        target = self.root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(pipeline, target, compress=3)

    def load(self, relative: str) -> Pipeline:
        pipeline = joblib.load(self.root / relative)
        if not isinstance(pipeline, Pipeline):
            raise ContractError(f"Artefato={type(pipeline)}; esperado sklearn Pipeline")
        return pipeline
