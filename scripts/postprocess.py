"""Post-process generated articles to ensure valid Hugo front matter and SEO compliance."""

import json
import re
from pathlib import Path

import yaml


REQUIRED_FIELDS = ["title", "description", "date", "tags", "keywords", "faq", "slug"]
MIN_DESCRIPTION_LENGTH = 140
MAX_DESCRIPTION_LENGTH = 165
MIN_FAQ_COUNT = 2


def postprocess_article(file_path: Path) -> list[str]:
    """Validate and fix a single article's front matter. Returns list of fixes applied."""
    content = file_path.read_text()
    fixes = []

    # Step 1: Extract and normalize front matter delimiters
    content, delimiter_fixes = _fix_delimiters(content)
    fixes.extend(delimiter_fixes)

    # Step 2: Parse front matter
    fm_match = re.match(r"^---\n(.*?\n)---\n(.*)$", content, re.DOTALL)
    if not fm_match:
        fixes.append("CRITICAL: Could not parse front matter even after fixing delimiters")
        file_path.write_text(content)
        return fixes

    fm_text = fm_match.group(1)
    body = fm_match.group(2)

    try:
        fm = yaml.safe_load(fm_text)
    except yaml.YAMLError as e:
        fixes.append(f"CRITICAL: Invalid YAML: {e}")
        file_path.write_text(content)
        return fixes

    if not isinstance(fm, dict):
        fixes.append("CRITICAL: Front matter is not a dict")
        file_path.write_text(content)
        return fixes

    # Step 3: Fix individual fields
    slug = file_path.stem

    if "slug" not in fm or not fm["slug"]:
        fm["slug"] = slug
        fixes.append(f"Added missing slug: {slug}")

    if "title" not in fm or not fm["title"]:
        fm["title"] = slug.replace("-", " ").title()
        fixes.append(f"Generated title from slug")

    if "date" not in fm or not fm["date"]:
        fm["date"] = "2026-03-24"
        fixes.append("Added missing date")

    if "tags" not in fm or not isinstance(fm["tags"], list):
        fm["tags"] = ["AI memory", "agents"]
        fixes.append("Added default tags")

    if "keywords" not in fm or not isinstance(fm["keywords"], list):
        fm["keywords"] = [slug.replace("-", " ")]
        fixes.append("Added keywords from slug")

    # Fix description length
    desc = fm.get("description", "")
    if not desc or len(desc) < MIN_DESCRIPTION_LENGTH:
        # Try to generate from title + keywords
        kw_str = ", ".join(fm.get("keywords", [])[:2])
        title = fm["title"]
        desc = f"{title}. Learn about {kw_str} with practical examples, code snippets, and architectural insights for production systems."
        if len(desc) > MAX_DESCRIPTION_LENGTH:
            desc = desc[:MAX_DESCRIPTION_LENGTH - 3] + "..."
        fm["description"] = desc
        fixes.append(f"Extended description to {len(desc)} chars")
    elif len(desc) > MAX_DESCRIPTION_LENGTH:
        fm["description"] = desc[:MAX_DESCRIPTION_LENGTH - 3] + "..."
        fixes.append(f"Truncated description to {MAX_DESCRIPTION_LENGTH} chars")

    # Fix FAQ — extract from body if missing from front matter
    if "faq" not in fm or not isinstance(fm["faq"], list) or len(fm["faq"]) < MIN_FAQ_COUNT:
        body_faq = _extract_faq_from_body(body)
        if body_faq and len(body_faq) >= MIN_FAQ_COUNT:
            fm["faq"] = body_faq
            fixes.append(f"Extracted {len(body_faq)} FAQ items from article body")
        elif "faq" not in fm or not fm["faq"]:
            # Generate minimal FAQ from title/keywords
            primary_kw = fm["keywords"][0] if fm["keywords"] else fm["title"]
            fm["faq"] = [
                {"question": f"What is {primary_kw}?",
                 "answer": f"{primary_kw} refers to the techniques and systems described in this article. See the full article for detailed explanations and examples."},
                {"question": f"Why does {primary_kw} matter for AI agents?",
                 "answer": f"Understanding {primary_kw} is essential for building production AI systems that maintain context, learn from interactions, and provide reliable results."},
            ]
            fixes.append("Generated placeholder FAQ (should be improved)")

    # Step 4: Remove duplicate FAQ section from body if it's now in front matter
    if fm.get("faq"):
        body = _remove_body_faq_section(body)

    # Step 5: Demote H1 headings in body to H2 (template renders H1 from title)
    body, h1_fixes = _demote_h1(body)
    fixes.extend(h1_fixes)

    # Step 6: Rebuild file
    # Use yaml.dump for front matter to ensure valid YAML
    fm_yaml = yaml.dump(fm, default_flow_style=False, allow_unicode=True, sort_keys=False, width=200)
    new_content = f"---\n{fm_yaml}---\n{body}"

    file_path.write_text(new_content)
    return fixes


