#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

from docx import Document


VIDEO_SUFFIXES = {".mp4", ".mov", ".avi", ".mkv", ".m4v", ".webm"}


def normalize_title(title: str) -> str:
    value = title.strip().replace("(", "（").replace(")", "）")
    value = re.sub(r"\s*（\s*", "（", value)
    value = re.sub(r"\s*）\s*", "）", value)
    value = re.sub(r"\s+", " ", value).strip()
    match = re.search(r"《(.+?)》", value)
    return match.group(1).strip() if match else value.split("-", 1)[0].strip()


def title_key(title: str) -> str:
    return re.sub(r"[\W_]+", "", normalize_title(title), flags=re.UNICODE).lower()


def source_index(path: Path) -> int | None:
    match = re.match(r"^\s*0*(\d+)", path.stem)
    return int(match.group(1)) if match else None


def source_title(path: Path) -> str:
    return re.sub(r"^\s*0*\d+[\s._-]*", "", path.stem).strip()


def read_program_list(path: Path) -> list[tuple[int, str]]:
    doc = Document(path)
    for table in doc.tables:
        songs: list[tuple[int, str]] = []
        for row in table.rows:
            cells = [cell.text.strip() for cell in row.cells]
            if len(cells) < 2:
                continue
            match = re.search(r"\d+", cells[0])
            if match and cells[1]:
                songs.append((int(match.group()), normalize_title(cells[1])))
        if songs:
            return songs
    raise RuntimeError("节目单中没有找到可识别的曲目表格。")


def find_sources(source_dir: Path) -> tuple[dict[int, Path], list[Path]]:
    indexed: dict[int, Path] = {}
    unindexed: list[Path] = []
    for path in sorted(source_dir.iterdir()):
        if not path.is_file() or path.suffix.lower() not in VIDEO_SUFFIXES:
            continue
        index = source_index(path)
        if index is None:
            unindexed.append(path)
        elif index in indexed:
            raise RuntimeError(f"发现重复视频序号 {index}: {indexed[index].name} / {path.name}")
        else:
            indexed[index] = path
    return indexed, unindexed


def ffprobe_duration(path: Path) -> float:
    output = subprocess.check_output(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(path),
        ],
        text=True,
    )
    return float(output.strip())


def encode_once(source: Path, output: Path, video_kbps: int, audio_kbps: int) -> None:
    subprocess.run(
        [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-stats",
            "-y",
            "-i",
            str(source),
            "-vf",
            "scale=-2:480",
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-b:v",
            f"{video_kbps}k",
            "-maxrate",
            f"{video_kbps}k",
            "-bufsize",
            f"{video_kbps * 2}k",
            "-c:a",
            "aac",
            "-b:a",
            f"{audio_kbps}k",
            "-movflags",
            "+faststart",
            str(output),
        ],
        check=True,
    )


def encode_two_pass(source: Path, output: Path, video_kbps: int, audio_kbps: int) -> None:
    with tempfile.TemporaryDirectory(prefix="approval-video-") as temp_dir:
        passlog = str(Path(temp_dir) / "ffmpeg2pass")
        common = [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-i",
            str(source),
            "-vf",
            "scale=-2:480",
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-b:v",
            f"{video_kbps}k",
            "-passlogfile",
            passlog,
        ]
        subprocess.run(common + ["-pass", "1", "-an", "-f", "mp4", "/dev/null"], check=True)
        subprocess.run(
            common
            + [
                "-pass",
                "2",
                "-c:a",
                "aac",
                "-b:a",
                f"{audio_kbps}k",
                "-movflags",
                "+faststart",
                str(output),
            ],
            check=True,
        )


def bitrate_for_max_size(duration: float, target_mb: float, audio_kbps: int) -> int:
    total_kbps = target_mb * 1024 * 1024 * 8 / duration / 1000
    return max(250, int(total_kbps - audio_kbps - 24))


def popup_missing(missing: list[tuple[int, str]]) -> None:
    if not missing or not shutil.which("osascript"):
        return
    lines = "\\n".join(f"{index}.{title}" for index, title in missing)
    script = f'display dialog "报批视频缺失：\\n{lines}" with title "报批视频缺失提醒" buttons {{"知道了"}} default button "知道了" with icon caution giving up after 15'
    subprocess.Popen(["osascript", "-e", script], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def main() -> None:
    parser = argparse.ArgumentParser(description="按节目单匹配、改名并压缩报批视频。")
    parser.add_argument("--program-list", required=True, type=Path)
    parser.add_argument("--source-dir", required=True, type=Path)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--video-kbps", type=int, default=1200)
    parser.add_argument("--audio-kbps", type=int, default=64)
    parser.add_argument("--max-mb", type=float, default=50)
    parser.add_argument("--target-mb", type=float, default=47)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--no-popup", action="store_true")
    args = parser.parse_args()

    output_dir = args.output_dir or args.source_dir / "报批视频已压缩"
    songs = read_program_list(args.program_list)
    indexed, unindexed = find_sources(args.source_dir)
    by_title = {title_key(source_title(path)): path for path in unindexed}

    matched: list[tuple[int, str, Path]] = []
    missing: list[tuple[int, str]] = []
    for index, title in songs:
        source = indexed.get(index) or by_title.get(title_key(title))
        if source:
            matched.append((index, title, source))
        else:
            missing.append((index, title))

    print(f"节目单={len(songs)} 匹配={len(matched)} 缺失={len(missing)}")
    for index, title in missing:
        print(f"缺失: {index}.{title}")
    if not args.no_popup:
        popup_missing(missing)
    if args.dry_run:
        return

    output_dir.mkdir(parents=True, exist_ok=True)
    generated: list[dict[str, object]] = []
    for index, title, source in matched:
        output = output_dir / f"{index}.{title}.mp4"
        print(f"[{index:02d}/{len(songs):02d}] {source.name} -> {output.name}", flush=True)
        encode_once(source, output, args.video_kbps, args.audio_kbps)
        size_mb = output.stat().st_size / 1024 / 1024
        if size_mb > args.max_mb:
            duration = ffprobe_duration(source)
            adjusted_kbps = min(
                args.video_kbps,
                bitrate_for_max_size(duration, args.target_mb, args.audio_kbps),
            )
            print(f"重压: {output.name} {size_mb:.1f}MB -> {adjusted_kbps}k", flush=True)
            encode_two_pass(source, output, adjusted_kbps, args.audio_kbps)
            size_mb = output.stat().st_size / 1024 / 1024
        generated.append({"file": output.name, "size_mb": round(size_mb, 1)})

    report = {
        "program_count": len(songs),
        "matched_count": len(matched),
        "missing": [{"index": index, "title": title} for index, title in missing],
        "generated": generated,
        "settings": {
            "format": "mp4",
            "video_codec": "h264",
            "height": 480,
            "default_video_kbps": args.video_kbps,
            "audio_codec": "aac",
            "audio_kbps": args.audio_kbps,
            "max_mb": args.max_mb,
        },
    }
    (output_dir / "压缩报告.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
