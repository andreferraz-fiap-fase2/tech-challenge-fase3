"""Autor: André Mohallem Ferraz. Gera Word, PowerPoint e roteiro da entrega."""

import argparse
from pathlib import Path

from documentos_slides import SlideDocuments
from documentos_word import WordDocuments


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    WordDocuments(args.output).report()
    SlideDocuments(args.output).presentation()
    print("Documentos e oito slides gerados:", args.output)


if __name__ == "__main__":
    main()
