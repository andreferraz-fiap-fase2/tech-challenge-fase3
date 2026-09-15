"""Autor: André Mohallem Ferraz. Monta a pasta oficial a partir dos documentos de preparação.

A pasta oficial reúne apenas a visão técnica em PDF, a apresentação em PowerPoint e um ZIP
com esses dois arquivos, e a montagem falha se sobrar qualquer outro arquivo. Roteiros,
editáveis, renderizações e recibos ficam na preparação, como definido na reorganização 1.4.
O ZIP é determinístico: mesma entrada produz o mesmo SHA-256.

Exemplo:
    python tools/montar_entrega_oficial.py --documentos /caminho/documentos-1.7 \\
        --version 1.7 --output "/caminho/Entrega-Final-1.7"
"""

import argparse
import hashlib
import re
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

AUTHOR = "André Mohallem Ferraz"
ARCHIVE = "TechChallenge-Fase3.zip"
FIXED_TIMESTAMP = (1980, 1, 1, 0, 0, 0)
OFFICIAL_NAMES = {
    "Relatorio-Tecnico-Fase3-v{version}.pdf": "VisaoTecnica-TechChallengeFase3.pdf",
    "Apresentacao-Executiva-Fase3-v{version}.pptx": "Apresentacao-TechChallenge-Fase3.pptx",
}


def digest(path: Path) -> str:
    """SHA-256 de um arquivo; exemplo: `digest(Path('a.pdf'))`."""
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def resolve_sources(documents: Path, version: str) -> dict[str, Path]:
    """Mapeia nome oficial para o arquivo de origem; exemplo: `resolve_sources(pasta, '1.7')`."""
    resolved: dict[str, Path] = {}
    for template, official in OFFICIAL_NAMES.items():
        source = documents / template.format(version=version)
        if not source.is_file():
            raise FileNotFoundError(f"Ausente: {source}; esperado documento da versão {version}")
        resolved[official] = source
    return resolved


def require_empty(output: Path) -> None:
    """Protege entregas anteriores; exemplo: `require_empty(Path('Entrega-Final-1.7'))`."""
    if output.exists() and any(output.iterdir()):
        raise FileExistsError(f"{output} já contém arquivos; esperado pasta nova para a versão")


def copy_official(sources: dict[str, Path], output: Path) -> dict[str, str]:
    """Copia com os nomes da entrega e devolve os hashes; exemplo: `copy_official(src, out)`."""
    hashes: dict[str, str] = {}
    for official, source in sources.items():
        target = output / official
        target.write_bytes(source.read_bytes())
        hashes[official] = digest(target)
    return hashes


def deterministic_entry(name: str) -> ZipInfo:
    """Data fixa para que o mesmo conteúdo gere o mesmo ZIP; exemplo: `deterministic_entry('a.pdf')`."""
    entry = ZipInfo(name, date_time=FIXED_TIMESTAMP)
    entry.compress_type = ZIP_DEFLATED
    entry.external_attr = 0o644 << 16
    return entry


def build_archive(output: Path, official_names: list[str]) -> str:
    """Empacota somente os dois documentos, na ordem oficial; exemplo: `build_archive(out, nomes)`."""
    archive = output / ARCHIVE
    with ZipFile(archive, "w", compression=ZIP_DEFLATED) as bundle:
        for name in official_names:
            bundle.writestr(deterministic_entry(name), (output / name).read_bytes())
    return digest(archive)


def require_preparation(destination: Path) -> None:
    """Recibos ficam fora da entrega; cobre `Entrega-Final` e `Entrega-Final-1.7`."""
    if any(part.casefold().startswith("entrega-final") for part in destination.parts):
        raise ValueError(f"Recibo em {destination}; esperado uma pasta de Preparacao")


def write_receipt(documents: Path, version: str, hashes: dict[str, str]) -> Path:
    """Grava o sha256sum na preparação; exemplo: `write_receipt(docs, '1.7', hashes)`."""
    receipt = documents / f"sha256-entrega-{version}.txt"
    require_preparation(receipt)
    lines = [f"{value}  {name}" for name, value in sorted(hashes.items())]
    receipt.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return receipt


def verify_official_folder(output: Path) -> None:
    """A pasta oficial tem exatamente os três arquivos; exemplo: `verify_official_folder(out)`."""
    expected = {*OFFICIAL_NAMES.values(), ARCHIVE}
    actual = {path.name for path in output.iterdir()}
    if actual != expected:
        raise ValueError(f"Pasta oficial com {sorted(actual)}; esperado {sorted(expected)}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--documentos", type=Path, required=True)
    parser.add_argument("--version", required=True, help="Versão N.N dos documentos gerados")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if not re.fullmatch(r"\d+\.\d+", args.version):
        parser.error(f"Versão {args.version!r}; esperado formato N.N")
    output, documents = args.output.resolve(), args.documentos.resolve()
    require_empty(output)
    output.mkdir(parents=True, exist_ok=True)
    sources = resolve_sources(documents, args.version)
    hashes = copy_official(sources, output)
    hashes[ARCHIVE] = build_archive(output, list(OFFICIAL_NAMES.values()))
    verify_official_folder(output)
    receipt = write_receipt(documents, args.version, hashes)
    print(f"Entrega oficial {args.version} montada em {output}")
    for name, value in sorted(hashes.items()):
        print(f"  {value}  {name}")
    print(f"Recibo gravado fora da entrega: {receipt}")


if __name__ == "__main__":
    main()
