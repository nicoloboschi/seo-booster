"""Cross-post articles to Dev.to and Hashnode for backlinks and distribution.

Both platforms support canonical URLs, so Google credits the original site.
Dev.to: REST API, nofollow body links but canonical passes authority.
Hashnode: GraphQL API, dofollow body links + canonical.
"""

import json
import os
import re
import time
from pathlib import Path

import httpx
import yaml
from dotenv import load_dotenv

load_dotenv()

SITE_URL = "https://aiagentmemory.org"
DISTRIBUTION_STATE_FILE = Path("data/_distributed.json")

# Max tags per platform
DEVTO_MAX_TAGS = 4
HASHNODE_MAX_TAGS = 5


def _load_state() -> dict:
    """Load distribution state — tracks which articles have been posted where."""
    if DISTRIBUTION_STATE_FILE.exists():
        return json.loads(DISTRIBUTION_STATE_FILE.read_text())
    return {}


def _save_state(state: dict):
    DISTRIBUTION_STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    DISTRIBUTION_STATE_FILE.write_text(json.dumps(state, indent=2))


def _parse_article(file_path: Path) -> dict | None:
    """Parse a Hugo markdown article into front matter + body."""
    content = file_path.read_text()
    fm_match = re.match(r"^---\n(.*?\n)---\n(.*)$", content, re.DOTALL)
    if not fm_match:
        return None

    try:
        fm = yaml.safe_load(fm_match.group(1))
    except yaml.YAMLError:
        return None

    if not isinstance(fm, dict):
        return None

    body = fm_match.group(2).strip()

    # Convert internal links to absolute URLs
    body = re.sub(
        r'\[([^\]]+)\]\(/articles/([^)]+)/?\)',
        rf'[\1]({SITE_URL}/articles/\2/)',
        body,
    )

    return {
        "title": fm.get("title", ""),
        "description": fm.get("description", ""),
        "body": body,
        "tags": fm.get("tags", []),
        "slug": fm.get("slug", file_path.stem),
        "canonical_url": f"{SITE_URL}/articles/{fm.get('slug', file_path.stem)}/",
    }


def _sanitize_devto_tag(tag: str) -> str:
    """Dev.to tags: lowercase, alphanumeric + hyphens, max 30 chars."""
    tag = tag.lower().strip()
    tag = re.sub(r"[^a-z0-9\s-]", "", tag)
    tag = re.sub(r"\s+", "", tag)
    return tag[:30]


# --- Dev.to ---

def post_to_devto(article: dict) -> dict | None:
    """Publish an article to Dev.to. Returns the response data or None on failure."""
    api_key = os.environ.get("DEVTO_API_KEY")
    if not api_key:
        print("    DEVTO_API_KEY not set, skipping Dev.to")
        return None

    tags = [_sanitize_devto_tag(t) for t in article["tags"][:DEVTO_MAX_TAGS]]
    # Filter empty tags
    tags = [t for t in tags if t]

    payload = {
        "article": {
            "title": article["title"],
            "body_markdown": article["body"],
            "published": True,
            "canonical_url": article["canonical_url"],
            "tags": tags,
            "description": article["description"][:100] if article["description"] else "",
        }
    }

    try:
        resp = httpx.post(
            "https://dev.to/api/articles",
            json=payload,
            headers={
                "api-key": api_key,
                "Content-Type": "application/json",
            },
            timeout=30,
        )
        if resp.status_code == 201:
            data = resp.json()
            return {
                "id": data.get("id"),
                "url": data.get("url"),
                "platform": "devto",
            }
        else:
            print(f"    Dev.to error {resp.status_code}: {resp.text[:200]}")
            return None
    except Exception as e:
        print(f"    Dev.to request failed: {e}")
        return None


# --- Hashnode ---

