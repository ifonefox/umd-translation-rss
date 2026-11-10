# UMD Translations RSS feed

An RSS feed of the latest releases from [UMD Translations](https://udonmanga.github.io/),
built from their `data/catalog.json` and hosted on GitHub Pages. The site serves only `feed.xml`.

Feed URL: `https://<your-username>.github.io/umd-translation-feed/feed.xml`

A GitHub Actions workflow rebuilds and redeploys it daily at midnight US Eastern
(`0 5 * * *` UTC, so 1am during daylight saving time).

## Setup

1. Create a **public** GitHub repo named `umd-translation-feed` and push this folder to `main`.
2. In the repo: Settings → Pages → Source: **GitHub Actions**.
3. Actions tab → "Build and deploy RSS feed" → Run workflow (or just push to `main`).
4. Add the feed URL to your RSS reader.

Local test: `python3 build_feed.py` writes `public/feed.xml`.
