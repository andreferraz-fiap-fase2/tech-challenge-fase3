"""Autor: André Mohallem Ferraz. Gera documentos de preparação em pasta separada."""

import argparse
from pathlib import Path

from documentos_slides import SlideDocuments
from documentos_word import WordDocuments


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--report-version", default="1.0", help="Versão N.N dos entregáveis")
    parser.add_argument(
        "--report-only", action="store_true", help="Gera somente o relatório técnico"
    )
    args = parser.parse_args()
    args.output = args.output.resolve()
    if "entrega-final" in {part.casefold() for part in args.output.parts}:
        parser.error("Use uma pasta de Preparacao: arquivos intermediários não são entregáveis")
    WordDocuments(args.output, args.report_version).report()
    if args.report_only:
        print("Relatório técnico gerado:", args.output)
        return
    SlideDocuments(args.output, args.report_version).presentation()
    print("Documentos e oito slides gerados:", args.output)


if __name__ == "__main__":
    main()