def post_to_hashnode(article: dict) -> dict | None:
    """Publish an article to Hashnode via GraphQL API. Returns response data or None."""
    token = os.environ.get("HASHNODE_API_TOKEN")
    publication_id = os.environ.get("HASHNODE_PUBLICATION_ID")

    if not token:
        print("    HASHNODE_API_TOKEN not set, skipping Hashnode")
        return None
    if not publication_id:
        print("    HASHNODE_PUBLICATION_ID not set, skipping Hashnode")
        return None

    tags_input = []
    for tag in article["tags"][:HASHNODE_MAX_TAGS]:
        # Hashnode tags are objects with slug and name
        slug = re.sub(r"[^a-z0-9-]", "", tag.lower().replace(" ", "-"))
        tags_input.append({"slug": slug, "name": tag})

    query = """
    mutation PublishPost($input: PublishPostInput!) {
        publishPost(input: $input) {
            post {
                id
                url
                title
            }
        }
    }
    """

    variables = {
        "input": {
            "title": article["title"],
            "contentMarkdown": article["body"],
            "publicationId": publication_id,
            "originalArticleURL": article["canonical_url"],
            "tags": tags_input,
            "subtitle": article["description"][:150] if article["description"] else "",
        }
    }

    try:
        resp = httpx.post(
            "https://gql.hashnode.com",
            json={"query": query, "variables": variables},
            headers={
                "Authorization": token,
                "Content-Type": "application/json",
            },
            timeout=30,
        )
        data = resp.json()

        if "errors" in data:
            print(f"    Hashnode error: {data['errors'][0].get('message', str(data['errors']))}")
            return None

        post_data = data.get("data", {}).get("publishPost", {}).get("post", {})
        if post_data:
            return {
                "id": post_data.get("id"),
                "url": post_data.get("url"),
                "platform": "hashnode",
            }
        return None
    except Exception as e:
        print(f"    Hashnode request failed: {e}")
        return None


# --- Main distribution logic ---

def distribute_articles(content_dir: str, platforms: list[str] | None = None,
                        max_articles: int = 5, dry_run: bool = False):
    """Cross-post new articles to Dev.to and Hashnode.

    Only posts articles that haven't been distributed yet.
    Respects rate limits with delays between posts.
    """
    if platforms is None:
        platforms = ["devto", "hashnode"]

    content_path = Path(content_dir)
    state = _load_state()

    # Find articles not yet distributed
    pending = []
    for md_file in sorted(content_path.glob("*.md")):
        if md_file.name.startswith("_"):
            continue
        slug = md_file.stem
        article_state = state.get(slug, {})

        # Check if already posted to all requested platforms
        posted_platforms = set(article_state.get("platforms", {}).keys())
        missing = set(platforms) - posted_platforms
        if missing:
            pending.append((md_file, slug, missing))

    if not pending:
        print("All articles already distributed to all platforms.")
        return

    batch = pending[:max_articles]
    print(f"\nDistributing {len(batch)} articles ({len(pending)} total pending)...\n")

    for i, (md_file, slug, missing_platforms) in enumerate(batch, 1):
        article = _parse_article(md_file)
        if not article:
            print(f"  [{i}/{len(batch)}] {slug}: SKIP (couldn't parse)")
            continue

        print(f"  [{i}/{len(batch)}] {article['title']}")

        if slug not in state:
            state[slug] = {"platforms": {}}

        if dry_run:
            for platform in missing_platforms:
                print(f"    [DRY RUN] Would post to {platform}: {article['canonical_url']}")
            continue

        for platform in missing_platforms:
            if platform == "devto":
                result = post_to_devto(article)
            elif platform == "hashnode":
                result = post_to_hashnode(article)
            else:
                print(f"    Unknown platform: {platform}")
                continue

            if result:
                state[slug]["platforms"][platform] = {
                    "id": result["id"],
                    "url": result["url"],
                    "posted_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
                }
                print(f"    → {platform}: {result['url']}")
            else:
                print(f"    ✗ {platform}: failed")

            # Rate limit: wait between posts
            time.sleep(3)

        _save_state(state)

    _save_state(state)

    total_posted = sum(
        len(v.get("platforms", {}))
        for v in state.values()
    )
    print(f"\nDone. {total_posted} total posts across all platforms.")


def distribution_status(content_dir: str):
    """Print distribution status for all articles."""
    content_path = Path(content_dir)
    state = _load_state()

    articles = sorted(f.stem for f in content_path.glob("*.md") if not f.name.startswith("_"))

    print(f"\nDistribution status ({len(articles)} articles):\n")

    devto_count = 0
    hashnode_count = 0

    for slug in articles:
        article_state = state.get(slug, {})
        platforms = article_state.get("platforms", {})

        devto = "✓" if "devto" in platforms else "✗"
        hashnode = "✓" if "hashnode" in platforms else "✗"

        if "devto" in platforms:
            devto_count += 1
        if "hashnode" in platforms:
            hashnode_count += 1

        print(f"  [{devto} devto] [{hashnode} hashnode] {slug}")

    print(f"\n  Dev.to: {devto_count}/{len(articles)}")
    print(f"  Hashnode: {hashnode_count}/{len(articles)}")
