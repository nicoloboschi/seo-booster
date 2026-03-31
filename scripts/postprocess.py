"""Post-process generated articles to ensure valid Hugo front matter and SEO compliance.

Includes AI content scrubbing, keyword density tracking, and content quality scoring.
"""

import json
import re
import unicodedata
from pathlib import Path

import yaml


REQUIRED_FIELDS = ["title", "description", "date", "tags", "keywords", "faq", "slug"]
MIN_DESCRIPTION_LENGTH = 140
MAX_DESCRIPTION_LENGTH = 165
MIN_FAQ_COUNT = 2

# --- AI Content Scrubbing ---

# Invisible Unicode characters that AI watermarking tools insert
INVISIBLE_CHARS = [
    "\u200b",  # zero-width space
    "\u200c",  # zero-width non-joiner
    "\u200d",  # zero-width joiner
    "\u2060",  # word joiner
    "\ufeff",  # BOM / zero-width no-break space
    "\u00ad",  # soft hyphen
    "\u200e",  # left-to-right mark
    "\u200f",  # right-to-left mark
    "\u2061",  # function application
    "\u2062",  # invisible times
    "\u2063",  # invisible separator
    "\u2064",  # invisible plus
]

# Words/phrases that scream "AI wrote this"
AI_TELL_PHRASES = [
    r"\bdelve[sd]?\b", r"\bdelving\b",
    r"\bleverage[sd]?\b", r"\bleveraging\b",
    r"\brobust\b", r"\bcomprehensive\b",
    r"\bcutting[\s-]edge\b", r"\bgame[\s-]changer\b",
    r"\brevolutionize[sd]?\b", r"\bparadigm\b", r"\bsynergy\b",
    r"\butilize[sd]?\b", r"\butilization\b",
    r"\bfurthermore\b", r"\bmoreover\b", r"\badditionally\b",
    r"\bnotably\b", r"\bimportantly\b",
    r"it'?s important to note", r"it'?s worth noting",
    r"it bears mentioning", r"a testament to",
    r"shed light on", r"a plethora of", r"myriad of",
    r"in the realm of", r"at the forefront",
    r"navigating the landscape", r"tapestry of",
    r"in today'?s (?:digital )?(?:age|landscape|world|era)",
    r"the rapidly evolving",
    r"in this article,? we'?ll",
    r"let'?s (?:dive|delve|explore)",
]

# Filler words to remove (with word boundaries)
AI_FILLER_WORDS = [
    r"\babsolutely\b", r"\bessentially\b", r"\bincredibl[ye]\b",
    r"\bfundamentally\b", r"\bundeniably\b", r"\bliterally\b",
    r"\bbasically\b",
]

# Vague quantifiers — flag but don't auto-remove (need context)
VAGUE_QUANTIFIERS = [
    r"\bsignificant(?:ly)?\b", r"\bsubstantial(?:ly)?\b",
    r"\bnumerous\b", r"\bvarious\b", r"\bvastly\b",
    r"\bcountless\b",
]

# Replacements for common AI phrases
AI_PHRASE_REPLACEMENTS = {
    "utilize": "use",
    "utilizes": "uses",
    "utilized": "used",
    "utilizing": "using",
    "utilization": "use",
    "leverage": "use",
    "leverages": "uses",
    "leveraged": "used",
    "leveraging": "using",
    "furthermore": "also",
    "moreover": "also",
    "additionally": "also",
    "it's important to note that": "",
    "it's worth noting that": "",
    "it is important to note that": "",
    "it is worth noting that": "",
    "it bears mentioning that": "",
    "in the realm of": "in",
    "at the forefront of": "leading",
    "a plethora of": "many",
    "myriad of": "many",
    "a myriad of": "many",
}


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

    # Step 2.5: AI content scrubbing (before field fixes so description gets scrubbed too)
    body, scrub_fixes = _scrub_ai_content(body)
    fixes.extend(scrub_fixes)

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

    # Step 6: Content quality scoring
    primary_kw = fm.get("keywords", [""])[0] if fm.get("keywords") else ""
    quality_warnings = _score_content_quality(body, primary_kw)
    fixes.extend(quality_warnings)

    # Step 7: Rebuild file
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

    # Replace ``` used as front matter closing delimiter with ---
    # This happens when LLMs generate ``` instead of --- to close YAML front matter
    lines = content.split("\n")
    if lines and lines[0].strip() == "---":
        for i in range(1, min(len(lines), 30)):
            if lines[i].strip() == "```":
                lines[i] = "---"
                fixes.append("Replaced ``` front matter closer with ---")
                break
            if lines[i].strip() == "---":
                break  # proper delimiter found
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


