/**
 * ============================================================
 *  YOUR PROJECTS LIVE HERE
 * ============================================================
 *  To add a new side project, copy one of the objects below,
 *  fill in your details, and push. That's it — the site
 *  renders this list automatically.
 *
 *  Fields:
 *    title    — project name
 *    blurb    — 1–3 sentence description of what it does
 *    stack    — array of technologies used (shown as tags)
 *    live     — URL of the deployed app  (omit or null to hide the link)
 *    source   — URL of the GitHub repo   (omit or null to hide the link)
 *    featured — true to give it a highlighted, full-width card
 * ============================================================
 */
const PROJECTS = [
  {
    title: "Football CV — Broadcast Play Tracker",
    blurb:
      "Computer vision pipeline that watches American football broadcast " +
      "footage and produces play-by-play insights: detects and tracks every " +
      "player, splits teams by jersey color, auto-segments the broadcast " +
      "into plays, and reports per-player speed and distance in real yards " +
      "and mph via click-to-calibrate field mapping.",
    stack: ["Python", "YOLOv8", "OpenCV", "ByteTrack", "scikit-learn"],
    live: null,
    source: "https://github.com/reagannwin/ReaganWebsite/tree/main/football-cv",
    featured: true,
  },
  {
    title: "Example: Weather Dashboard",
    blurb:
      "REPLACE ME — another sample. Pulls live data from a public API and " +
      "charts it with a responsive UI.",
    stack: ["JavaScript", "Chart.js", "REST APIs"],
    live: null,
    source: null,
    featured: false,
  },
  {
    title: "Example: CLI Toolkit",
    blurb:
      "REPLACE ME — a third sample. A command-line utility suite for " +
      "automating everyday dev tasks.",
    stack: ["Python", "Shell"],
    live: null,
    source: null,
    featured: false,
  },
];
