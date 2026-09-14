"""Leitura e download verificável das três fontes históricas do Inep."""

import argparse
import hashlib
import ssl
from dataclasses import dataclass
from datetime import date, datetime
from io import BytesIO
from pathlib import Path
from typing import cast
from urllib.parse import urlparse
from urllib.request import urlopen
from zipfile import ZipFile

import pandas as pd

from src.domain.contract import ContractError, JsonObject
from src.infrastructure.files import FileStore
from src.preprocessing.education import INDICATORS, combine_education_context, parse_education_xlsx


@dataclass(frozen=True)
class EducationSource:
    indicator: str
    relative: str
    url: str
    size: int
    sha256: str
    member: str
    member_size: int
    member_sha256: str


class EducationSources:
    """I/O injetado por FileStore; download explícito, leitura sempre verifica SHA-256."""

    def __init__(
        self, store: FileStore, manifest_relative: str = "config/fontes-educacionais.json"
    ) -> None:
        self.store = store
        manifest = store.read_json(manifest_relative)
        if manifest.get("ano_referencia") != 2021:
            raise ContractError("Manifesto educacional exige ano de referência 2021")
        sources = manifest.get("fontes")
        if not isinstance(sources, list) or len(sources) != 3:
            raise ContractError("Manifesto educacional exige exatamente três fontes")
        self.sources: list[EducationSource] = []
        for source in sources:
            if not isinstance(source, dict):
                raise ContractError("Fonte educacional deve ser um objeto")
            self.sources.append(self._source(cast(JsonObject, source)))
        if {source.indicator for source in self.sources} != set(INDICATORS):
            raise ContractError("Manifesto educacional deve conter ATU, DSU e HAD sem duplicatas")

    def _source(self, source: JsonObject) -> EducationSource:
        try:
            indicator = str(source["indicador"])
            url = str(source["url"])
            expected_url = (
                "https://download.inep.gov.br/informacoes_estatisticas/"
                f"indicadores_educacionais/2021/{indicator}_2021_MUNICIPIOS.zip"
            )
            relative = str(source["caminho"])
            publication = datetime.fromisoformat(str(source["publicado_em_pagina"]))
            if publication.date() > date(2022, 12, 31):
                raise ContractError("Publicação educacional posterior ao limite de 2022")
            if url != expected_url or urlparse(url).scheme != "https":
                raise ContractError("URL educacional deve apontar para a edição oficial de 2021")
            if relative != f"data/input/inep/{indicator}_2021_MUNICIPIOS.zip":
                raise ContractError("Destino de fonte Inep fora do caminho de entrada esperado")
            if source["variavel"] != INDICATORS[indicator][0]:
                raise ContractError("Variável educacional incompatível com seu indicador")
            return EducationSource(
                indicator,
                relative,
                url,
                int(str(source["bytes"])),
                str(source["sha256"]),
                str(source["membro"]),
                int(str(source["membro_bytes"])),
                str(source["membro_sha256"]),
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise ContractError(f"Manifesto educacional inválido: {exc}") from exc

    def _verified_payload(self, source: EducationSource) -> bytes:
        path = self.store.root / source.relative
        payload = path.read_bytes()
        self._verify(payload, source.size, source.sha256, source.relative)
        return payload

    @staticmethod
    def _verify(payload: bytes, size: int, sha256: str, label: str) -> None:
        if len(payload) != size or hashlib.sha256(payload).hexdigest() != sha256:
            raise ContractError(f"Tamanho/SHA-256 divergente na fonte educacional {label}")

    def load(self) -> pd.DataFrame:
        frames: dict[str, pd.DataFrame] = {}
        for source in self.sources:
            with ZipFile(BytesIO(self._verified_payload(source))) as archive:
                if archive.namelist().count(source.member) != 1:
                    raise ContractError(f"Membro XLSX ausente/duplicado em {source.relative}")
                payload = archive.read(source.member)
                self._verify(payload, source.member_size, source.member_sha256, source.member)
                frames[source.indicator] = parse_education_xlsx(payload, source.indicator)
        return combine_education_context(frames)

    def download(self, ca_file: Path | None = None) -> None:
        """Baixa apenas entradas ausentes; recusa mudanças de bytes e nunca sobrescreve."""
        context = ssl.create_default_context()
        if ca_file is not None:
            context.load_verify_locations(cafile=ca_file)
        for source in self.sources:
            path = self.store.root / source.relative
            if path.exists():
                self._verified_payload(source)
                continue
            with urlopen(source.url, context=context, timeout=60) as response:
                payload = response.read(source.size + 1)
            self._verify(payload, source.size, source.sha256, source.relative)
            target = self.store.destination(source.relative)
            with target.open("xb") as stream:
                stream.write(payload)


def load_education_context(
    store: FileStore, manifest_relative: str = "config/fontes-educacionais.json"
) -> pd.DataFrame:
    """Retorna município/rede e três atributos de 2021, sem ler resultados de alunos."""
    return EducationSources(store, manifest_relative).load()


def main() -> None:
    parser = argparse.ArgumentParser(description="Baixa e verifica indicadores Inep 2021")
    parser.add_argument("command", choices=["download", "inspect"])
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--ca-file", type=Path, help="Certificado intermediário adicional para TLS")
    args = parser.parse_args()
    sources = EducationSources(FileStore(args.root))
    if args.command == "download":
        sources.download(args.ca_file)
    frame = sources.load()
    print(f"Contexto educacional: {len(frame)} combinações município/rede")
    print(frame.isna().sum().to_string())


if __name__ == "__main__":
    main()
