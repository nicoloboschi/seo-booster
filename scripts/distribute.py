"""Cross-post articles to Hashnode for backlinks and distribution.

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

def distribute_articles(content_dir: str, max_articles: int = 5, dry_run: bool = False):
    """Cross-post new articles to Hashnode.

    Only posts articles that haven't been distributed yet.
    Respects rate limits with delays between posts.
    """
    if not os.environ.get("HASHNODE_API_TOKEN"):
        print("HASHNODE_API_TOKEN not set in .env")
        return

    content_path = Path(content_dir)
    state = _load_state()

    # Find articles not yet distributed
    pending = []
    for md_file in sorted(content_path.glob("*.md")):
        if md_file.name.startswith("_"):
            continue
        slug = md_file.stem
        article_state = state.get(slug, {})
        if "hashnode" not in article_state.get("platforms", {}):
            pending.append((md_file, slug))

    if not pending:
        print("All articles already distributed to Hashnode.")
        return

    batch = pending[:max_articles]
    print(f"\nDistributing {len(batch)} articles to Hashnode ({len(pending)} total pending)...\n")

    for i, (md_file, slug) in enumerate(batch, 1):
        article = _parse_article(md_file)
        if not article:
            print(f"  [{i}/{len(batch)}] {slug}: SKIP (couldn't parse)")
            continue

        print(f"  [{i}/{len(batch)}] {article['title']}")

        if slug not in state:
            state[slug] = {"platforms": {}}

        if dry_run:
            print(f"    [DRY RUN] Would post to Hashnode: {article['canonical_url']}")
            continue

        result = post_to_hashnode(article)
        if result:
            state[slug]["platforms"]["hashnode"] = {
                "id": result["id"],
                "url": result["url"],
                "posted_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
            }
            print(f"    → hashnode: {result['url']}")
        else:
            print(f"    ✗ hashnode: failed")

        # Rate limit
        time.sleep(3)
        _save_state(state)

    _save_state(state)

    total_posted = sum(
        1 for v in state.values()
        if "hashnode" in v.get("platforms", {})
    )
    print(f"\nDone. {total_posted} total posts on Hashnode.")


def distribution_status(content_dir: str):
    """Print distribution status for all articles."""
    content_path = Path(content_dir)
    state = _load_state()

    articles = sorted(f.stem for f in content_path.glob("*.md") if not f.name.startswith("_"))

    print(f"\nDistribution status ({len(articles)} articles):\n")

    hashnode_count = 0

    for slug in articles:
        article_state = state.get(slug, {})
        platforms = article_state.get("platforms", {})

        hashnode = "✓" if "hashnode" in platforms else "✗"
        if "hashnode" in platforms:
            hashnode_count += 1

        print(f"  [{hashnode} hashnode] {slug}")

    print(f"\n  Hashnode: {hashnode_count}/{len(articles)}")
