"""Regressões de parsing que alterariam a interpretação dos atributos."""

import pytest

from src.preprocessing.context import parse_pib, parse_population


def test_pib_layout_uses_vab_not_gdp_as_sector_denominator() -> None:
    line = [" "] * 1257
    fields = [
        (0, "2020"),
        (23, "RO"),
        (46, "1100015"),
        (820, "100"),
        (877, "200"),
        (896, "1000"),
        (934, "1200"),
        (953, "25000"),
    ]
    for start, value in fields:
        line[start : start + len(value)] = value
    result = parse_pib("".join(line).encode("latin-1"))
    assert result.iloc[0]["participacao_agropecuaria_2020"] == pytest.approx(10.0)
    assert result.iloc[0]["participacao_servicos_publicos_2020"] == pytest.approx(20.0)
    assert result.iloc[0]["pib_per_capita_2020"] == 25000.0


def test_population_footnotes_and_leading_zero_code() -> None:
    xml = b"""<root xmlns:t="urn:oasis:names:tc:opendocument:xmlns:table:1.0">
    <t:table t:name="Munic\xc3\xadpios"><t:table-row>
    <t:table-cell>RO</t:table-cell><t:table-cell>11</t:table-cell>
    <t:table-cell>00015</t:table-cell><t:table-cell>M</t:table-cell>
    <t:table-cell>22.516(1)</t:table-cell></t:table-row></t:table></root>"""
    result = parse_population(xml)
    assert result.iloc[0]["id_municipio"] == "1100015"
    assert result.iloc[0]["populacao_2021"] == 22516
