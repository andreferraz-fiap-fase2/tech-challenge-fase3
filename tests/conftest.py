"""Cenários pequenos: dados reais, ausências e simulação identificada."""

import pandas as pd
import pytest


@pytest.fixture
def raw_students() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "ano": [2023] * 5,
            "id_aluno": ["a", "b", "c", "d", "e"],
            "id_escola": ["s1", "s2", "s1", "s2", "s1"],
            "id_municipio": ["1100015", "1100023", "1100015", "1100023", "1100015"],
            "serie": ["2"] * 5,
            "rede": ["3", "2", "3", "2", "4"],
            "presenca": ["1", "1", "0", "1", "1"],
            "alfabetizado": ["1", "0", "0", "0", "1"],
            "proficiencia": [750.0, 700.0, float("nan"), float("nan"), 800.0],
            "peso_aluno": [1.0, 2.0, float("nan"), float("nan"), 1.0],
        }
    )


@pytest.fixture
def silver_students(raw_students: pd.DataFrame) -> pd.DataFrame:
    silver = raw_students.rename(columns={"presenca": "presente"}).copy()
    silver["presente"] = silver["presente"].eq("1")
    silver["alfabetizado"] = silver["alfabetizado"].eq("1")
    silver["rede_nome"] = silver["rede"].map({"2": "Estadual", "3": "Municipal", "4": "Privada"})
    silver["origem"] = "batch"
    simulated = silver.iloc[[0]].assign(id_aluno="STREAM1", origem="streaming")
    return pd.concat([silver, simulated], ignore_index=True)


@pytest.fixture
def context_inputs() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    municipalities = pd.DataFrame(
        {
            "id_municipio": ["1100015", "1100023"],
            "nome_municipio": ["M1", "M2"],
            "sigla_uf": ["RO", "RO"],
        }
    )
    states = pd.DataFrame({"sigla_uf": ["RO"], "nome_uf": ["Rondônia"], "regiao": ["Norte"]})
    context = pd.DataFrame(
        {
            "id_municipio": ["1100015", "1100023"],
            "sigla_uf_ibge": ["RO", "RO"],
            "populacao_2021": [1000, 2000],
            "pib_per_capita_2020": [15000.0, 20000.0],
            "participacao_agropecuaria_2020": [0.0, 25.0],
            "participacao_servicos_publicos_2020": [30.0, 20.0],
        }
    )
    folds = pd.DataFrame({"id_municipio": ["1100015", "1100023"], "fold": [0, 1]})
    return context, municipalities, states, folds


@pytest.fixture
def development_students() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "ano": [2023] * 9,
            "id_aluno": list("abcdefghi"),
            "id_municipio": ["m0"] * 3 + ["m1"] * 3 + ["m2"] * 3,
            "id_escola": ["s0"] * 3 + ["s1"] * 3 + ["s2"] * 3,
            "fold_validacao": [0] * 3 + [1] * 3 + [2] * 3,
            "particao": ["desenvolvimento"] * 9,
            "alfabetizado": [1, 1, 0, 0, 0, 1, 1, 0, 1],
            "peso_aluno": [1.0] * 9,
            "rede_nome": ["Municipal"] * 9,
            "sigla_uf": ["RO"] * 9,
            "populacao_2021": [1000] * 9,
            "pib_per_capita_2020": [15000.0] * 9,
            "participacao_agropecuaria_2020": [10.0] * 9,
            "participacao_servicos_publicos_2020": [20.0] * 9,
        }
    )
