"""CLI do projeto; exemplos: `python -m src.pipeline gold` e `... baseline`."""

import argparse
import json
from pathlib import Path

from src.infrastructure.files import FileStore
from src.usecase.baseline import run_baseline
from src.usecase.eda import run_eda
from src.usecase.logistic import run_logistic
from src.usecase.prepare import build_all_gold, import_snapshot


def argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Fase 3 — Gold, EDA e baseline de desenvolvimento")
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
        "run-all", help="Gold + EDA + baseline + logística; requer prepare anterior"
    )
    return parser


def main() -> None:
    args = argument_parser().parse_args()
    store = FileStore(args.root)
    if args.command == "prepare":
        print(json.dumps(import_snapshot(store, args.source), ensure_ascii=False))
        return
    operations = {
        "gold": build_all_gold,
        "eda": run_eda,
        "baseline": run_baseline,
        "logistic": run_logistic,
    }
    commands = tuple(operations) if args.command == "run-all" else (args.command,)
    for command in commands:
        result = operations[command](store)
        print(json.dumps({"stage": command, "result": result}, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
