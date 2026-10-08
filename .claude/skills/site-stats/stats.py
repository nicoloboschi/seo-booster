# /// script
# dependencies = ["google-api-python-client", "google-auth", "google-analytics-data", "python-dotenv"]
# ///
"""Print a plain-text report: Google Search Console, index coverage sample, GA4.

Usage: uv run .claude/skills/site-stats/stats.py [--days 28] [--inspect 30] [--pages]
"""
import argparse
import os
import random
import re
import urllib.request
import subprocess
import warnings
from datetime import date, timedelta
from pathlib import Path

warnings.filterwarnings("ignore")
# Secrets live in the main checkout; in a git worktree they aren't present, so resolve via the common .git dir.
ROOT = Path(subprocess.run(["git", "rev-parse", "--path-format=absolute", "--git-common-dir"], cwd=Path(__file__).parent,
                           capture_output=True, text=True).stdout.strip()).parent
SITE = "https://aiagentmemory.org/"

ap = argparse.ArgumentParser()
ap.add_argument("--days", type=int, default=28)
ap.add_argument("--inspect", type=int, default=30, help="random sitemap URLs to check index status (0 = skip)")
ap.add_argument("--pages", action="store_true", help="dump every page with impressions (slug, clicks, impr, pos)")
args = ap.parse_args()

end = date.today() - timedelta(days=3)  # GSC lags ~3 days
start = end - timedelta(days=args.days)

# --- Search Console. Prefer the service account (never expires; must be a "Full" user on the property),
# fall back to the user's gcloud login.
import google.auth
from google.oauth2 import service_account
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/webmasters.readonly"]
sa = ROOT / ".secrets" / "ga-service-account.json"
gsc = None
if sa.exists():
    gsc = build("searchconsole", "v1", credentials=service_account.Credentials.from_service_account_file(str(sa), scopes=SCOPES))
    if SITE not in {s["siteUrl"] for s in gsc.sites().list().execute().get("siteEntry", [])}:
        print(f"(service account has no Search Console access to {SITE}; using gcloud login)")
        gsc = None
if gsc is None:
    gsc = build("searchconsole", "v1", credentials=google.auth.default(scopes=SCOPES)[0])


def q(dims, limit=25, s=start, e=end):
    body = {"startDate": str(s), "endDate": str(e), "dimensions": dims, "rowLimit": limit}
    return gsc.searchanalytics().query(siteUrl=SITE, body=body).execute().get("rows", [])


def slug(url):
    return url.replace(SITE, "/") or "/"


print(f"== Google Search Console {start} .. {end}")
tot = q([], 1)
if tot:
    t = tot[0]
    print(f"clicks {t['clicks']:.0f}  impressions {t['impressions']:.0f}  avg pos {t['position']:.1f}")
pages = q(["page"], 5000)
print(f"pages with any impression: {len(pages)}")
print("\nTop queries (by impressions):")
for r in sorted(q(["query"], 1000), key=lambda r: -r["impressions"])[:25]:
    print(f"  {r['keys'][0][:60]:60} c{r['clicks']:<3.0f} i{r['impressions']:<5.0f} pos {r['position']:.1f}")
print("\nTop pages (by impressions):")
for r in sorted(pages, key=lambda r: -r["impressions"])[:20]:
    print(f"  {slug(r['keys'][0])[:60]:60} c{r['clicks']:<3.0f} i{r['impressions']:<5.0f} pos {r['position']:.1f}")
if args.pages:
    print("\nAll pages with impressions:")
    for r in pages:
        print(f"  {slug(r['keys'][0])}\t{r['clicks']:.0f}\t{r['impressions']:.0f}\t{r['position']:.1f}")

if args.inspect:
    from collections import Counter

    urls = re.findall(r"<loc>([^<]+)</loc>", urllib.request.urlopen(SITE + "sitemap.xml").read().decode())
    sample = random.sample(urls, min(args.inspect, len(urls)))
    states = Counter()
    for u in sample:
        res = gsc.urlInspection().index().inspect(body={"inspectionUrl": u, "siteUrl": SITE}).execute()
        states[res["inspectionResult"]["indexStatusResult"].get("coverageState", "?")] += 1
    print(f"\n== Index status, random {len(sample)} of {len(urls)} sitemap URLs")
    for k, v in states.most_common():
        print(f"  {v:3}  {k}")

# --- GA4 (service account in .secrets/, property id in .env GA_PROPERTY_ID)
from dotenv import load_dotenv

load_dotenv(ROOT / ".env")
prop = os.environ.get("GA_PROPERTY_ID")
if not (sa.exists() and prop):
    print("\n(GA skipped: need .secrets/ga-service-account.json and GA_PROPERTY_ID)")
    raise SystemExit
from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import DateRange, Dimension, Metric, OrderBy, RunReportRequest

ga = BetaAnalyticsDataClient.from_service_account_file(str(sa))


def run(dims, mets, limit=15):
    r = ga.run_report(RunReportRequest(
        property=f"properties/{prop}",
        date_ranges=[DateRange(start_date=f"{args.days}daysAgo", end_date="today")],
        dimensions=[Dimension(name=d) for d in dims], metrics=[Metric(name=m) for m in mets], limit=limit,
        order_bys=[OrderBy(metric=OrderBy.MetricOrderBy(metric_name=mets[0]), desc=True)]))
    return [([v.value for v in x.dimension_values], [v.value for v in x.metric_values]) for x in r.rows]


# GA only sees JS-running visitors. AI crawlers don't run JS, so this is humans + scrapers.
# "Direct" from Singapore with ~0 engagement is scraper noise; judge by engaged sessions.
print(f"\n== GA4 last {args.days} days (humans + JS scrapers; AI crawlers are invisible here)")
for d, m in run(["sessionDefaultChannelGroup"], ["sessions", "engagedSessions"], 8):
    print(f"  {d[0]:20} sessions {m[0]:>6}  engaged {m[1]:>5}")
print("Search sources:")
for d, m in run(["sessionSource"], ["engagedSessions"], 10):
    print(f"  {d[0]:30} engaged {m[0]}")
print("Top pages by engaged sessions:")
for d, m in run(["pagePath"], ["engagedSessions", "screenPageViews"], 20):
    print(f"  {d[0][:60]:60} engaged {m[0]:>4}  views {m[1]}")
print("Hindsight link clicks:")
for d, m in run(["linkUrl"], ["eventCount"], 50):
    if "hindsight" in d[0]:
        print(f"  {d[0]}  {m[0]}")
