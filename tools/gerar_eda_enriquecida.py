"""Consolida a EDA enriquecida de 2023, sem ajustar modelos ou ler dados de 2024."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import tempfile
from datetime import UTC, datetime
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

AUTHOR = "André Mohallem Ferraz"
GOLD = "data/gold/estudo_educacional/ano=2023/alunos.parquet"
GOLD_SHA256 = "7c0fef1ec483853a13719a7068adbe05b1a5982f97ea72cfee2882efba83d19b"
IBGE = (
    "populacao_2021",
    "pib_per_capita_2020",
    "participacao_agropecuaria_2020",
    "participacao_servicos_publicos_2020",
)
INEP = ("alunos_por_turma_ai_2021", "docentes_superior_ai_2021", "horas_aula_ai_2021")
LABELS = {
    "populacao_2021": "População",
    "pib_per_capita_2020": "PIB per capita",
    "participacao_agropecuaria_2020": "Agropecuária / VAB",
    "participacao_servicos_publicos_2020": "Serviços públicos / VAB",
    "alunos_por_turma_ai_2021": "Alunos por turma",
    "docentes_superior_ai_2021": "Funções docentes com curso superior",
    "horas_aula_ai_2021": "Horas de aula por dia",
}
UNITS = {
    INEP[0]: "Média de alunos por turma",
    INEP[1]: "Funções docentes (%)",
    INEP[2]: "Média diária de horas",
}
REPORT = "reports/eda_enriquecida_2023"
EXPECTED_COUNTS = {"students": 1502809, "municipalities": 4871, "contexts": 5881}


def digest(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def read_verified(path: Path, expected: str) -> None:
    if digest(path) != expected:
        raise ValueError(f"SHA-256 divergente: {path.name}")


def load_contexts(study: Path) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, int]]:
    """Lê exclusivamente a Gold de 2023; mantém separados os dois grãos contextuais."""
    read_verified(study / GOLD, GOLD_SHA256)
    columns = ["ano", "id_aluno", "id_municipio", "rede_nome", "alfabetizado", *IBGE, *INEP]
    frame = pd.read_parquet(study / GOLD, columns=columns)
    if set(frame["ano"]) != {2023} or frame[["ano", "id_aluno"]].duplicated().any():
        raise ValueError("Esperado exclusivamente 2023, sem duplicidade aluno × ano")
    if frame["alfabetizado"].isna().any() or set(frame["alfabetizado"]) != {0, 1}:
        raise ValueError("Alvo inválido; esperado alfabetizado completo em 0/1")
    if not set(frame["rede_nome"]).issubset({"Estadual", "Municipal"}):
        raise ValueError("Rede fora da população do estudo")
    if np.isinf(frame[[*IBGE, *INEP]].to_numpy(dtype=float)).any():
        raise ValueError("Preditor infinito; esperado número finito ou ausência")
    by_context = frame.groupby(["id_municipio", "rede_nome"], observed=True, sort=True)
    if by_context[[*IBGE, *INEP]].nunique(dropna=False).gt(1).any().any():
        raise ValueError("Atributo variável dentro de um mesmo contexto município × rede")
    by_municipality = frame.groupby("id_municipio", observed=True, sort=True)
    if by_municipality[list(IBGE)].nunique(dropna=False).gt(1).any().any():
        raise ValueError("Atributo IBGE variável dentro do mesmo município")
    context = by_context.agg(
        **{name: (name, "first") for name in (*IBGE, *INEP)},
        literacy_rate=("alfabetizado", "mean"),
        students=("alfabetizado", "size"),
    ).reset_index()
    municipal = by_municipality.agg(
        **{name: (name, "first") for name in IBGE},
        literacy_rate=("alfabetizado", "mean"),
        students=("alfabetizado", "size"),
    ).reset_index()
    counts = {
        "students": len(frame),
        "municipalities": len(municipal),
        "contexts": len(context),
    }
    if counts != EXPECTED_COUNTS:
        raise ValueError(f"População divergente: {counts}; esperado {EXPECTED_COUNTS}")
    return context, municipal, counts


def summarize(
    context: pd.DataFrame, municipal: pd.DataFrame
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Usa contexto como observação; nenhuma ausência é imputada na descrição."""
    distribution = context[list(INEP)].describe().T
    distribution["missing"] = context[list(INEP)].isna().sum()
    distribution = distribution.reset_index(names="attribute")
    coverage = []
    associations = []
    for names, frame, method, unit in (
        (IBGE, municipal, "spearman", "município"),
        (INEP, context, "pearson", "município × rede"),
    ):
        for name in names:
            paired = frame[[name, "literacy_rate"]].dropna()
            associations.append(
                {
                    "attribute": name,
                    "method": method,
                    "observation_unit": unit,
                    "complete_contexts": len(paired),
                    "target": "taxa observada de alfabetização",
                    "correlation_literacy": paired[name].corr(
                        paired["literacy_rate"], method=method
                    ),
                }
            )
    for name in INEP:
        known = context[name].notna()
        coverage.append(
            {
                "attribute": name,
                "student_rows": int(context["students"].sum()),
                "student_nonmissing": int(context.loc[known, "students"].sum()),
                "student_coverage": float(
                    context.loc[known, "students"].sum() / context["students"].sum()
                ),
                "context_rows": len(context),
                "context_nonmissing": int(known.sum()),
                "context_coverage": float(known.mean()),
            }
        )
    matrix = municipal[list(IBGE)].corr(method="spearman")
    return distribution, pd.DataFrame(coverage), pd.DataFrame(associations), matrix


