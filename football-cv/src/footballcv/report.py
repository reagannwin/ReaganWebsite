"""Write analysis results to JSON, CSV, and a self-contained HTML report."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from .insights import PlayStats, play_stats_to_dict, summarize


def write_reports(plays: list[PlayStats], out_dir: str | Path, video_name: str) -> Path:
    """Write report.json, players.csv, and report.html. Returns the out dir."""
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    summary = summarize(plays)
    payload = {
        "video": video_name,
        "summary": summary,
        "plays": [play_stats_to_dict(p) for p in plays],
    }
    (out / "report.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")

    rows = [
        {
            "play": p.play_number,
            "start_time_s": p.start_time_s,
            "duration_s": p.duration_s,
            "track_id": pl.track_id,
            "team": pl.team,
            "distance": pl.distance,
            "avg_speed": pl.avg_speed,
            "max_speed": pl.max_speed,
        }
        for p in plays
        for pl in p.players
    ]
    pd.DataFrame(rows).to_csv(out / "players.csv", index=False)

    (out / "report.html").write_text(_render_html(video_name, summary, plays), encoding="utf-8")
    return out


def _render_html(video_name: str, summary: dict, plays: list[PlayStats]) -> str:
    units = summary.get("units", "")
    cards = "".join(
        f"<div class='card'><div class='num'>{v}</div><div class='lbl'>{k}</div></div>"
        for k, v in [
            ("plays detected", summary.get("n_plays", 0)),
            ("avg play length", f"{summary.get('avg_play_duration_s', '—')}s"),
            ("longest play", f"{summary.get('longest_play_s', '—')}s"),
            ("top speed", f"{summary.get('top_speed_observed', '—')}"),
        ]
    )
    play_rows = ""
    for p in plays:
        top = p.players[0] if p.players else None
        top_txt = f"#{top.track_id} @ {top.max_speed}" if top else "—"
        play_rows += (
            f"<tr><td>{p.play_number}</td><td>{p.start_time_s}s</td>"
            f"<td>{p.duration_s}s</td><td>{p.n_players}</td><td>{top_txt}</td></tr>"
        )
    return f"""<!doctype html><html><head><meta charset="utf-8">
<title>Football CV — {video_name}</title>
<style>
  body {{ font-family: system-ui, sans-serif; margin: 2rem auto; max-width: 720px; color: #1c2430; }}
  h1 {{ font-size: 1.4rem; }} .units {{ color: #6b7686; font-size: 0.85rem; }}
  .cards {{ display: flex; gap: 12px; flex-wrap: wrap; margin: 1.2rem 0; }}
  .card {{ background: #f2f5f9; border-radius: 10px; padding: 14px 18px; min-width: 120px; }}
  .num {{ font-size: 1.5rem; font-weight: 700; }} .lbl {{ font-size: 0.78rem; color: #6b7686; }}
  table {{ border-collapse: collapse; width: 100%; }} th, td {{ padding: 7px 10px; text-align: left; }}
  th {{ border-bottom: 2px solid #d6dde6; font-size: 0.8rem; text-transform: uppercase; color: #6b7686; }}
  tr:nth-child(even) {{ background: #f7f9fb; }}
</style></head><body>
<h1>Play analysis — {video_name}</h1>
<p class="units">units: {units}</p>
<div class="cards">{cards}</div>
<table><thead><tr><th>Play</th><th>Start</th><th>Duration</th><th>Players tracked</th><th>Fastest player</th></tr></thead>
<tbody>{play_rows}</tbody></table>
</body></html>"""
