"""Adaptador único para os arquivos do experimento."""

import hashlib
import json
import shutil
from pathlib import Path
from typing import cast
from zipfile import ZipFile

import pandas as pd

from src.domain.contract import ContractError, JsonObject


class FileStore:
    """I/O relativo a uma raiz injetada; exemplo: `FileStore(Path('.')).read_json(...)`."""

    def __init__(self, root: Path) -> None:
        self.root = root.resolve()

    def destination(self, relative: str) -> Path:
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        return path

    def read_json(self, relative: str) -> JsonObject:
        contents = json.loads((self.root / relative).read_text(encoding="utf-8"))
        if not isinstance(contents, dict):
            raise ContractError(f"JSON {relative}; esperado objeto na raiz")
        return cast(JsonObject, contents)

    def write_json(self, relative: str, contents: JsonObject) -> None:
        encoded = json.dumps(contents, ensure_ascii=False, indent=2, allow_nan=False)
        self.destination(relative).write_text(encoded + "\n", encoding="utf-8")

    def read_parquet(self, relative: str) -> pd.DataFrame:
        return pd.read_parquet(self.root / relative, engine="pyarrow")

    def read_csv(self, relative: str) -> pd.DataFrame:
        return pd.read_csv(self.root / relative, dtype={"id_municipio": "string"})

    def write_parquet(self, relative: str, frame: pd.DataFrame) -> None:
        frame.to_parquet(self.destination(relative), index=False, compression="zstd")

    def write_csv(self, relative: str, frame: pd.DataFrame) -> None:
        frame.to_csv(self.destination(relative), index=False, encoding="utf-8-sig")

    def write_text(self, relative: str, text: str) -> None:
        self.destination(relative).write_text(text, encoding="utf-8")

    def read_archive_member(self, relative: str, suffix: str) -> bytes:
        with ZipFile(self.root / relative) as archive:
            names = [n for n in archive.namelist() if n.endswith(suffix)]
            if len(names) != 1:
                raise ContractError(
                    f"Membros {names} de {relative}; esperado exatamente um {suffix}"
                )
            return archive.read(names[0])

    def digest(self, relative: str) -> str:
        with (self.root / relative).open("rb") as stream:
            return hashlib.file_digest(stream, "sha256").hexdigest()

    def copy_verified(self, source: Path, relative: str, expected_hash: str) -> None:
        with source.open("rb") as stream:
            observed = hashlib.file_digest(stream, "sha256").hexdigest()
        if observed != expected_hash:
            raise ContractError(f"SHA-256 de {source.name}: {observed}; esperado {expected_hash}")
        target = self.destination(relative)
        if source.resolve() != target.resolve():
            shutil.copyfile(source, target)

    def load_development(self) -> pd.DataFrame:
        frame = self.read_parquet("data/gold/ml_aluno/ano=2023/alunos.parquet")
        if set(frame["ano"]) != {2023} or set(frame["particao"]) != {"desenvolvimento"}:
            raise ContractError("Partição de EDA/baseline inválida; esperado exclusivamente 2023")
        return frame
