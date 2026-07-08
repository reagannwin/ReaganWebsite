# Football CV — broadcast play tracking & insights

Computer vision pipeline that watches American football broadcast footage and
produces play-by-play data: it detects and tracks every player, splits them
into teams by jersey color, segments the broadcast into individual plays, and
reports per-player speed and distance for each play.

## What it does

```
broadcast video ─▶ player detection (YOLOv8)
                 ─▶ multi-object tracking (ByteTrack)
                 ─▶ team split (jersey-color clustering)
                 ─▶ play segmentation (activity signal + camera-cut detection)
                 ─▶ field mapping (click-to-calibrate homography → yards/mph)
                 ─▶ insights: report.html, report.json, players.csv, annotated.mp4
```

- **Plays detected automatically** — the pipeline finds bursts of coordinated
  player movement between static pre-snap stretches, and uses camera-cut
  detection so replays and crowd shots don't pollute the data.
- **Real units with one minute of setup** — click 4+ known field landmarks
  once per camera angle and every metric switches from pixels to yards and mph.
- **Runs on a laptop** — CPU-friendly defaults (nano model, frame striding);
  one config change unlocks full quality on a GPU.

## Quick start

```sh
cd football-cv
python -m venv .venv
.venv\Scripts\activate            # Windows  (source .venv/bin/activate on mac/linux)
pip install -r requirements.txt

# 1. Get a test clip (any footage you have the right to use, e.g. official
#    league/team highlight uploads or your own recordings)
python cli.py fetch "https://www.youtube.com/watch?v=..."

# 2. Analyze it
python cli.py analyze "data/clips/your-clip.mp4" --render

# 3. Open the results
#    output/<clip-name>/report.html    ← play-by-play dashboard
#    output/<clip-name>/annotated.mp4  ← tracked video
#    output/<clip-name>/players.csv    ← raw per-player numbers
```

First run downloads the YOLOv8 weights (~6 MB for the nano model) automatically.

### Getting real yards and mph

Without calibration the numbers are relative (pixels). To get real units:

```sh
python cli.py calibrate "data/clips/your-clip.mp4" --out calibration.json --at 12.5
```

A window shows the frame at that timestamp. Click 4+ points whose field
position you know — yard line × sideline intersections are ideal — press
ENTER, then type each point's coordinates (x: 0–120 yd along the sideline,
goal lines at 10 and 110; y: 0–53.3 yd across). Then:

```sh
python cli.py analyze "data/clips/your-clip.mp4" --calibration calibration.json --render
```

Calibration is per camera angle: it's most accurate for clips from the main
sideline (all-22 style) camera. Highlight reels that cut between many angles
will still segment plays fine but yardage is only valid on the calibrated angle.

## CPU laptop vs GPU

`config.yaml` ships with the CPU preset. On a machine with an NVIDIA GPU:

```yaml
video:
  frame_stride: 1
detection:
  model: yolov8m.pt   # or yolov8x.pt
  imgsz: 1280         # catches small/far-away players
  device: cuda:0
```

and install CUDA-enabled PyTorch first
(`pip install torch --index-url https://download.pytorch.org/whl/cu121`).

## Test footage sources

- **Your own recordings** of games you're allowed to use.
- **Official highlight uploads** (league/team channels) via `cli.py fetch`.
- **Kaggle — NFL Health & Safety: Helmet Assignment** — thousands of real
  broadcast + all-22 clips, free with a Kaggle account:
  `kaggle competitions download -c nfl-health-and-safety-helmet-assignment`

## Project layout

```
football-cv/
├── cli.py                    # analyze / calibrate / fetch commands
├── config.yaml               # tuning knobs (CPU preset)
├── src/footballcv/
│   ├── detection.py          # YOLOv8 player + ball detection
│   ├── tracking.py           # ByteTrack IDs + position history
│   ├── teams.py              # jersey-color KMeans → team labels
│   ├── field.py              # homography: pixels → field yards
│   ├── plays.py              # play segmentation + camera-cut detection
│   ├── insights.py           # per-play speed/distance metrics
│   ├── annotate.py           # annotated video rendering
│   ├── report.py             # HTML/JSON/CSV output
│   ├── calibrate.py          # interactive click-to-calibrate tool
│   └── pipeline.py           # orchestrates the two passes
├── scripts/get_sample_clip.py
└── tests/                    # pytest suite for the analytics logic
```

## Running the tests

```sh
pip install -r requirements.txt
pytest tests/
```

## Roadmap

- [ ] Automatic field-line calibration (no clicking)
- [ ] Snap detection → pre-snap formation recognition
- [ ] Ball-carrier identification and route visualization
- [ ] Top-down play diagrams rendered per play
- [ ] Jersey number OCR for real player identity
