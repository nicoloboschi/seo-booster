"""Fetch Google Analytics 4 real-time and reporting data."""

import os
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

PROJECT_DIR = Path(__file__).parent.parent
GA_SERVICE_ACCOUNT = PROJECT_DIR / "data" / "ga-service-account.json"


def _get_ga_client():
    """Get GA4 Data API client using service account."""
    from google.analytics.data_v1beta import BetaAnalyticsDataClient

    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = str(GA_SERVICE_ACCOUNT)
    return BetaAnalyticsDataClient()


def get_property_id() -> str:
    """Get GA4 property ID from env or config."""
    return os.environ.get("GA_PROPERTY_ID", "")


def fetch_realtime(property_id: str) -> dict:
    """Fetch real-time active users and top pages."""
    from google.analytics.data_v1beta.types import (
        RunRealtimeReportRequest,
        Metric,
        Dimension,
    )

    client = _get_ga_client()

    # Real-time active users
    request = RunRealtimeReportRequest(
        property=f"properties/{property_id}",
        metrics=[Metric(name="activeUsers")],
        dimensions=[Dimension(name="unifiedScreenName")],
    )
    response = client.run_realtime_report(request)

    active_users = 0
    top_pages = []
    for row in response.rows:
        users = int(row.metric_values[0].value)
        page = row.dimension_values[0].value
        active_users += users
        top_pages.append({"page": page, "users": users})

    top_pages.sort(key=lambda x: x["users"], reverse=True)

    return {
        "active_users": active_users,
        "top_pages": top_pages[:5],
    }


def fetch_last_7_days(property_id: str) -> dict:
    """Fetch last 7 days: users, sessions, pageviews, top pages."""
    from google.analytics.data_v1beta.types import (
        RunReportRequest,
        DateRange,
        Metric,
        Dimension,
        OrderBy,
    )

    client = _get_ga_client()

    # Overall metrics
    request = RunReportRequest(
        property=f"properties/{property_id}",
        date_ranges=[DateRange(start_date="7daysAgo", end_date="today")],
        metrics=[
            Metric(name="activeUsers"),
            Metric(name="sessions"),
            Metric(name="screenPageViews"),
            Metric(name="averageSessionDuration"),
            Metric(name="bounceRate"),
        ],
    )
    response = client.run_report(request)

    overall = {}
    if response.rows:
        row = response.rows[0]
        overall = {
            "users": int(row.metric_values[0].value),
            "sessions": int(row.metric_values[1].value),
            "pageviews": int(row.metric_values[2].value),
            "avg_session_duration": round(float(row.metric_values[3].value), 1),
            "bounce_rate": round(float(row.metric_values[4].value) * 100, 1),
        }

    # Top pages
    request = RunReportRequest(
        property=f"properties/{property_id}",
        date_ranges=[DateRange(start_date="7daysAgo", end_date="today")],
        metrics=[Metric(name="screenPageViews"), Metric(name="activeUsers")],
        dimensions=[Dimension(name="pagePath")],
        order_bys=[OrderBy(metric=OrderBy.MetricOrderBy(metric_name="screenPageViews"), desc=True)],
        limit=10,
    )
    response = client.run_report(request)

    top_pages = []
    for row in response.rows:
        top_pages.append({
            "path": row.dimension_values[0].value,
            "pageviews": int(row.metric_values[0].value),
            "users": int(row.metric_values[1].value),
        })

    # Traffic sources
    request = RunReportRequest(
        property=f"properties/{property_id}",
        date_ranges=[DateRange(start_date="7daysAgo", end_date="today")],
        metrics=[Metric(name="sessions")],
        dimensions=[Dimension(name="sessionDefaultChannelGroup")],
        order_bys=[OrderBy(metric=OrderBy.MetricOrderBy(metric_name="sessions"), desc=True)],
        limit=5,
    )
    response = client.run_report(request)

    sources = []
    for row in response.rows:
        sources.append({
            "channel": row.dimension_values[0].value,
            "sessions": int(row.metric_values[0].value),
        })

    return {
        "overall": overall,
        "top_pages": top_pages,
        "sources": sources,
    }


def fetch_ga_report() -> dict:
    """Fetch all GA data."""
    property_id = get_property_id()
    if not property_id:
        return {"error": "GA_PROPERTY_ID not set in .env"}

    if not GA_SERVICE_ACCOUNT.exists():
        return {"error": "GA service account key not found at data/ga-service-account.json"}

    report = {"timestamp": datetime.now().isoformat()}

    try:
        report["realtime"] = fetch_realtime(property_id)
    except Exception as e:
        report["realtime"] = {"error": str(e)[:100]}

    try:
        report["last_7_days"] = fetch_last_7_days(property_id)
    except Exception as e:
        report["last_7_days"] = {"error": str(e)[:100]}

    return report


def format_ga_telegram(report: dict) -> str:
    """Format GA report for Telegram."""
    if "error" in report:
        return f"📈 GA: {report['error']}"

    lines = ["📈 <b>Google Analytics</b>", ""]

    # Real-time
    rt = report.get("realtime", {})
    if "error" not in rt:
        lines.append(f"<b>Right now:</b> {rt.get('active_users', 0)} active users")
        for p in rt.get("top_pages", [])[:3]:
            lines.append(f"  • {p['page']} ({p['users']} users)")
    else:
        lines.append(f"Real-time: {rt['error']}")

    # Last 7 days
    d = report.get("last_7_days", {})
    if "error" not in d:
        o = d.get("overall", {})
        lines.append(f"\n<b>Last 7 days:</b>")
        lines.append(f"  Users: {o.get('users', 0)} | Sessions: {o.get('sessions', 0)} | Pages: {o.get('pageviews', 0)}")
        lines.append(f"  Bounce: {o.get('bounce_rate', 0)}% | Avg duration: {o.get('avg_session_duration', 0)}s")

        sources = d.get("sources", [])
        if sources:
            src_str = ", ".join(f"{s['channel']}({s['sessions']})" for s in sources[:3])
            lines.append(f"  Sources: {src_str}")

        top = d.get("top_pages", [])
        if top:
            lines.append(f"\n<b>Top pages:</b>")
            for p in top[:5]:
                lines.append(f"  • {p['path']} — {p['pageviews']} views")

    return "\n".join(lines)
