"""Download a test clip with yt-dlp.

Point it at any football broadcast footage you have the right to use —
e.g. official league/team highlight uploads, or your own recordings.
720p is capped by default: plenty for detection, much faster to process.
"""

from __future__ import annotations

from pathlib import Path


def fetch_clip(url: str, out_dir: str | Path = "data/clips", max_height: int = 720) -> Path:
    """Download the video at `url` and return the saved file path."""
    import yt_dlp

    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    options = {
        "format": f"bv*[height<={max_height}][ext=mp4]+ba[ext=m4a]/b[height<={max_height}][ext=mp4]/b",
        "outtmpl": str(out / "%(title).80s.%(ext)s"),
        "merge_output_format": "mp4",
        "noplaylist": True,
    }
    with yt_dlp.YoutubeDL(options) as ydl:
        info = ydl.extract_info(url, download=True)
        return Path(ydl.prepare_filename(info)).with_suffix(".mp4")


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        raise SystemExit("Usage: python scripts/get_sample_clip.py <url> [out_dir]")
    dest = sys.argv[2] if len(sys.argv) > 2 else "data/clips"
    print(fetch_clip(sys.argv[1], dest))
