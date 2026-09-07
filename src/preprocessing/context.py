"""Leitura das edições históricas do IBGE, sem incorporar revisões posteriores."""

import re
import xml.etree.ElementTree as ET

import pandas as pd

from src.domain.contract import ContractError

TABLE_NS = "urn:oasis:names:tc:opendocument:xmlns:table:1.0"


def parse_pib(payload: bytes) -> pd.DataFrame:
    """Aplica o layout de posições fixas do ZIP de 2020; exemplo: `parse_pib(txt_bytes)`."""
    lines = [line for line in payload.decode("latin-1").splitlines() if line[:4] == "2020"]
    records = [_pib_record(line) for line in lines]
    return pd.DataFrame.from_records(records).astype({"id_municipio": "string"})


def _pib_record(line: str) -> dict[str, str | float]:
    total = float(line[896:914])
    if total <= 0:
        raise ContractError(f"VAB total={total}, município={line[46:53]}; esperado positivo")
    return {
        "id_municipio": line[46:53].strip(),
        "sigla_uf_ibge": line[23:25].strip(),
        "pib_per_capita_2020": float(line[953:971]),
        "participacao_agropecuaria_2020": 100 * float(line[820:838]) / total,
        "participacao_servicos_publicos_2020": 100 * float(line[877:895]) / total,
    }


def parse_population(payload: bytes) -> pd.DataFrame:
    """Lê a aba Municípios do ODS original; exemplo: `parse_population(content_xml)`."""
    root = ET.fromstring(payload)
    tables = root.findall(f".//{{{TABLE_NS}}}table")
    municipality_table = next(t for t in tables if t.get(f"{{{TABLE_NS}}}name") == "Municípios")
    records = [_population_record(_row_cells(r)) for r in municipality_table]
    return pd.DataFrame.from_records([r for r in records if r]).astype({"id_municipio": "string"})


def _row_cells(row: ET.Element) -> list[str]:
    cells: list[str] = []
    for cell in row:
        repeats = int(cell.get(f"{{{TABLE_NS}}}number-columns-repeated", "1"))
        cells.extend(["".join(cell.itertext())] * min(repeats, 5 - len(cells)))
        if len(cells) >= 5:
            break
    return cells


def _population_record(cells: list[str]) -> dict[str, str | int]:
    if len(cells) < 5 or not re.fullmatch(r"\d{2}", cells[1]):
        return {}
    if not re.fullmatch(r"\d{5}", cells[2]):
        raise ContractError(f"Código municipal={cells[2]}; esperado cinco dígitos após UF")
    population = re.sub(r"\([^)]*\)", "", cells[4]).strip().replace(".", "")
    return {"id_municipio": cells[1] + cells[2], "populacao_2021": int(population)}


def combine_context(pib: pd.DataFrame, population: pd.DataFrame) -> pd.DataFrame:
    """Une contextos pelas chaves oficiais; exemplo: `combine_context(pib, population)`."""
    joined = pib.merge(population, on="id_municipio", how="outer", validate="one_to_one")
    if len(joined) != 5570 or joined.isna().any().any():
        raise ContractError(f"Contexto: {len(joined)} linhas; esperado 5570 sem nulos")
    if int(joined["populacao_2021"].sum()) != 213317639:
        raise ContractError("Soma populacional divergente; esperado 213317639 na edição original")
    return joined.sort_values("id_municipio").reset_index(drop=True)