def _scrub_ai_content(body: str) -> tuple[str, list[str]]:
    """Remove AI watermarks, replace AI phrases, fix em-dashes. Returns (cleaned_body, fixes)."""
    fixes = []

    # 1. Remove invisible Unicode watermark characters
    invisible_count = 0
    for char in INVISIBLE_CHARS:
        count = body.count(char)
        if count > 0:
            invisible_count += count
            body = body.replace(char, "")
    if invisible_count:
        fixes.append(f"Removed {invisible_count} invisible Unicode watermark chars")

    # 2. Replace em-dashes with appropriate punctuation
    # Pattern: word — word  →  word, word (or semicolon for independent clauses)
    em_dash_count = body.count("—") + body.count("–")
    if em_dash_count:
        # Replace em-dash between spaces with comma
        body = re.sub(r"\s*[—–]\s*", ", ", body)
        # Clean up double commas or comma after period
        body = re.sub(r",\s*,", ",", body)
        body = re.sub(r"\.\s*,", ".", body)
        fixes.append(f"Replaced {em_dash_count} em-dashes with commas")

    # 3. Auto-replace known AI phrases with better alternatives
    replacement_count = 0
    for ai_phrase, replacement in AI_PHRASE_REPLACEMENTS.items():
        pattern = re.compile(re.escape(ai_phrase), re.IGNORECASE)
        matches = pattern.findall(body)
        if matches:
            replacement_count += len(matches)
            # Preserve case of first letter
            def _replace_preserving_case(m):
                original = m.group(0)
                if not replacement:
                    return ""
                if original[0].isupper():
                    return replacement[0].upper() + replacement[1:]
                return replacement
            body = pattern.sub(_replace_preserving_case, body)
    if replacement_count:
        fixes.append(f"Replaced {replacement_count} AI-tell phrases")

    # 4. Remove filler words (only when they start a sentence or follow a comma)
    filler_count = 0
    for filler in AI_FILLER_WORDS:
        # Match filler at start of sentence or after comma
        for pattern in [
            re.compile(rf"(?<=\. ){filler}\s*,?\s*", re.IGNORECASE),
            re.compile(rf"(?<=, ){filler}\s*,?\s*", re.IGNORECASE),
            re.compile(rf"^{filler}\s*,?\s*", re.IGNORECASE | re.MULTILINE),
        ]:
            matches = pattern.findall(body)
            if matches:
                filler_count += len(matches)
                body = pattern.sub("", body)
    if filler_count:
        fixes.append(f"Removed {filler_count} filler words")

    # 5. Clean up whitespace artifacts from removals
    body = re.sub(r"  +", " ", body)  # double spaces
    body = re.sub(r"\n{3,}", "\n\n", body)  # triple+ newlines
    body = re.sub(r" +\n", "\n", body)  # trailing spaces

    return body, fixes


