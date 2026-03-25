"""Send notifications via Telegram Bot API."""

import os

import httpx
from dotenv import load_dotenv

load_dotenv()


def send_telegram(message: str) -> bool:
    """Send a message via Telegram Bot API. Returns True on success."""
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")

    if not token or not chat_id:
        return False

    try:
        resp = httpx.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={
                "chat_id": chat_id,
                "text": message,
                "parse_mode": "HTML",
                "disable_web_page_preview": True,
            },
            timeout=10,
        )
        return resp.status_code == 200
    except Exception:
        return False


def format_health_report(report: dict) -> str:
    """Format a health report for Telegram."""
    s = report.get("stats", {})
    checks = report.get("checks", {})
    issues = report.get("issues", [])

    # Status emoji
    all_pass = all(checks.values()) and len(issues) == 0
    status = "🟢" if all_pass else ("🟡" if len(issues) <= 2 else "🔴")

    lines = [
        f"{status} <b>SEO Booster Health Report</b>",
        "",
        f"📝 Articles: <b>{s.get('total_articles', '?')}</b> published",
        f"🔑 Keywords: <b>{s.get('pending_keywords', '?')}</b> queued",
        f"🗺 Sitemap: {s.get('sitemap_urls', '?')} URLs",
    ]

    if "ga_active_users" in s:
        lines.append(f"👥 GA live: <b>{s['ga_active_users']}</b> active users")
    if "ga_users_7d" in s:
        lines.append(f"📈 GA (7d): {s['ga_users_7d']} users, {s.get('ga_pageviews_7d', 0)} pageviews, {s.get('ga_sessions_7d', 0)} sessions")

    if "gsc_impressions_7d" in s:
        lines.append(f"📊 GSC (7d): {s['gsc_impressions_7d']} imp, {s['gsc_clicks_7d']} clicks")

    if "scraped_age_hours" in s:
        lines.append(f"📡 Scraped: {s.get('scraped_items', '?')} items ({s['scraped_age_hours']}h ago)")

    # GA top pages if available
    ga_report = report.get("ga_report", {})
    top_pages = ga_report.get("last_7_days", {}).get("top_pages", [])
    if top_pages:
        lines.append(f"\n<b>Top pages (7d):</b>")
        for p in top_pages[:5]:
            lines.append(f"  • {p['path']} — {p['pageviews']} views")

    # Checks
    failed = [k for k, v in checks.items() if not v]
    if failed:
        lines.append(f"\n❌ Failed: {', '.join(failed)}")

    # Issues
    if issues:
        lines.append(f"\n⚠️ <b>Issues ({len(issues)}):</b>")
        for issue in issues[:5]:
            lines.append(f"  • {issue}")
    else:
        lines.append("\n✅ No issues found")

    return "\n".join(lines)


def format_generation_report(count: int, total: int, keywords_remaining: int) -> str:
    """Format a generation batch report for Telegram."""
    return (
        f"📝 <b>Generated {count} new articles</b>\n"
        f"Total: {total} articles\n"
        f"Keywords remaining: {keywords_remaining}"
    )


def format_deploy_report(files_changed: int) -> str:
    """Format a deploy notification for Telegram."""
    return f"🚀 Deployed ({files_changed} files changed)"
