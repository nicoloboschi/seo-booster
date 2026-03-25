"""Daily health report — checks everything and prints a summary."""

import json
import subprocess
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

PROJECT_DIR = Path(__file__).parent.parent


def run_health_check() -> dict:
    """Run all health checks and return a report."""
    report = {
        "timestamp": datetime.now().isoformat(),
        "checks": {},
        "issues": [],
        "stats": {},
    }

    # 1. Article count
    articles_dir = PROJECT_DIR / "content" / "articles"
    articles = [f for f in articles_dir.glob("*.md") if not f.name.startswith("_")]
    report["stats"]["total_articles"] = len(articles)
    report["checks"]["articles_exist"] = len(articles) > 0

    # 2. Generated tracking
    gen_file = articles_dir / "_generated.json"
    if gen_file.exists():
        generated = json.loads(gen_file.read_text())
        report["stats"]["tracked_articles"] = len(generated)
    else:
        report["stats"]["tracked_articles"] = 0
        report["issues"].append("No _generated.json — tracking file missing")

    # 3. Keywords remaining
    kw_file = PROJECT_DIR / "data" / "keywords.yaml"
    if kw_file.exists():
        import yaml
        with open(kw_file) as f:
            kw_config = yaml.safe_load(f)
        all_kw = kw_config.get("keywords", [])
        generated_slugs = set(generated.keys()) if gen_file.exists() else set()
        pending = [kw for kw in all_kw
                   if kw.get("slug", kw["primary"].lower().replace(" ", "-")) not in generated_slugs]
        report["stats"]["total_keywords"] = len(all_kw)
        report["stats"]["pending_keywords"] = len(pending)
        if len(pending) < 10:
            report["issues"].append(f"Only {len(pending)} keywords remaining — need more research")
    else:
        report["issues"].append("No keywords.yaml found")

    # 4. Hugo build test
    result = subprocess.run(
        ["hugo", "--minify"], cwd=PROJECT_DIR,
        capture_output=True, text=True,
    )
    report["checks"]["hugo_builds"] = result.returncode == 0
    if result.returncode != 0:
        report["issues"].append(f"Hugo build failed: {result.stderr[:200]}")

    # 5. Site is live
    import httpx
    try:
        resp = httpx.get("https://aiagentmemory.org/", timeout=10, follow_redirects=True)
        report["checks"]["site_live"] = resp.status_code == 200
        if resp.status_code != 200:
            report["issues"].append(f"Site returned HTTP {resp.status_code}")
    except Exception as e:
        report["checks"]["site_live"] = False
        report["issues"].append(f"Site unreachable: {e}")

    # 6. Sitemap accessible
    try:
        resp = httpx.get("https://aiagentmemory.org/sitemap.xml", timeout=10)
        report["checks"]["sitemap_accessible"] = resp.status_code == 200
        if resp.status_code == 200:
            # Count URLs in sitemap
            url_count = resp.text.count("<loc>")
            report["stats"]["sitemap_urls"] = url_count
        else:
            report["issues"].append("Sitemap not accessible")
    except Exception as e:
        report["checks"]["sitemap_accessible"] = False
        report["issues"].append(f"Sitemap unreachable: {e}")

    # 7. CSS loads
    try:
        resp = httpx.get("https://aiagentmemory.org/css/style.css", timeout=10)
        report["checks"]["css_loads"] = resp.status_code == 200
        if resp.status_code != 200:
            report["issues"].append("CSS file not loading")
    except Exception:
        report["checks"]["css_loads"] = False
        report["issues"].append("CSS unreachable")

    # 8. Git status — any uncommitted changes?
    status = subprocess.run(
        ["git", "status", "--porcelain"],
        capture_output=True, text=True, cwd=PROJECT_DIR,
    )
    uncommitted = len([l for l in status.stdout.strip().split("\n") if l.strip()])
    report["stats"]["uncommitted_files"] = uncommitted
    if uncommitted > 20:
        report["issues"].append(f"{uncommitted} uncommitted files — deploy may be stale")

    # 9. Scraped content freshness
    scraped_dir = PROJECT_DIR / "data" / "scraped"
    if scraped_dir.exists():
        scraped_files = list(scraped_dir.glob("*.json"))
        report["stats"]["scraped_items"] = len(scraped_files)
        if scraped_files:
            newest = max(f.stat().st_mtime for f in scraped_files)
            age_hours = (datetime.now().timestamp() - newest) / 3600
            report["stats"]["scraped_age_hours"] = round(age_hours, 1)
            if age_hours > 48:
                report["issues"].append(f"Scraped content is {age_hours:.0f}h old — scraper may be stuck")
    else:
        report["stats"]["scraped_items"] = 0
        report["issues"].append("No scraped content directory")

    # 10. GSC data check
    try:
        import google.auth
        from googleapiclient.discovery import build
        creds, _ = google.auth.default(
            scopes=["https://www.googleapis.com/auth/webmasters.readonly"]
        )
        service = build("searchconsole", "v1", credentials=creds)
        from datetime import timedelta
        end = datetime.now() - timedelta(days=3)
        start = end - timedelta(days=7)
        response = service.searchanalytics().query(
            siteUrl="https://aiagentmemory.org/",
            body={
                "startDate": start.strftime("%Y-%m-%d"),
                "endDate": end.strftime("%Y-%m-%d"),
                "dimensions": ["page"],
                "rowLimit": 5,
            },
        ).execute()
        rows = response.get("rows", [])
        total_impressions = sum(r["impressions"] for r in rows)
        total_clicks = sum(r["clicks"] for r in rows)
        report["checks"]["gsc_connected"] = True
        report["stats"]["gsc_impressions_7d"] = total_impressions
        report["stats"]["gsc_clicks_7d"] = total_clicks
        report["stats"]["gsc_pages_reporting"] = len(rows)
        if total_impressions == 0:
            report["issues"].append("GSC shows 0 impressions — Google may not have indexed yet")
    except Exception as e:
        report["checks"]["gsc_connected"] = False
        err = str(e)
        if "permission" in err.lower() or "403" in err:
            report["issues"].append("GSC: site not verified or no permission")
        else:
            report["issues"].append(f"GSC check failed: {err[:100]}")

    # 11. Google Analytics data
    try:
        from scripts.ga_stats import fetch_ga_report
        ga = fetch_ga_report()
        if "error" not in ga:
            rt = ga.get("realtime", {})
            d7 = ga.get("last_7_days", {})
            if "error" not in rt:
                report["stats"]["ga_active_users"] = rt.get("active_users", 0)
                report["checks"]["ga_connected"] = True
            if "error" not in d7:
                o = d7.get("overall", {})
                report["stats"]["ga_users_7d"] = o.get("users", 0)
                report["stats"]["ga_pageviews_7d"] = o.get("pageviews", 0)
                report["stats"]["ga_sessions_7d"] = o.get("sessions", 0)
            report["ga_report"] = ga
        else:
            report["checks"]["ga_connected"] = False
    except Exception as e:
        report["checks"]["ga_connected"] = False

    return report