def verify_existing_tables(
    project: Path,
    study: Path,
    distribution: pd.DataFrame,
    coverage: pd.DataFrame,
    associations: pd.DataFrame,
    matrix: pd.DataFrame,
) -> dict[str, str]:
    """Confronta a nova agregação com as tabelas históricas e inverte o alvo do IBGE."""
    record = json.loads((study / "reports/estudo_educacional_2023.json").read_text())
    paths = {}
    for suffix, observed in (("distribuicoes", distribution), ("cobertura", coverage)):
        relative = f"reports/estudo_educacional_{suffix}_2023.csv"
        read_verified(study / relative, record["generated_sha256"][relative])
        expected = pd.read_csv(study / relative)
        pd.testing.assert_frame_equal(observed, expected, check_dtype=False, rtol=1e-12, atol=1e-12)
        paths[f"study:{relative}"] = digest(study / relative)
    relative = "reports/estudo_educacional_correlacoes_2023.csv"
    read_verified(study / relative, record["generated_sha256"][relative])
    expected = pd.read_csv(study / relative).set_index("attribute")
    observed = associations.set_index("attribute")
    np.testing.assert_allclose(
        observed.loc[list(INEP), "correlation_literacy"], expected["pearson_literacy"], atol=1e-12
    )
    np.testing.assert_array_equal(
        observed.loc[list(INEP), "complete_contexts"], expected["complete_contexts"]
    )
    paths[f"study:{relative}"] = digest(study / relative)
    relative = "reports/correlacoes_municipais_2023.csv"
    original = pd.read_csv(project / relative, index_col="feature")
    np.testing.assert_allclose(
        observed.loc[list(IBGE), "correlation_literacy"],
        -original.loc[list(IBGE), "risco_observado"],
        atol=1e-12,
    )
    np.testing.assert_allclose(matrix, original.loc[list(IBGE), list(IBGE)], atol=1e-12)
    paths[f"project:{relative}"] = digest(project / relative)
    paths[f"study:{GOLD}"] = GOLD_SHA256
    for relative in (
        "reports/estudo_educacional_2023.json",
        "reports/estudo_educacional_eda_2023.json",
    ):
        paths[f"study:{relative}"] = digest(study / relative)
    return paths


def save_figure(figure: plt.Figure, destination: Path, name: str) -> None:
    """PNG e SVG determinísticos, com autoria explícita e texto vetorial legível."""
    folder = destination / "images"
    folder.mkdir(parents=True, exist_ok=True)
    figure.savefig(folder / f"{name}.png", dpi=200, metadata={"Author": AUTHOR})
    figure.savefig(
        folder / f"{name}.svg", metadata={"Creator": AUTHOR, "Date": None, "Title": name}
    )
    plt.close(figure)


