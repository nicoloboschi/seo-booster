"""One-off repair: reconstruct YAML front matter for article files that were
generated without any (body-only markdown). These files had an empty `:slug`,
so Hugo collided them all at /articles/, making them invisible to Google and
clobbering the section landing page.

For each broken file it rebuilds front matter from:
  - the filename stem  -> slug (fixes the URL collision)
  - data/keywords.yaml -> primary/related keywords, cluster, role
  - the first body paragraph -> description
  - the in-body "Frequently Asked Questions" block -> faq: (for FAQ schema),
    which is then removed from the body to match healthy articles
  - git first-commit date -> date, today -> lastmod

Run: uv run python scripts/fix_missing_frontmatter.py [--apply]
Without --apply it does a dry run and prints what it would change.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
ARTICLES = ROOT / "content" / "articles"
KEYWORDS_YAML = ROOT / "data" / "keywords.yaml"
TODAY = "2026-06-09"

# Acronyms / proper nouns to keep cased correctly when title-casing a keyword.
ACRONYMS = {
    "ai": "AI", "llm": "LLM", "llms": "LLMs", "ram": "RAM", "gpu": "GPU",
    "hbm": "HBM", "rag": "RAG", "api": "API", "node": "Node", "js": "JS",
    "nodejs": "Node.js", "vram": "VRAM", "url": "URL", "faq": "FAQ",
    "chatgpt": "ChatGPT", "deepseek": "DeepSeek", "dify": "Dify",
    "github": "GitHub", "reddit": "Reddit", "ios": "iOS",
}


def title_from_keyword(primary: str) -> str:
    words = []
    for w in primary.split():
        lw = w.lower()
        if lw in ACRONYMS:
            words.append(ACRONYMS[lw])
        elif w.isupper():
            words.append(w)
        else:
            words.append(w.capitalize())
    return " ".join(words)


def first_commit_date(path: Path) -> str:
    try:
        out = subprocess.run(
            ["git", "log", "--diff-filter=A", "--follow", "--format=%ad",
             "--date=short", "--", str(path)],
            cwd=ROOT, capture_output=True, text=True, check=True,
        ).stdout.strip().splitlines()
        if out:
            return out[-1]
    except subprocess.CalledProcessError:
        pass
    return TODAY


def extract_first_paragraph(body: str) -> str:
    for block in body.split("\n\n"):
        b = block.strip()
        if not b or b.startswith("#") or b.startswith("---"):
            continue
        # strip markdown emphasis and links -> plain text
        b = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", b)
        b = re.sub(r"[*_`]", "", b)
        b = " ".join(b.split())
        return b
    return ""


def extract_faq(body: str) -> tuple[list[dict], str]:
    """Pull the trailing FAQ section into a list and return (faq, body_without_faq)."""
    m = re.search(r"\n#+\s*(?:Frequently Asked Questions|FAQ)\b.*", body,
                  re.IGNORECASE | re.DOTALL)
    if not m:
        return [], body
    faq_block = body[m.start():]
    remainder = body[: m.start()].rstrip()
    # split into ### question \n answer pairs
    faq = []
    for qm in re.finditer(r"\n#{3,}\s*(.+?)\n+([^\n#][^\n]*(?:\n(?!#).*)*)",
                          "\n" + faq_block):
        question = qm.group(1).strip().rstrip("?") + "?"
        answer = " ".join(qm.group(2).split())
        answer = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", answer)
        answer = re.sub(r"[*_`]", "", answer)
        if answer:
            faq.append({"question": question, "answer": answer})
    return faq, remainder


def truncate(text: str, n: int = 155) -> str:
    if len(text) <= n:
        return text
    cut = text[:n].rsplit(" ", 1)[0]
    return cut.rstrip(".,;:") + "..."


def main() -> int:
    apply = "--apply" in sys.argv
    kw = yaml.safe_load(KEYWORDS_YAML.read_text())["keywords"]
    by_slug = {e["slug"]: e for e in kw if e.get("slug")}

    broken = [p for p in sorted(ARTICLES.glob("*.md"))
              if p.name != "_index.md" and not p.read_text().startswith("---")]
    print(f"Found {len(broken)} article(s) missing front matter\n")

    for path in broken:
        slug = path.stem
        body = path.read_text()
        entry = by_slug.get(slug, {})
        primary = entry.get("primary") or slug.replace("-", " ")
        related = entry.get("related") or []

        title = title_from_keyword(primary)
        description = truncate(extract_first_paragraph(body))
        faq, new_body = extract_faq(body)
        date = first_commit_date(path)

        keywords = [primary] + [r for r in related if r.lower() != primary.lower()]
        tags = related[:6] if related else [primary]

        fm: dict = {
            "title": title,
            "description": description,
            "date": date,
            "lastmod": TODAY,
            "tags": tags,
            "keywords": keywords,
        }
        if entry.get("cluster"):
            fm["cluster"] = entry["cluster"]
        if entry.get("role"):
            fm["role"] = entry["role"]
        if faq:
            fm["faq"] = faq
        fm["slug"] = slug

        front = yaml.safe_dump(fm, sort_keys=False, allow_unicode=True,
                               default_flow_style=False, width=1000)
        new_content = f"---\n{front}---\n\n{new_body.lstrip()}\n"

        print(f"- {path.name}: title={title!r} faq={len(faq)} date={date} "
              f"kw={'yes' if entry else 'NO keywords.yaml entry'}")
        if apply:
            path.write_text(new_content)

    print(f"\n{'APPLIED' if apply else 'DRY RUN (use --apply to write)'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
