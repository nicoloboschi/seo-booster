"""SEO audit — builds the Hugo site and checks every page for SEO compliance."""

import subprocess
from pathlib import Path

from bs4 import BeautifulSoup


CHECKS = [
    "has_title_tag",
    "title_length",
    "has_meta_description",
    "description_length",
    "has_canonical",
    "has_og_title",
    "has_og_description",
    "has_og_type",
    "has_og_url",
    "has_og_image",
    "has_twitter_card",
    "has_json_ld",
    "has_h1",
    "single_h1",
    "heading_hierarchy",
    "has_lang",
]


def audit_html(build_dir: str = "public"):
    """Build Hugo and audit all HTML pages."""
    # Build the site
    print("  Building Hugo site...")
    result = subprocess.run(["hugo", "--minify"], capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  Hugo build failed:\n{result.stderr}")
        return

    print(f"  Built successfully.\n")

    build_path = Path(build_dir)
    html_files = list(build_path.rglob("*.html"))

    if not html_files:
        print("  No HTML files found in build output.")
        return

    total_issues = 0
    pages_with_issues = 0

    for html_file in sorted(html_files):
        rel_path = html_file.relative_to(build_path)

        # Skip pagination pages
        if "page" in str(rel_path) and rel_path.name == "index.html":
            parent = rel_path.parent.name
            if parent.isdigit():
                continue

        content = html_file.read_text()
        soup = BeautifulSoup(content, "html.parser")
        is_taxonomy = "tags/" in str(rel_path) or "categories/" in str(rel_path)
        issues = _check_page(soup, str(rel_path), is_taxonomy=is_taxonomy)

        if issues:
            pages_with_issues += 1
            total_issues += len(issues)
            print(f"  {rel_path}:")
            for issue in issues:
                print(f"    ✗ {issue}")
        else:
            print(f"  {rel_path}: OK")

    print(f"\n  Audit complete: {len(html_files)} pages, {pages_with_issues} with issues, {total_issues} total issues.")


def _check_page(soup: BeautifulSoup, path: str, is_taxonomy: bool = False) -> list[str]:
    """Run all SEO checks on a page."""
    issues = []

    # Title tag (relaxed min length for taxonomy pages — "AI", "LLM" etc. are inherently short)
    min_title_len = 10 if is_taxonomy else 20
    title_tag = soup.find("title")
    if not title_tag or not title_tag.string:
        issues.append("Missing <title> tag")
    elif title_tag.string:
        title_text = title_tag.string.strip()
        if len(title_text) < min_title_len:
            issues.append(f"Title too short ({len(title_text)} chars): '{title_text}'")
        elif len(title_text) > 70:
            issues.append(f"Title too long ({len(title_text)} chars, max 70)")

    # Meta description
    meta_desc = soup.find("meta", attrs={"name": "description"})
    if not meta_desc or not meta_desc.get("content"):
        issues.append("Missing meta description")
    else:
        desc = meta_desc["content"]
        if len(desc) < 120:
            issues.append(f"Meta description too short ({len(desc)} chars, min 120)")
        elif len(desc) > 165:
            issues.append(f"Meta description too long ({len(desc)} chars, max 165)")

    # Canonical URL
    canonical = soup.find("link", attrs={"rel": "canonical"})
    if not canonical or not canonical.get("href"):
        issues.append("Missing canonical URL")

    # Open Graph tags
    og_checks = {
        "og:title": "Missing og:title",
        "og:description": "Missing og:description",
        "og:type": "Missing og:type",
        "og:url": "Missing og:url",
        "og:image": "Missing og:image",
    }
    for prop, msg in og_checks.items():
        tag = soup.find("meta", attrs={"property": prop})
        if not tag or not tag.get("content"):
            issues.append(msg)

    # Twitter card
    twitter_card = soup.find("meta", attrs={"name": "twitter:card"})
    if not twitter_card or not twitter_card.get("content"):
        issues.append("Missing twitter:card meta tag")

    # JSON-LD structured data
    json_ld = soup.find("script", attrs={"type": "application/ld+json"})
    if not json_ld:
        issues.append("Missing JSON-LD structured data")

    # H1 tag (should exist and be unique on article pages)
    h1_tags = soup.find_all("h1")
    if not h1_tags:
        issues.append("Missing <h1> tag")
    elif len(h1_tags) > 1:
        issues.append(f"Multiple <h1> tags found ({len(h1_tags)})")

    # Heading hierarchy (no skipping levels)
    headings = soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6"])
    if headings:
        levels = [int(h.name[1]) for h in headings]
        for i in range(1, len(levels)):
            if levels[i] > levels[i - 1] + 1:
                issues.append(f"Heading hierarchy skip: h{levels[i-1]} → h{levels[i]}")
                break

    # HTML lang attribute
    html_tag = soup.find("html")
    if html_tag and not html_tag.get("lang"):
        issues.append("Missing lang attribute on <html> tag")

    return issues
