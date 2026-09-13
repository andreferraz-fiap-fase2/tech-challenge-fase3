"""CLI do projeto; exemplos: `python -m src.pipeline gold` e `... baseline`."""

import argparse
import json
from pathlib import Path

from src.domain.contract import ContractError
from src.infrastructure.files import FileStore
from src.usecase.baseline import run_baseline
from src.usecase.boosting import run_boosting
from src.usecase.eda import run_eda
from src.usecase.final_figures import run_final_figures
from src.usecase.final_fit import run_final_fit
from src.usecase.freeze import run_freeze
from src.usecase.interpretation import run_interpretation
from src.usecase.logistic import run_logistic
from src.usecase.prepare import build_all_gold, import_snapshot
from src.usecase.strategy import run_strategy
from src.usecase.temporal import run_temporal


def argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Fase 3 — modelagem, avaliação e inteligência territorial"
    )
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    subparsers = parser.add_subparsers(dest="command", required=True)
    preparation = subparsers.add_parser(
        "prepare", help="Importa o snapshot verificado da etapa anterior"
    )
    preparation.add_argument(
        "--source", required=True, type=Path, help="Pasta apoio com fontes-fase2 e fontes-externas"
    )
    subparsers.add_parser("gold", help="Constrói Gold 2023/2024 sem modelar o teste")
    subparsers.add_parser("eda", help="EDA exclusivamente de 2023")
    subparsers.add_parser("baseline", help="DummyClassifier com validação por município em 2023")
    subparsers.add_parser("logistic", help="Compara duas Regressões Logísticas nos folds de 2023")
    subparsers.add_parser(
        "boosting", help="Busca limitada de Gradient Boosting e confirmação em 2023"
    )
    subparsers.add_parser(
        "run-all", help="Gold + EDA + baseline + logística + boosting; requer prepare anterior"
    )
    subparsers.add_parser("freeze", help="Congela modelo e limiar usando apenas 2023")
    subparsers.add_parser("final-fit", help="Ajusta o modelo congelado em todo 2023")
    subparsers.add_parser(
        "temporal", help="Avalia uma vez o teste 2024 com modelo e limiar congelados"
    )
    subparsers.add_parser("interpret", help="Importância por permutação e correlações em 2023")
    subparsers.add_parser(
        "strategy", help="Leitura territorial do teste congelado e metas de referência"
    )
    subparsers.add_parser("final-figures", help="Exporta as figuras finais do experimento")
    return parser


def main() -> None:
    args = argument_parser().parse_args()
    store = FileStore(args.root)
    if (store.root / "config/modelo-final.json").exists() and args.command in {
        "run-all",
        "logistic",
        "boosting",
    }:
        raise ContractError(
            "Entrega congelada; use src.usecase.reproduce_all para repetir sem sobrescrever os resultados"
        )
    if args.command == "prepare":
        print(json.dumps(import_snapshot(store, args.source), ensure_ascii=False))
        return
    operations = {
        "gold": build_all_gold,
        "eda": run_eda,
        "baseline": run_baseline,
        "logistic": run_logistic,
        "boosting": run_boosting,
    }
    commands = tuple(operations) if args.command == "run-all" else (args.command,)
    operations.update({"freeze": run_freeze, "final-fit": run_final_fit, "temporal": run_temporal})
    operations.update(
        {
            "interpret": run_interpretation,
            "strategy": run_strategy,
            "final-figures": run_final_figures,
        }
    )
    for command in commands:
        result = operations[command](store)
        print(json.dumps({"stage": command, "result": result}, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
