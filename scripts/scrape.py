"""Scrape content from RSS feeds, blogs, and news sources."""

import json
import hashlib
from datetime import datetime
from pathlib import Path

import feedparser
import httpx
import yaml
from bs4 import BeautifulSoup


def scrape_sources(config_path: str, output_dir: str):
    """Read sources config and scrape each one."""
    config_path = Path(config_path)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    with open(config_path) as f:
        config = yaml.safe_load(f)

    seen_file = output_path / "_seen.json"
    seen = json.loads(seen_file.read_text()) if seen_file.exists() else {}

    for source in config.get("sources", []):
        source_type = source.get("type", "rss")
        print(f"Scraping [{source_type}] {source['name']}...")

        if source_type == "rss":
            items = _scrape_rss(source["url"])
        elif source_type == "web":
            items = _scrape_web(source["url"], source.get("selector", "article"))
        elif source_type == "local":
            items = _scrape_local(source["path"], source.get("glob", "*.md"))
        else:
            print(f"  Unknown source type: {source_type}")
            continue

        new_count = 0
        for item in items:
            item_id = hashlib.sha256(item["url"].encode()).hexdigest()[:12]
            if item_id in seen:
                continue

            item["source"] = source["name"]
            item["scraped_at"] = datetime.now().isoformat()

            item_file = output_path / f"{item_id}.json"
            item_file.write_text(json.dumps(item, indent=2))
            seen[item_id] = item["url"]
            new_count += 1

        print(f"  → {new_count} new items from {source['name']}")

    seen_file.write_text(json.dumps(seen, indent=2))


def _scrape_rss(url: str) -> list[dict]:
    """Parse RSS feed and extract articles."""
    feed = feedparser.parse(url)
    items = []
    for entry in feed.entries:
        content = ""
        if hasattr(entry, "content"):
            content = entry.content[0].value
        elif hasattr(entry, "summary"):
            content = entry.summary

        # Strip HTML
        if content:
            soup = BeautifulSoup(content, "html.parser")
            content = soup.get_text(separator="\n", strip=True)

        items.append({
            "title": entry.get("title", ""),
            "url": entry.get("link", ""),
            "content": content,
            "published": entry.get("published", ""),
        })
    return items


def _scrape_web(url: str, selector: str) -> list[dict]:
    """Scrape a web page and extract content from a CSS selector."""
    resp = httpx.get(url, follow_redirects=True, timeout=30)
    soup = BeautifulSoup(resp.text, "html.parser")

    items = []
    seen_urls = set()
    for el in soup.select(selector):
        title_el = el.select_one("h1, h2, h3, a")

        # If the selected element is itself an <a>, use its href directly
        if el.name == "a" and el.get("href"):
            link = el["href"]
        else:
            link_el = el.select_one("a[href]")
            link = link_el["href"] if link_el else url

        title = title_el.get_text(strip=True) if title_el else ""
        if not link.startswith("http"):
            from urllib.parse import urljoin
            link = urljoin(url, link)

        # Deduplicate (multiple <a> tags can point to the same article)
        if link in seen_urls:
            continue
        seen_urls.add(link)

        content = el.get_text(separator="\n", strip=True)

        # Follow link to fetch full article body if listing content is thin
        if len(content) < 200 and link != url:
            try:
                article_resp = httpx.get(link, follow_redirects=True, timeout=30)
                article_soup = BeautifulSoup(article_resp.text, "html.parser")
                # Try common article body selectors
                body_el = (
                    article_soup.select_one("article")
                    or article_soup.select_one("[class*='prose']")
                    or article_soup.select_one("main")
                )
                if body_el:
                    content = body_el.get_text(separator="\n", strip=True)
                    if not title:
                        h1 = article_soup.select_one("h1")
                        title = h1.get_text(strip=True) if h1 else title
            except Exception:
                pass  # Keep listing-page content as fallback

        items.append({
            "title": title,
            "url": link,
            "content": content,
            "published": "",
        })
    return items


def _scrape_local(path: str, glob_pattern: str) -> list[dict]:
    """Read local markdown/text files as source content."""
    base = Path(path)
    items = []
    for f in base.glob(glob_pattern):
        content = f.read_text()
        # Extract title from first heading
        title = ""
        for line in content.split("\n"):
            if line.startswith("# "):
                title = line.lstrip("# ").strip()
                break
            if line.startswith("title:"):
                title = line.split(":", 1)[1].strip().strip("\"'")
                break

        items.append({
            "title": title or f.stem,
            "url": f"local://{f}",
            "content": content,
            "published": "",
        })
    return items