def plot_distributions(context: pd.DataFrame, destination: Path) -> None:
    colors = ("#187f8a", "#607d42", "#a76a29")
    figure, axes = plt.subplots(1, 3, figsize=(13.8, 5.4))
    for axis, name, color in zip(axes, INEP, colors, strict=True):
        values = context[name].dropna()
        axis.hist(values, bins=25, color=color, edgecolor="white", linewidth=0.5)
        median = float(values.median())
        axis.axvline(median, color="#24364b", linestyle="--", linewidth=1.4)
        title = LABELS[name].replace("Funções docentes com", "Funções docentes\ncom")
        axis.set_title(title, fontsize=12, pad=13)
        axis.set_xlabel(UNITS[name], labelpad=10)
        axis.set_ylabel("Número de contextos")
        axis.grid(axis="y", alpha=0.2)
        axis.set_axisbelow(True)
        median_text = f"{median:.1f}".replace(".", ",")
        axis.text(
            0.03 if name == INEP[1] else 0.98,
            0.96,
            f"Mediana: {median_text}\nVálidos: {len(values):,}\nAusentes: {context[name].isna().sum()}".replace(
                f"{len(values):,}", f"{len(values):,}".replace(",", ".")
            ),
            transform=axis.transAxes,
            ha="left" if name == INEP[1] else "right",
            va="top",
            fontsize=10,
            bbox={"facecolor": "white", "edgecolor": "#d7dee6", "alpha": 0.94, "pad": 6},
        )
    figure.suptitle("Distribuições dos três indicadores educacionais do Inep", fontsize=17, y=0.98)
    figure.text(
        0.5,
        0.89,
        "Dados de 2021 associados ao desenvolvimento de 2023 · 5.881 contextos município × rede",
        ha="center",
        fontsize=11,
        color="#435368",
    )
    figure.text(
        0.5,
        0.025,
        "Cada contexto contribui uma vez; ausências excluídas de cada histograma. Anos iniciais, localização Total.\n"
        "Consolidação descritiva posterior: a EDA original do Inep precedeu os ajustes do estudo complementar.",
        ha="center",
        fontsize=9,
        color="#435368",
    )
    figure.subplots_adjust(top=0.77, bottom=0.22, left=0.055, right=0.99, wspace=0.30)
    save_figure(figure, destination, "16_eda_inep_2023")


def plot_associations(associations: pd.DataFrame, redundancy: float, destination: Path) -> None:
    figure, axes = plt.subplots(1, 2, figsize=(13.8, 6.2))
    for axis, names, color, title in zip(
        axes,
        (IBGE, INEP),
        ("#60758d", "#187f8a"),
        (
            "IBGE · Spearman\nUma observação por município",
            "Inep · Pearson\nUma observação por município × rede",
        ),
        strict=True,
    ):
        rows = associations.set_index("attribute").loc[list(names)]
        values = rows["correlation_literacy"].to_numpy()
        positions = np.arange(len(names))
        axis.barh(positions, values, height=0.56, color=color)
        axis.axvline(0, color="#24364b", linewidth=0.9)
        axis.set_yticks(
            positions,
            [
                LABELS[name].replace("Funções docentes com", "Funções docentes\ncom")
                for name in names
            ],
            fontsize=10,
        )
        axis.invert_yaxis()
        axis.set_xlim(-1, 1)
        axis.set_xticks([-1, -0.5, 0, 0.5, 1])
        axis.set_title(title, fontsize=12, pad=14)
        axis.set_xlabel("Correlação com a taxa de alfabetização", labelpad=10)
        axis.grid(axis="x", alpha=0.18)
        axis.set_axisbelow(True)
        for position, value in zip(positions, values, strict=True):
            axis.text(
                value + (0.035 if value >= 0 else -0.035),
                position,
                f"{value:+.3f}".replace(".", ","),
                ha="left" if value >= 0 else "right",
                va="center",
                fontsize=10,
            )
    figure.suptitle("Associações contextuais com a alfabetização em 2023", fontsize=17, y=0.97)
    figure.text(
        0.5,
        0.87,
        "IBGE: 4.871 municípios · Inep: 5.871 / 5.872 / 5.871 pares completos, na ordem apresentada",
        ha="center",
        fontsize=10,
        color="#435368",
    )
    figure.text(
        0.5,
        0.045,
        "Os dois painéis usam alfabetização como alvo; os sinais do IBGE foram invertidos em relação ao risco original.\n"
        "Métodos e unidades de observação diferem. Associação não é impacto causal nem importância do modelo.\n"
        f"Redundância entre atributos municipais: Spearman(PIB per capita, serviços públicos / VAB) = {redundancy:+.3f}.".replace(
            f"{redundancy:+.3f}", f"{redundancy:+.3f}".replace(".", ",")
        ),
        ha="center",
        fontsize=9,
        color="#435368",
    )
    figure.subplots_adjust(top=0.74, bottom=0.24, left=0.16, right=0.985, wspace=0.94)
    save_figure(figure, destination, "17_correlacoes_contextuais_2023")


