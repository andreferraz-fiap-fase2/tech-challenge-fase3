"""Produz a EDA inicial de 2023, preservando 2024 para avaliação posterior."""

import pandas as pd

from src.domain.contract import ExperimentContract, JsonObject
from src.evaluation.development import eda_overview, group_summary, numeric_summary
from src.infrastructure.files import FileStore
from src.visualization.plots import ReportPlots


def run_eda(store: FileStore) -> JsonObject:
    """Salva tabelas e figuras do desenvolvimento; exemplo: `run_eda(store)`."""
    contract = ExperimentContract()
    contract.validate_definition(store.read_json("config/contrato-ml-aluno.json"))
    frame = store.load_development()
    overview = eda_overview(frame, contract)
    summaries = {
        name: group_summary(frame, name)
        for name in ("regiao", "sigla_uf", "rede_nome", "fold_validacao")
    }
    for name, table in summaries.items():
        store.write_csv(f"reports/eda_{name}_2023.csv", table)
    store.write_csv("reports/eda_numericas_municipios_2023.csv", numeric_summary(frame, contract))
    store.write_json("reports/eda_development.json", overview)
    store.write_text("reports/eda_development.md", eda_markdown(overview, summaries["regiao"]))
    _export_plots(store, frame, summaries)
    return overview


def _export_plots(
    store: FileStore, frame: pd.DataFrame, summaries: dict[str, pd.DataFrame]
) -> None:
    plots = ReportPlots(store.root / "images")
    plots.target(frame)
    plots.regions(summaries["regiao"])
    plots.numeric(frame)
    plots.folds(summaries["fold_validacao"])


def eda_markdown(overview: JsonObject, regions: pd.DataFrame) -> str:
    """Relaciona achados e decisões; exemplo: `eda_markdown(overview, regions)`."""
    lowest = regions.loc[regions["taxa_nao_alfabetizado_pct"].idxmin()]
    highest = regions.loc[regions["taxa_nao_alfabetizado_pct"].idxmax()]
    return f"""# EDA inicial — desenvolvimento de 2023

População: **{overview["rows"]:,} avaliações reais elegíveis**, em
**{overview["municipalities"]:,} municípios**, após excluir a simulação de streaming,
ausentes, avaliações sem proficiência válida e redes fora do escopo.

- Não alfabetizados: **{overview["non_literate"]:,}**, ou **{overview["non_literate_pct"]:.2f}%**,
  sem ponderação. As classes são desiguais, mas a classe de risco tem volume expressivo;
  não há justificativa inicial para aplicar geração artificial de exemplos.
- O recorte regional vai de **{lowest["taxa_nao_alfabetizado_pct"]:.2f}%** de não alfabetização
  em **{lowest["regiao"]}** até **{highest["taxa_nao_alfabetizado_pct"]:.2f}%** em **{highest["regiao"]}**.
  Isso motiva reportar métricas por território; não demonstra causalidade nem representa
  uma classificação definitiva de todas as crianças de cada região.
- Os seis atributos estão completos no snapshot. A futura pipeline ainda deverá conter
  imputação para operar de forma definida diante de ausências em outras cargas, ajustada
  exclusivamente no treino de cada fold.
- Há **{overview["distinct_feature_profiles"]:,} combinações distintas dos seis preditores**,
  frente a {overview["rows"]:,} avaliações. O modelo inicial estima risco contextual;
  não diferencia alunos com atributos idênticos e não acompanha a mesma criança entre anos.
- As distribuições econômicas usam **uma linha por município**, evitando que municípios
  mais populosos apareçam repetidos milhares de vezes no mesmo histograma. Os gráficos
  de população e PIB usam escala logarítmica para tornar as diferenças de porte legíveis.

## Figuras

![Distribuição do alvo](../images/01_alvo_2023.png)

![Diferenças regionais](../images/02_regioes_2023.png)

![Distribuições do contexto municipal](../images/03_contexto_municipal_2023.png)

![Composição dos folds](../images/04_folds_2023.png)

## Como interpretar

As tabelas por região, UF, rede e fold trazem volumes e taxas não ponderadas, além de
uma visão ponderada por peso_aluno. Esses pesos não foram usados como preditores;
sua interpretação e a cobertura territorial deverão ser discutidas antes de inferir
representatividade populacional. Esta EDA não mede poder preditivo ou efeito de políticas.

**A partição de 2024 não foi lida pelos comandos de EDA ou baseline.** Ela foi somente
materializada e validada durante a construção da Gold. O próximo experimento comparará
modelos no desenvolvimento sob os folds já definidos.
"""
