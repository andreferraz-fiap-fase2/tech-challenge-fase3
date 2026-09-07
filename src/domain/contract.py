"""Contrato imutável do experimento; não depende de bibliotecas analíticas."""

from dataclasses import dataclass
from typing import cast

type JsonValue = str | int | float | bool | None | list[JsonValue] | dict[str, JsonValue]
type JsonObject = dict[str, JsonValue]

CATEGORICAL = ("rede_nome", "sigla_uf")
NUMERIC = (
    "populacao_2021",
    "pib_per_capita_2020",
    "participacao_agropecuaria_2020",
    "participacao_servicos_publicos_2020",
)


class ContractError(ValueError):
    """Entrada incompatível com a definição congelada do experimento."""


@dataclass(frozen=True)
class ExperimentContract:
    """Papéis de colunas e anos; exemplo: `ExperimentContract().features`."""

    categorical: tuple[str, ...] = CATEGORICAL
    numeric: tuple[str, ...] = NUMERIC
    development_year: int = 2023
    test_year: int = 2024

    @property
    def features(self) -> tuple[str, ...]:
        return self.categorical + self.numeric

    def validate_definition(self, definition: JsonObject) -> None:
        selected = cast(JsonObject, definition["features"])
        actual = tuple(cast(list[str], selected["categorical"])) + tuple(
            cast(list[str], selected["numeric"])
        )
        if actual != self.features:
            raise ContractError(f"Preditores {actual}; esperado {self.features}")
        validation = cast(JsonObject, definition["validation"])
        actual_years = (validation["development_year"], validation["test_year"])
        if actual_years != (self.development_year, self.test_year):
            raise ContractError(
                f"Partições {actual_years}; esperado desenvolvimento=2023, teste=2024"
            )

    def expected_rows(self, year: int) -> int:
        counts = {2023: 1502809, 2024: 1851828}
        if year not in counts:
            raise ContractError(f"Ano {year}; esperado um de {tuple(counts)}")
        return counts[year]