def markdown(distribution: pd.DataFrame, associations: pd.DataFrame, redundancy: float) -> str:
    rows = distribution.set_index("attribute")
    medians = {name: f"{rows.loc[name, '50%']:.1f}".replace(".", ",") for name in INEP}
    redundancy_text = f"{redundancy:.6f}".replace(".", ",")
    return f"""# EDA consolidada — base enriquecida de 2023

**Autor: {AUTHOR} · Consolidação descritiva posterior aos experimentos**

## População, enriquecimento e unidades

São os mesmos **1.502.809 alunos avaliados**, em **4.871 municípios** e **5.881 contextos
município × rede**. O enriquecimento amplia de seis para nove atributos: rede, UF,
quatro indicadores do IBGE e três indicadores educacionais do Inep. Ele acrescenta
informação contextual; não aumenta o número de alunos nem cria observações independentes.

O modelo final 1.0 utiliza seis atributos. Os nove pertencem ao estudo complementar
exploratório de 2023. Esta consolidação não ajusta modelos, não seleciona atributos
e não lê dados de 2024. Todos os números abaixo foram confrontados com as tabelas
existentes, preservando a Gold enriquecida e os resultados já publicados.

## Distribuições e ausências

Os histogramas usam uma observação por município × rede; cada contexto tem o mesmo
peso. Os valores ausentes são excluídos de cada estatística descritiva, sem imputação.

| Indicador Inep, anos iniciais de 2021 | Mediana | Intervalo observado | Contextos válidos | Contextos ausentes | Alunos sem indicador |
| --- | ---: | ---: | ---: | ---: | ---: |
| Alunos por turma | {medians[INEP[0]]} | 3,6–34,8 alunos | 5.871 | 10 | 213 |
| Funções docentes com curso superior | {medians[INEP[1]]}% | 4,7–100% | 5.872 | 9 | 173 |
| Horas de aula por dia | {medians[INEP[2]]} | 3,0–10,3 horas | 5.871 | 10 | 213 |

As distribuições mostram diferenças entre contextos. O percentual de funções docentes com
curso superior se concentra em valores elevados, com mediana de 94,4%; as horas diárias
têm mediana de 4,3 e cauda até 10,3. Valores nas caudas não são automaticamente erros
e não foram removidos por esta consolidação. Médias, quartis, desvios e extremos estão
na [tabela de distribuições](eda_enriquecida_2023_distribuicoes.csv).

A cobertura por aluno é 99,9858% em turmas/horas e 99,9885% em funções docentes. Na comparação
complementar já executada, a mediana de cada atributo foi aprendida somente no treino
do fold para tratar as ausências residuais. A [tabela de cobertura](eda_enriquecida_2023_cobertura.csv)
separa denominadores estudantis e contextuais.

![Distribuições do Inep](../images/16_eda_inep_2023.png)

## Correlações e interpretação

Os gráficos e a [tabela de associações](eda_enriquecida_2023_correlacoes.csv) usam sempre
a **taxa observada de alfabetização** como alvo. Para o IBGE, as correlações originais
de Spearman com não alfabetização têm o sinal invertido. A agregação municipal refeita
confirma essa equivalência. Para o Inep, são preservadas as correlações de Pearson
com alfabetização por município × rede; a nova agregação reproduz as tabelas existentes.

| Associação com alfabetização | Método | Unidade | Coeficiente |
| --- | --- | --- | ---: |
{_association_rows(associations)}

Coeficiente positivo indica associação com maior taxa de alfabetização; negativo,
com menor taxa, dentro da unidade observada. Métodos, anos e unidades diferentes limitam
comparações diretas entre coeficientes. Nenhum coeficiente demonstra efeito causal,
explica a trajetória individual de um aluno ou equivale à importância no modelo.

A correlação de Spearman entre PIB per capita e participação dos serviços públicos
no VAB é **{redundancy_text}**, em 4.871 municípios. A associação forte sugere redundância
entre esses atributos contextuais e exige cautela ao interpretar contribuições isoladas.
Ela não comprova causalidade e não motivou exclusão posterior de atributos do modelo final.

![Correlações com alfabetização](../images/17_correlacoes_contextuais_2023.png)

## Cronologia e relação com a modelagem

A EDA inicial antecedeu os modelos e examinou classes, regiões, distribuições, ausências
e repetição de contextos. As correlações originais do IBGE foram calculadas posteriormente,
na interpretação. A EDA dos três indicadores do Inep, incluindo correlações, foi gravada
antes dos ajustes de sua comparação exploratória, conforme o
[registro anterior ao ajuste](estudo_educacional_eda_2023.json).

**Estes novos gráficos são uma consolidação posterior** de dados e resultados já
existentes. Não são apresentados como análises que orientaram decisões no passado.
Distribuições e ausências ajudam a entender a imputação; contextos repetidos fundamentam
a separação por município; as associações ajudam a interpretar o contexto estudado.
A comparação de seis e nove atributos apresentou ganho médio pequeno de AP (+0,000531),
com melhora em dois folds e piora em um. Significância estatística não foi demonstrada.

[Proveniência e verificações](eda_enriquecida_2023.json) ·
[Comparação complementar já executada](estudo_educacional_2023.md).
"""


