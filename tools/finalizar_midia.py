"""Autor: André Mohallem Ferraz. Exporta mídia executiva com duração conferida."""

import argparse
import hashlib
import json
import re
import subprocess
import wave
from pathlib import Path

import imageio_ffmpeg
import pymupdf

AUTHOR = "André Mohallem Ferraz"


def stamp_pdfs(output: Path) -> list[dict]:
    receipts = []
    for path in sorted(output.glob("*.pdf")):
        with pymupdf.open(path) as document:
            document.set_metadata(
                {**document.metadata, "author": AUTHOR, "title": path.stem.replace("-", " ")}
            )
            document.saveIncr()
            receipts.append({"file": path.name, "pages": len(document), "author": AUTHOR})
    return receipts


def audio_durations(output: Path) -> list[float]:
    durations = []
    for index in range(1, 9):
        with wave.open(str(output / f"audio/slide-{index:02d}.wav")) as sound:
            durations.append(sound.getnframes() / sound.getframerate() + 0.5)
    if sum(durations) > 299:
        raise ValueError(f"Duração {sum(durations):.2f}s; esperado até 299s com margem de 1s")
    return durations


def encode_clip(ffmpeg: str, output: Path, index: int, duration: float) -> Path:
    clip = output / f"render/clip-{index:02d}.mp4"
    subprocess.run(
        [
            ffmpeg,
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-loop",
            "1",
            "-framerate",
            "24",
            "-i",
            str(output / f"render/slide-{index:02d}.png"),
            "-i",
            str(output / f"audio/slide-{index:02d}.wav"),
            "-vf",
            "scale=1280:720",
            "-c:v",
            "libx264",
            "-preset",
            "fast",
            "-tune",
            "stillimage",
            "-crf",
            "21",
            "-pix_fmt",
            "yuv420p",
            "-threads",
            "2",
            "-c:a",
            "aac",
            "-b:a",
            "128k",
            "-ar",
            "48000",
            "-af",
            "apad=pad_dur=0.5",
            "-t",
            str(duration),
            str(clip),
        ],
        check=True,
    )
    return clip


def assemble_video(ffmpeg: str, output: Path, clips: list[Path], version: str = "1.0") -> Path:
    listing = output / "render/clips.txt"
    listing.write_text("\n".join(f"file '{clip.name}'" for clip in clips) + "\n")
    video = output / f"Video-Executivo-Fase3-v{version}.mp4"
    subprocess.run(
        [
            ffmpeg,
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(listing),
            "-c",
            "copy",
            "-movflags",
            "+faststart",
            "-metadata",
            f"artist={AUTHOR}",
            "-metadata",
            f"author={AUTHOR}",
            "-metadata",
            "title=Alfabetização — Tech Challenge Fase 3",
            "-metadata",
            "comment=Narração sintética em português; Microsoft Maria Desktop. Trabalho individual.",
            str(video),
        ],
        check=True,
    )
    subprocess.run([ffmpeg, "-v", "error", "-i", str(video), "-f", "null", "-"], check=True)
    return video


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--version", default="1.0")
    parser.add_argument(
        "--generate-video", action="store_true", help="Gera vídeo somente quando solicitado"
    )
    args = parser.parse_args()
    if not re.fullmatch(r"\d+\.\d+", args.version):
        parser.error("Versão inválida; esperado N.N")
    output = args.output.resolve()
    if "entrega-final" in {part.casefold() for part in output.parts}:
        parser.error("Use uma pasta de Preparacao; recibos e mídia de apoio ficam fora da entrega")
    pdfs = stamp_pdfs(output)
    if not args.generate_video:
        receipt = {
            "author": AUTHOR,
            "version": args.version,
            "pdfs": pdfs,
            "video_generated": False,
        }
        (output / "verificacao-documentos.json").write_text(
            json.dumps(receipt, ensure_ascii=False, indent=2) + "\n"
        )
        print(json.dumps(receipt, ensure_ascii=False), flush=True)
        return
    durations = audio_durations(output)
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    clips = [encode_clip(ffmpeg, output, i, seconds) for i, seconds in enumerate(durations, 1)]
    video = assemble_video(ffmpeg, output, clips, args.version)
    frames = imageio_ffmpeg.read_frames(str(video))
    metadata = next(frames)
    frames.close()
    if metadata["duration"] > 300:
        raise ValueError(f"Vídeo com {metadata['duration']}s; esperado até 300s")
    receipt = {
        "author": AUTHOR,
        "pdfs": pdfs,
        "slide_seconds": durations,
        "planned_seconds": sum(durations),
        "actual_seconds": metadata["duration"],
        "resolution": list(metadata["size"]),
        "video": video.name,
        "video_sha256": hashlib.sha256(video.read_bytes()).hexdigest(),
        "video_bytes": video.stat().st_size,
        "full_decode_verified": True,
    }
    (output / "verificacao-midia.json").write_text(
        json.dumps(receipt, ensure_ascii=False, indent=2) + "\n"
    )
    print(json.dumps(receipt, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
