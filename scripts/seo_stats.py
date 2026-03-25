"""Fetch and analyze SEO stats from Google Search Console."""

import json
from datetime import datetime, timedelta
from pathlib import Path

import google.auth
from googleapiclient.discovery import build


def _get_gsc_service():
    """Authenticate using Application Default Credentials and return GSC service."""
    creds, _ = google.auth.default(
        scopes=["https://www.googleapis.com/auth/webmasters.readonly"]
    )
    return build("searchconsole", "v1", credentials=creds)


def fetch_seo_stats(credentials_path: str, site_url: str, days: int) -> dict:
    """Fetch performance data from Google Search Console."""
    service = _get_gsc_service()

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
    print(f"\nSEO Report ({data['period']['start']} to {data['period']['end']})")
    print("=" * 60)

    pages = sorted(data["pages"], key=lambda x: x["impressions"], reverse=True)
    print(f"\nTop Pages by Impressions:")
    for p in pages[:10]:
        print(f"  {p['impressions']:>6} imp | {p['clicks']:>4} clicks | CTR {p['ctr']:>5}% | Pos {p['position']:>4} | {p['key']}")

    low_ctr = [p for p in pages if p["impressions"] > 50 and p["ctr"] < 3.0]
    if low_ctr:
        print(f"\nHigh Impressions, Low CTR (optimize title/description):")
        for p in low_ctr[:5]:
            print(f"  {p['impressions']:>6} imp | CTR {p['ctr']:>5}% | Pos {p['position']:>4} | {p['key']}")

    almost = [p for p in pages if 5 <= p["position"] <= 20]
    if almost:
        print(f"\nAlmost Page 1 (position 5-20, strengthen content):")
        for p in almost[:5]:
            print(f"  Pos {p['position']:>4} | {p['impressions']:>6} imp | {p['key']}")

    queries = sorted(data["queries"], key=lambda x: x["impressions"], reverse=True)
    print(f"\nTop Queries:")
    for q in queries[:10]:
        print(f"  {q['impressions']:>6} imp | {q['clicks']:>4} clicks | Pos {q['position']:>4} | {q['key']}")

    if not pages and not queries:
        print("\n  No data yet. Google needs a few days to start reporting after indexing.")


def suggest_optimizations(data: dict) -> list[str]:
    """Analyze data and suggest concrete optimizations."""
    suggestions = []
    pages = data["pages"]

    for p in pages:
        if p["impressions"] > 100 and p["ctr"] < 2.0:
            suggestions.append(
                f"REWRITE TITLE/DESC: {p['key']} — {p['impressions']} impressions but only {p['ctr']}% CTR"
            )

    for p in pages:
        if 4 <= p["position"] <= 15 and p["impressions"] > 50:
            suggestions.append(
                f"STRENGTHEN CONTENT: {p['key']} — position {p['position']}, needs more depth to reach top 3"
            )

    page_queries = data.get("page_queries", [])
    top_queries = {q["key"] for q in sorted(data["queries"], key=lambda x: x["impressions"], reverse=True)[:20]}
    covered_queries = set()
    for pq in page_queries:
        if pq["position"] <= 5:
            covered_queries.add(pq["query"])

    uncovered = top_queries - covered_queries
    for q in uncovered:
        suggestions.append(f"NEW ARTICLE NEEDED: No page ranks well for '{q}'")

    if not suggestions:
        suggestions.append("No actionable optimizations yet — need more data from Google.")

    return suggestions
