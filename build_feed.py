#!/usr/bin/env python3
"""Build an Atom feed of UMD Translations releases from their catalog.json."""

import html
import json
import os
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote
from xml.etree import ElementTree as ET

SITE_URL = "https://udonmanga.github.io/"
CATALOG_URL = SITE_URL + "data/catalog.json"
OUT_DIR = Path(__file__).parent / "public"
ATOM_NS = "http://www.w3.org/2005/Atom"


def fetch_catalog() -> dict:
    req = urllib.request.Request(CATALOG_URL, headers={"User-Agent": "atom-feed-builder/1.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)


def rfc3339(ts: int) -> str:
    return datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def build_atom(catalog: dict, feed_url: str | None) -> ET.ElementTree:
    site = catalog.get("site", {})
    releases = catalog.get("latest_releases") or []
    if not releases:
        raise SystemExit("catalog has no latest_releases; refusing to publish an empty feed")
    releases = sorted(releases, key=lambda r: r.get("released_at") or 0, reverse=True)

    ET.register_namespace("", ATOM_NS)
    q = lambda tag: f"{{{ATOM_NS}}}{tag}"
    name = site.get("name") or "UMD Translations"

    feed = ET.Element(q("feed"))
    ET.SubElement(feed, q("title")).text = name
    if site.get("subtitle"):
        ET.SubElement(feed, q("subtitle")).text = site["subtitle"]
    ET.SubElement(feed, q("id")).text = feed_url or SITE_URL
    # Newest release time, so the feed only changes when something is released.
    ET.SubElement(feed, q("updated")).text = rfc3339(releases[0].get("released_at") or 0)
    ET.SubElement(feed, q("link"), href=SITE_URL, rel="alternate", type="text/html")
    if feed_url:
        ET.SubElement(feed, q("link"), href=feed_url, rel="self", type="application/atom+xml")
    ET.SubElement(ET.SubElement(feed, q("author")), q("name")).text = name

    for r in releases:
        title = f"{r['series_title']} – {r['chapter_label']}"
        if r.get("chapter_title"):
            title += f": {r['chapter_title']}"
        link = r.get("cubari_url") or SITE_URL

        parts = []
        if r.get("cover"):
            cover = SITE_URL + r["cover"].lstrip("/")
            parts.append(f'<p><img src="{html.escape(cover)}" alt="{html.escape(r["series_title"])}"/></p>')
        parts.append(f"<p><strong>{html.escape(r['series_title'])}</strong> — {html.escape(r['chapter_label'])}</p>")
        if r.get("chapter_title"):
            parts.append(f"<p>{html.escape(r['chapter_title'])}</p>")
        parts.append(f'<p><a href="{html.escape(link)}">Read on Cubari</a></p>')

        entry = ET.SubElement(feed, q("entry"))
        ET.SubElement(entry, q("title")).text = title
        # Tag URIs must be ASCII, so percent-encode ids like "turas_réalta_".
        entry_id = quote(f"{r['series_id']}:{r['chapter_number']}", safe="")
        ET.SubElement(entry, q("id")).text = f"tag:udonmanga.github.io,2024:{entry_id}"
        ET.SubElement(entry, q("link"), href=link, rel="alternate", type="text/html")
        ts = rfc3339(r.get("released_at") or 0)
        ET.SubElement(entry, q("updated")).text = ts
        ET.SubElement(entry, q("published")).text = ts
        ET.SubElement(entry, q("category"), term=r["series_title"])
        ET.SubElement(entry, q("content"), type="html").text = "\n".join(parts)

    ET.indent(feed)
    return ET.ElementTree(feed)


def feed_url_from_env() -> str | None:
    """FEED_URL if set, else derive the Pages URL from GITHUB_REPOSITORY (owner/repo)."""
    if os.environ.get("FEED_URL"):
        return os.environ["FEED_URL"]
    repo = os.environ.get("GITHUB_REPOSITORY")
    if repo and "/" in repo:
        owner, name = repo.split("/", 1)
        return f"https://{owner.lower()}.github.io/{name}/feed.xml"
    return None


def main() -> None:
    catalog = fetch_catalog()
    feed_url = feed_url_from_env()
    if not feed_url:
        print("warning: FEED_URL not set; feed will lack rel=self link", file=sys.stderr)
    tree = build_atom(catalog, feed_url)
    OUT_DIR.mkdir(exist_ok=True)
    tree.write(OUT_DIR / "feed.xml", encoding="utf-8", xml_declaration=True)
    (OUT_DIR / ".nojekyll").touch()
    print(f"wrote {OUT_DIR / 'feed.xml'} with {len(catalog['latest_releases'])} entries", file=sys.stderr)


if __name__ == "__main__":
    main()
