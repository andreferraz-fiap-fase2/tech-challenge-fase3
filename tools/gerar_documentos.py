"""Autor: André Mohallem Ferraz. Gera Word, PowerPoint e roteiro da entrega."""

import argparse
from pathlib import Path

from documentos_slides import SlideDocuments
from documentos_word import WordDocuments


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--report-version", default="1.0", help="Revisão documental N.N")
    parser.add_argument(
        "--report-only", action="store_true", help="Gera somente o relatório técnico"
    )
    args = parser.parse_args()
    WordDocuments(args.output, args.report_version).report()
    if args.report_only:
        print("Relatório técnico gerado:", args.output)
        return
    SlideDocuments(args.output).presentation()
    print("Documentos e oito slides gerados:", args.output)


if __name__ == "__main__":
    main()
