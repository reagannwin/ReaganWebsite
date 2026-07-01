# ReaganWebsite

My personal resume/portfolio site — the home base for all of my full stack web
side projects.

**Stack:** plain HTML/CSS/JS. No build step, no dependencies — just push and
it deploys to GitHub Pages.

## Adding a new project

All projects live in [`projects.js`](projects.js). Add one object to the
`PROJECTS` array and push:

```js
{
  title: "My New App",
  blurb: "What it does, in a sentence or three.",
  stack: ["React", "Node.js", "PostgreSQL"],
  live: "https://my-new-app.example.com",   // or null to hide the link
  source: "https://github.com/reagannwin/my-new-app", // or null
  featured: false,  // true = highlighted full-width card
}
```

The site renders the list automatically — no other files need to change.

## Running locally

Open `index.html` in a browser, or serve it:

```sh
python3 -m http.server 8000
# → http://localhost:8000
```

## Deploying (one-time setup)

The site auto-deploys on every push to `main` via
[`.github/workflows/deploy.yml`](.github/workflows/deploy.yml). To enable it:

1. On GitHub, go to **Settings → Pages**.
2. Under **Build and deployment → Source**, choose **GitHub Actions**.

After the next push to `main`, the site will be live at
`https://reagannwin.github.io/reaganwebsite/`.

> Tip: for hosting the projects themselves, deploy each app on its own
> (Vercel, Render, Railway, Fly.io, etc.) and link to it from `projects.js` —
> this site is the hub that ties them all together.

## Updating resume content

Experience, skills, and education are in plain HTML sections in
[`index.html`](index.html) — edit them directly.
