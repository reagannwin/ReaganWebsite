"""footballcv command line.

  python cli.py analyze game.mp4 --render          # full analysis + annotated video
  python cli.py analyze game.mp4 --calibration c.json
  python cli.py calibrate game.mp4 --out c.json    # click landmarks -> yards/mph
  python cli.py fetch "https://youtube.com/..."    # download a test clip
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

logging.basicConfig(level=logging.INFO, format="%(message)s")
log = logging.getLogger("footballcv")


def _cmd_analyze(args: argparse.Namespace) -> int:
    from footballcv.config import load_config
    from footballcv.pipeline import run

    config = load_config(args.config)
    out_dir = run(
        args.video,
        config,
        calibration_path=args.calibration,
        render=args.render,
    )
    log.info("\nDone. Results in %s", out_dir.resolve())
    log.info("  report.html — open in a browser")
    log.info("  report.json / players.csv — raw data")
    if args.render:
        log.info("  annotated.mp4 — tracked video")
    return 0


def _cmd_calibrate(args: argparse.Namespace) -> int:
    from footballcv.calibrate import calibrate_interactive

    calibrate_interactive(args.video, args.out, at_seconds=args.at)
    return 0


def _cmd_fetch(args: argparse.Namespace) -> int:
    from scripts.get_sample_clip import fetch_clip

    path = fetch_clip(args.url, args.out_dir, args.max_height)
    log.info("Saved: %s", path)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="footballcv", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    p_an = sub.add_parser("analyze", help="Analyze a broadcast video")
    p_an.add_argument("video", help="Path to the video file")
    p_an.add_argument("--config", default=str(Path(__file__).parent / "config.yaml"))
    p_an.add_argument("--calibration", default=None, help="Calibration JSON for yards/mph")
    p_an.add_argument("--render", action="store_true", help="Also write annotated.mp4")
    p_an.set_defaults(func=_cmd_analyze)

    p_cal = sub.add_parser("calibrate", help="Create a field calibration for a camera angle")
    p_cal.add_argument("video", help="Path to the video file")
    p_cal.add_argument("--out", default="calibration.json")
    p_cal.add_argument("--at", type=float, default=0.0, help="Timestamp (s) of the frame to calibrate on")
    p_cal.set_defaults(func=_cmd_calibrate)

    p_f = sub.add_parser("fetch", help="Download a test clip from a URL (yt-dlp)")
    p_f.add_argument("url")
    p_f.add_argument("--out-dir", default="data/clips")
    p_f.add_argument("--max-height", type=int, default=720)
    p_f.set_defaults(func=_cmd_fetch)

    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except (FileNotFoundError, RuntimeError, ValueError) as exc:
        log.error("Error: %s", exc)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