def _score_content_quality(body: str, primary_keyword: str) -> list[str]:
    """Score content quality and return warnings for issues found.

    Scoring dimensions (composite score):
    - Humanity (30%): AI phrase density, filler count, sentence rhythm
    - Specificity (25%): vague quantifiers, concrete numbers/stats
    - Structure (20%): prose-to-list ratio, heading frequency, paragraph length
    - SEO (15%): keyword density, keyword in headings, featured snippet formatting
    - Readability (10%): sentence length, paragraph length
    """
    warnings = []

    # Strip code blocks for analysis (they skew metrics)
    analysis_text = re.sub(r"```[\s\S]*?```", "", body)
    # Strip markdown links but keep anchor text
    analysis_text = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", analysis_text)
    # Strip images
    analysis_text = re.sub(r"!\[([^\]]*)\]\([^\)]+\)", "", analysis_text)

    words = analysis_text.split()
    word_count = len(words)

    if word_count < 100:
        return warnings  # too short to score meaningfully

    # --- Humanity (30%) ---

    # Count remaining AI tell phrases (after scrubbing, some might be in headings etc.)
    ai_phrase_count = 0
    for pattern in AI_TELL_PHRASES:
        ai_phrase_count += len(re.findall(pattern, analysis_text, re.IGNORECASE))
    if ai_phrase_count > 0:
        warnings.append(f"QUALITY: {ai_phrase_count} AI-tell phrases still present after scrubbing")

    # Check sentence rhythm variety
    sentences = re.split(r'[.!?]+\s+', analysis_text)
    sentences = [s for s in sentences if len(s.split()) > 2]
    if len(sentences) >= 5:
        lengths = [len(s.split()) for s in sentences]
        avg_len = sum(lengths) / len(lengths)
        # Standard deviation of sentence lengths
        variance = sum((l - avg_len) ** 2 for l in lengths) / len(lengths)
        std_dev = variance ** 0.5
        if std_dev < 3:
            warnings.append(f"QUALITY: Monotonous sentence rhythm (std_dev={std_dev:.1f}, want >3). Mix short and long sentences")
        if avg_len > 22:
            warnings.append(f"QUALITY: Average sentence too long ({avg_len:.0f} words, target 15-20)")

    # --- Specificity (25%) ---

    # Count vague quantifiers
    vague_count = 0
    for pattern in VAGUE_QUANTIFIERS:
        vague_count += len(re.findall(pattern, analysis_text, re.IGNORECASE))
    if vague_count > 5:
        warnings.append(f"QUALITY: {vague_count} vague quantifiers found (significant, various, etc.). Use specific numbers")

    # Check for concrete numbers/statistics
    stat_count = len(re.findall(r"\d+(?:\.\d+)?%|\d{2,}", analysis_text))
    if stat_count < 2:
        warnings.append(f"QUALITY: Only {stat_count} statistics/numbers. Add 2-3 specific stats with source attribution")

    # --- Structure (20%) ---

    # Prose-to-list ratio
    list_lines = len(re.findall(r"^\s*[-*\d]+[.)]\s", body, re.MULTILINE))
    total_lines = len([l for l in body.split("\n") if l.strip()])
    if total_lines > 0:
        list_ratio = list_lines / total_lines
        if list_ratio > 0.6:
            warnings.append(f"QUALITY: Too many bullet lists ({list_ratio:.0%} of lines). Target 30-60% prose")
        elif list_ratio < 0.05 and word_count > 1000:
            warnings.append("QUALITY: No bullet lists or numbered lists. Add lists to improve scannability")

    # Heading frequency
    headings = re.findall(r"^#{2,3}\s", body, re.MULTILINE)
    if word_count > 500:
        words_per_heading = word_count / max(len(headings), 1)
        if words_per_heading > 450:
            warnings.append(f"QUALITY: Headings too sparse ({words_per_heading:.0f} words/heading, target 300-400)")

    # Long paragraphs
    paragraphs = re.split(r"\n\n+", analysis_text)
    long_paragraphs = [p for p in paragraphs if len(p.split()) > 80]
    if long_paragraphs:
        warnings.append(f"QUALITY: {len(long_paragraphs)} paragraphs exceed 80 words. Break them up")

    # --- SEO (15%) ---

    if primary_keyword and len(primary_keyword) > 2:
        # Keyword density
        kw_lower = primary_keyword.lower()
        text_lower = analysis_text.lower()
        kw_count = text_lower.count(kw_lower)
        density = (kw_count * len(kw_lower.split())) / max(word_count, 1)
        if density < 0.005:
            warnings.append(f"QUALITY: Keyword density too low ({density:.1%} for '{primary_keyword}'). Target 1-2%")
        elif density > 0.03:
            warnings.append(f"QUALITY: Keyword stuffing detected ({density:.1%} for '{primary_keyword}'). Target 1-2%")

        # Keyword in headings
        headings_text = " ".join(re.findall(r"^#{2,3}\s+(.+)$", body, re.MULTILINE)).lower()
        if kw_lower not in headings_text:
            warnings.append(f"QUALITY: Primary keyword '{primary_keyword}' not found in any H2/H3 heading")

    # --- Featured snippet check ---
    # Check if first H2 has a concise answer paragraph following it
    first_h2_match = re.search(r"^##\s+.+\n\n(.+?)(?:\n\n|\Z)", body, re.MULTILINE)
    if first_h2_match:
        first_answer = first_h2_match.group(1)
        answer_words = len(first_answer.split())
        if answer_words > 80:
            warnings.append(f"QUALITY: First paragraph after H2 is {answer_words} words. Keep to 40-60 for featured snippets")

    return warnings


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