def _association_rows(associations: pd.DataFrame) -> str:
    return "\n".join(
        f"| {LABELS[row.attribute]} | {row.method.capitalize()} | {row.observation_unit} | "
        + f"{row.correlation_literacy:+.3f}".replace(".", ",")
        + " |"
        for row in associations.itertuples()
    )


def generate(project: Path, study: Path, output: Path) -> dict:
    project, study, output = project.resolve(), study.resolve(), output.resolve()
    if output == study or study in output.parents or output in study.parents:
        raise ValueError("Saída não pode substituir nem conter a pasta privada do estudo")
    context, municipal, counts = load_contexts(study)
    distribution, coverage, associations, matrix = summarize(context, municipal)
    provenance = verify_existing_tables(
        project, study, distribution, coverage, associations, matrix
    )
    redundancy = float(matrix.loc[IBGE[1], IBGE[3]])
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 10,
            "svg.fonttype": "none",
            "svg.hashsalt": "fiap-eda-2023",
        }
    )
    with tempfile.TemporaryDirectory(prefix="fiap-eda-enriquecida-") as temporary:
        staged = Path(temporary)
        (staged / "reports").mkdir()
        for suffix, table in (
            ("distribuicoes", distribution),
            ("cobertura", coverage),
            ("correlacoes", associations),
        ):
            table.to_csv(staged / f"{REPORT}_{suffix}.csv", index=False, encoding="utf-8-sig")
        (staged / f"{REPORT}.md").write_text(
            markdown(distribution, associations, redundancy), encoding="utf-8"
        )
        plot_distributions(context, staged)
        plot_associations(associations, redundancy, staged)
        generated = {
            str(path.relative_to(staged)): digest(path)
            for path in sorted(staged.rglob("*"))
            if path.is_file()
        }
        record = {
            "author": AUTHOR,
            "created_at_utc": datetime.now(UTC).isoformat(),
            "analysis_year": 2023,
            "kind": "consolidação descritiva posterior de dados e resultados existentes",
            "counts": counts,
            "features_original": 6,
            "features_enriched": 9,
            "context_missing_inep": {name: int(context[name].isna().sum()) for name in INEP},
            "target_orientation": "taxa observada de alfabetização em ambos os painéis",
            "ibge_method_and_unit": "Spearman, uma observação por município",
            "inep_method_and_unit": "Pearson, uma observação por município × rede",
            "pairwise_missing_policy": "pares completos; sem imputação na EDA",
            "ibge_gdp_public_services_spearman": redundancy,
            "existing_tables_reproduced": True,
            "model_fit_performed": False,
            "test_2024_read": False,
            "causal_inference": False,
            "chronology": {
                "initial_eda": "anterior aos modelos; classes, territórios, distribuições, ausências e contextos",
                "ibge_correlations": "interpretação posterior ao ajuste dos modelos originais",
                "inep_eda": "distribuições e correlações anteriores aos ajustes do estudo complementar",
                "these_figures": "consolidação posterior; não justifica retrospectivamente escolhas anteriores",
            },
            "inputs_sha256": provenance,
            "generator_sha256": digest(Path(__file__).resolve()),
            "generated_sha256": generated,
        }
        (staged / f"{REPORT}.json").write_text(
            json.dumps(record, ensure_ascii=False, indent=2, allow_nan=False) + "\n",
            encoding="utf-8",
        )
        for path in staged.rglob("*"):
            if path.is_file() and (output / path.relative_to(staged)).exists():
                raise ValueError(
                    "Saída já existente; reproduza em outra pasta sem sobrescrever arquivos"
                )
        read_verified(study / GOLD, GOLD_SHA256)
        for path in staged.rglob("*"):
            if path.is_file():
                target = output / path.relative_to(staged)
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(path, target)
        return record


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--study-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    args = parser.parse_args()
    record = generate(args.project_root, args.study_root, args.output_root)
    print(
        json.dumps(
            {"status": "EDA consolidada e conferida", **record["counts"]}, ensure_ascii=False
        )
    )


if __name__ == "__main__":
    main()
