"""Fetch and analyze SEO stats from Google Search Console."""

import json
from datetime import datetime, timedelta
from pathlib import Path

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build


SCOPES = ["https://www.googleapis.com/auth/webmasters.readonly"]


def _get_gsc_service(credentials_path: str):
    """Authenticate and return GSC service."""
    creds = None
    token_path = Path(credentials_path).parent / "gsc-token.json"

    if token_path.exists():
        creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
            creds = flow.run_local_server(port=0)
        token_path.write_text(creds.to_json())

    return build("searchconsole", "v1", credentials=creds)


def fetch_seo_stats(credentials_path: str, site_url: str, days: int) -> dict:
    """Fetch performance data from Google Search Console."""
    service = _get_gsc_service(credentials_path)

    end_date = datetime.now() - timedelta(days=3)  # GSC has ~3 day delay
    start_date = end_date - timedelta(days=days)

    # Fetch page-level stats
    page_response = service.searchanalytics().query(
        siteUrl=site_url,
        body={
            "startDate": start_date.strftime("%Y-%m-%d"),
            "endDate": end_date.strftime("%Y-%m-%d"),
            "dimensions": ["page"],
            "rowLimit": 500,
        },
    ).execute()

    # Fetch query-level stats
    query_response = service.searchanalytics().query(
        siteUrl=site_url,
        body={
            "startDate": start_date.strftime("%Y-%m-%d"),
            "endDate": end_date.strftime("%Y-%m-%d"),
            "dimensions": ["query"],
            "rowLimit": 1000,
        },
    ).execute()

    # Fetch page+query combo for deeper analysis
    page_query_response = service.searchanalytics().query(
        siteUrl=site_url,
        body={
            "startDate": start_date.strftime("%Y-%m-%d"),
            "endDate": end_date.strftime("%Y-%m-%d"),
            "dimensions": ["page", "query"],
            "rowLimit": 2000,
        },
    ).execute()

    data = {
        "period": {
            "start": start_date.strftime("%Y-%m-%d"),
            "end": end_date.strftime("%Y-%m-%d"),
        },
        "pages": _parse_rows(page_response),
        "queries": _parse_rows(query_response),
        "page_queries": _parse_page_query_rows(page_query_response),
    }

    return data


def _parse_rows(response: dict) -> list[dict]:
    """Parse GSC API response rows."""
    rows = []
    for row in response.get("rows", []):
        rows.append({
            "key": row["keys"][0],
            "clicks": row["clicks"],
            "impressions": row["impressions"],
            "ctr": round(row["ctr"] * 100, 2),
            "position": round(row["position"], 1),
        })
    return rows


def _parse_page_query_rows(response: dict) -> list[dict]:
    """Parse page+query combo rows."""
    rows = []
    for row in response.get("rows", []):
        rows.append({
            "page": row["keys"][0],
            "query": row["keys"][1],
            "clicks": row["clicks"],
            "impressions": row["impressions"],
            "ctr": round(row["ctr"] * 100, 2),
            "position": round(row["position"], 1),
        })
    return rows


def print_report(data: dict):
    """Print a human-readable SEO report."""
    print(f"\n📊 SEO Report ({data['period']['start']} → {data['period']['end']})")
    print("=" * 60)

    # Top pages by impressions
    pages = sorted(data["pages"], key=lambda x: x["impressions"], reverse=True)
    print(f"\n🏆 Top Pages by Impressions:")
    for p in pages[:10]:
        print(f"  {p['impressions']:>6} imp | {p['clicks']:>4} clicks | CTR {p['ctr']:>5}% | Pos {p['position']:>4} | {p['key']}")

    # High impression, low CTR (optimization opportunities)
    low_ctr = [p for p in pages if p["impressions"] > 50 and p["ctr"] < 3.0]
    if low_ctr:
        print(f"\n⚠️  High Impressions, Low CTR (title/description optimization needed):")
        for p in low_ctr[:5]:
            print(f"  {p['impressions']:>6} imp | CTR {p['ctr']:>5}% | Pos {p['position']:>4} | {p['key']}")

    # Position 5-20 (close to page 1 — content optimization)
    almost = [p for p in pages if 5 <= p["position"] <= 20]
    if almost:
        print(f"\n🎯 Almost Page 1 (position 5-20, optimize content):")
        for p in almost[:5]:
            print(f"  Pos {p['position']:>4} | {p['impressions']:>6} imp | {p['key']}")

    # Top queries
    queries = sorted(data["queries"], key=lambda x: x["impressions"], reverse=True)
    print(f"\n🔍 Top Queries:")
    for q in queries[:10]:
        print(f"  {q['impressions']:>6} imp | {q['clicks']:>4} clicks | Pos {q['position']:>4} | {q['key']}")


def suggest_optimizations(data: dict) -> list[str]:
    """Analyze data and suggest concrete optimizations."""
    suggestions = []
    pages = data["pages"]

    # High impressions, low CTR → rewrite title/description
    for p in pages:
        if p["impressions"] > 100 and p["ctr"] < 2.0:
            suggestions.append(
                f"REWRITE TITLE/DESC: {p['key']} — {p['impressions']} impressions but only {p['ctr']}% CTR"
            )

    # Position 4-15 → strengthen content to push to top 3
    for p in pages:
        if 4 <= p["position"] <= 15 and p["impressions"] > 50:
            suggestions.append(
                f"STRENGTHEN CONTENT: {p['key']} — position {p['position']}, needs more depth/keywords to reach top 3"
            )

    # Find queries with no dedicated page
    page_queries = data.get("page_queries", [])
    top_queries = {q["key"] for q in sorted(data["queries"], key=lambda x: x["impressions"], reverse=True)[:20]}
    covered_queries = set()
    for pq in page_queries:
        if pq["position"] <= 5:
            covered_queries.add(pq["query"])

    uncovered = top_queries - covered_queries
    for q in uncovered:
        suggestions.append(f"NEW ARTICLE NEEDED: No page ranks well for '{q}'")

    return suggestions
