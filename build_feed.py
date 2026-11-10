#!/usr/bin/env python3
"""Build an RSS feed of UMD Translations releases from their catalog.json."""

import html
import json
import os
import sys
import urllib.request
from email.utils import formatdate
from pathlib import Path
from xml.etree import ElementTree as ET

SITE_URL = "https://udonmanga.github.io/"
CATALOG_URL = SITE_URL + "data/catalog.json"
OUT_DIR = Path(__file__).parent / "public"
ATOM_NS = "http://www.w3.org/2005/Atom"


def fetch_catalog() -> dict:
    req = urllib.request.Request(CATALOG_URL, headers={"User-Agent": "rss-feed-builder/1.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)


def rfc822(ts: int) -> str:
    return formatdate(ts, usegmt=True)


def build_rss(catalog: dict, feed_url: str | None) -> ET.ElementTree:
    site = catalog.get("site", {})
    releases = catalog.get("latest_releases") or []
    if not releases:
        raise SystemExit("catalog has no latest_releases; refusing to publish an empty feed")

    ET.register_namespace("atom", ATOM_NS)
    rss = ET.Element("rss", version="2.0")
    channel = ET.SubElement(rss, "channel")
    ET.SubElement(channel, "title").text = site.get("name") or "UMD Translations"
    ET.SubElement(channel, "link").text = SITE_URL
    ET.SubElement(channel, "description").text = site.get("subtitle") or "Latest releases"
    ET.SubElement(channel, "language").text = "en"
    ET.SubElement(channel, "lastBuildDate").text = rfc822(catalog.get("generated_at") or 0)
    if feed_url:
        ET.SubElement(channel, f"{{{ATOM_NS}}}link", href=feed_url, rel="self", type="application/rss+xml")

    for r in sorted(releases, key=lambda r: r.get("released_at") or 0, reverse=True):
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

        item = ET.SubElement(channel, "item")
        ET.SubElement(item, "title").text = title
        ET.SubElement(item, "link").text = link
        ET.SubElement(item, "guid", isPermaLink="false").text = f"{r['series_id']}:{r['chapter_number']}"
        ET.SubElement(item, "pubDate").text = rfc822(r.get("released_at") or 0)
        ET.SubElement(item, "category").text = r["series_title"]
        ET.SubElement(item, "description").text = "\n".join(parts)

    ET.indent(rss)
    return ET.ElementTree(rss)


def main() -> None:
    catalog = fetch_catalog()
    tree = build_rss(catalog, os.environ.get("FEED_URL"))
    OUT_DIR.mkdir(exist_ok=True)
    tree.write(OUT_DIR / "feed.xml", encoding="utf-8", xml_declaration=True)
    (OUT_DIR / ".nojekyll").touch()
    print(f"wrote {OUT_DIR / 'feed.xml'} with {len(catalog['latest_releases'])} items", file=sys.stderr)


if __name__ == "__main__":
    main()