def print_health_report(report: dict):
    """Print a formatted health report."""
    print(f"\n{'='*60}")
    print(f"  HEALTH REPORT — {report['timestamp'][:16]}")
    print(f"{'='*60}")

    # Stats
    s = report["stats"]
    print(f"\n  Articles:     {s.get('total_articles', '?')} published, {s.get('pending_keywords', '?')} keywords queued")
    print(f"  Sitemap:      {s.get('sitemap_urls', '?')} URLs")
    print(f"  Scraped:      {s.get('scraped_items', '?')} items ({s.get('scraped_age_hours', '?')}h old)")
    if "gsc_impressions_7d" in s:
        print(f"  GSC (7d):     {s['gsc_impressions_7d']} impressions, {s['gsc_clicks_7d']} clicks, {s['gsc_pages_reporting']} pages")

    # Checks
    print(f"\n  Checks:")
    for check, passed in report["checks"].items():
        icon = "PASS" if passed else "FAIL"
        print(f"    [{icon}] {check}")

    # Issues
    if report["issues"]:
        print(f"\n  Issues ({len(report['issues'])}):")
        for issue in report["issues"]:
            print(f"    ! {issue}")
    else:
        print(f"\n  No issues found.")

    print(f"\n{'='*60}\n")


def save_health_history(report: dict):
    """Append report to health history file."""
    history_file = PROJECT_DIR / "data" / "_health_history.jsonl"
    history_file.parent.mkdir(parents=True, exist_ok=True)
    with open(history_file, "a") as f:
        f.write(json.dumps(report) + "\n")
