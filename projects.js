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
    title: "Minneapolis Food Inspections Analysis",
    blurb:
      "Cleaned and analyzed 41,646 City of Minneapolis food-inspection " +
      "records covering 2,916 facilities (2023–2025) to identify what " +
      "drives pass/fail outcomes — violation patterns, risk tiers, and " +
      "neighborhood trends — as a practical reference for anyone opening " +
      "a food business in the city.",
    stack: ["Python", "pandas", "Jupyter"],
    live: null,
    source: "https://github.com/reagannwin/Minneapolis-Food-Inspections",
    featured: false,
  },
  {
    title: "Movie Discovery App",
    blurb:
      "Single-page React app for browsing and searching movies from the " +
      "TMDB API, with debounced search to cut redundant requests while " +
      "you type. The trending section is backed by Appwrite — per-movie " +
      "search counts are persisted and ranked, so trending reflects real " +
      "user demand rather than a static list.",
    stack: ["React", "Vite", "Tailwind CSS", "Appwrite", "TMDB API"],
    live: null,
    source: "https://github.com/reagannwin/MovieProject",
    featured: false,
  },
  {
    title: "Bank Customer Churn Prediction",
    blurb:
      "Trained and compared six classification models — logistic " +
      "regression through XGBoost — to predict which bank customers are " +
      "likely to churn. Corrected class imbalance with SMOTE and tuned " +
      "each model with GridSearchCV, evaluating on ROC-AUC.",
    stack: ["Python", "scikit-learn", "XGBoost", "SMOTE"],
    live: null,
    source: "https://github.com/reagannwin/BankCustomerChurn",
    featured: false,
  },
  {
    title: "DJ Trivia Study Bot",
    blurb:
      "Web scraper that collects trivia source material and turns it into " +
      "prompt-engineered LLM study sessions. Field-tested: tied for first " +
      "place at a December 2025 trivia event.",
    stack: ["Python", "Web scraping", "LLM prompt engineering"],
    live: null,
    source: "https://github.com/reagannwin/WebScrapingProject",
    featured: false,
  },
];