def _fix_delimiters(content: str) -> tuple[str, list[str]]:
    """Fix front matter delimiters — handle missing ---, backticks, etc."""
    fixes = []
    lines = content.split("\n")

    # Remove leading backticks (```yaml, ```markdown, etc.)
    while lines and lines[0].strip().startswith("```"):
        lines.pop(0)
        fixes.append("Removed leading backtick fence")

    # Remove trailing backticks
    while lines and lines[-1].strip() == "```":
        lines.pop()
        fixes.append("Removed trailing backtick fence")

    content = "\n".join(lines)

    # Check for opening ---
    if not content.startswith("---"):
        # Check if first line looks like YAML (key: value)
        first_line = content.split("\n")[0].strip()
        if re.match(r'^[a-z_]+\s*:', first_line) or first_line.startswith("title:"):
            content = "---\n" + content
            fixes.append("Added missing opening ---")

    # Find where front matter ends — look for the closing ---
    lines = content.split("\n")
    if lines[0].strip() == "---":
        found_close = False
        for i in range(1, min(len(lines), 50)):  # Front matter shouldn't be more than 50 lines
            line = lines[i].strip()
            if line == "---":
                found_close = True
                # Check if next line is a backtick fence and remove it
                if i + 1 < len(lines) and lines[i + 1].strip().startswith("```"):
                    lines.pop(i + 1)
                    fixes.append("Removed backtick fence after closing ---")
                break
            # If we hit a markdown heading or empty line after what looks like YAML ended
            if line.startswith("## ") or line.startswith("# "):
                # Insert --- before this line
                lines.insert(i, "---")
                fixes.append("Inserted missing closing --- before article body")
                found_close = True
                break

        if not found_close:
            # Try to find where YAML ends by looking for the slug field (usually last)
            for i in range(1, min(len(lines), 50)):
                if lines[i].strip().startswith("slug:"):
                    lines.insert(i + 1, "---")
                    fixes.append("Inserted closing --- after slug field")
                    found_close = True
                    break

        content = "\n".join(lines)

    # Handle duplicate front matter blocks (some models output two)
    parts = content.split("---")
    if len(parts) >= 5:  # More than 2 --- pairs means duplicates
        # Keep only first front matter block + body
        fm_content = parts[1]
        body_parts = parts[2:]
        # Find the actual body (first part that contains markdown)
        body = ""
        for part in body_parts:
            if part.strip() and (part.strip().startswith("#") or len(part.strip()) > 100):
                body = part
                break
        if not body:
            body = "\n".join(body_parts)
        content = f"---{fm_content}---\n{body}"
        fixes.append("Removed duplicate front matter block")

    return content, fixes


def _extract_faq_from_body(body: str) -> list[dict]:
    """Extract FAQ items from the article body markdown."""
    faq_items = []

    # Look for FAQ section
    faq_match = re.search(r"#{2,3}\s*(?:FAQ|Frequently Asked Questions).*?\n(.*?)(?=\n#{1,2}\s|\Z)",
                          body, re.DOTALL | re.IGNORECASE)
    if not faq_match:
        return []

    faq_text = faq_match.group(1)

    # Pattern: **Question?** or ### Question? followed by answer
    # Try bold questions first
    bold_matches = re.findall(
        r"\*\*(.+?\?)\*\*\s*\n\s*(.+?)(?=\n\s*\*\*|\n\s*#{2,}|\Z)",
        faq_text, re.DOTALL
    )
    for q, a in bold_matches:
        faq_items.append({
            "question": q.strip(),
            "answer": a.strip().replace("\n", " "),
        })

    # Try heading questions
    if not faq_items:
        heading_matches = re.findall(
            r"#{3,4}\s*(.+?\?)\s*\n\s*(.+?)(?=\n\s*#{3,}|\Z)",
            faq_text, re.DOTALL
        )
        for q, a in heading_matches:
            faq_items.append({
                "question": q.strip(),
                "answer": a.strip().replace("\n", " "),
            })

    return faq_items


def _demote_h1(body: str) -> tuple[str, list[str]]:
    """Demote H1 headings to H2 in the article body (template renders H1 from title)."""
    fixes = []
    lines = body.split("\n")
    new_lines = []
    for line in lines:
        if re.match(r"^# (?!#)", line):
            new_lines.append("#" + line)  # # Title → ## Title
            fixes.append(f"Demoted H1 to H2: {line.strip()[:50]}")
        else:
            new_lines.append(line)
    return "\n".join(new_lines), fixes


def _remove_body_faq_section(body: str) -> str:
    """Remove FAQ section from body since it's in front matter for schema markup."""
    # Don't remove — keep it visible to users too, just ensure the structured data is in front matter
    return body


def postprocess_all(content_dir: str) -> dict:
    """Post-process all articles in a directory."""
    content_path = Path(content_dir)
    results = {}

    for md_file in sorted(content_path.glob("*.md")):
        if md_file.name.startswith("_"):
            continue

        fixes = postprocess_article(md_file)
        results[md_file.name] = fixes

        if fixes:
            print(f"  {md_file.name}: {len(fixes)} fixes")
            for fix in fixes:
                print(f"    - {fix}")
        else:
            print(f"  {md_file.name}: OK")

    return results
