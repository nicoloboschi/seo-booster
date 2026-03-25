"""Long-running daemon that continuously generates, optimizes, and deploys SEO content."""

import json
import os
import subprocess
import time
from datetime import datetime, timedelta
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# Schedule configuration
SCRAPE_INTERVAL_MINUTES = 30
GENERATE_INTERVAL_MINUTES = 120       # every 2h, generates a batch
ARTICLES_PER_BATCH = 5                # 5 per batch × ~5 batches/day = ~10/day
OPTIMIZE_INTERVAL_MINUTES = 60        # check GSC hourly
RESEARCH_INTERVAL_MINUTES = 360       # keyword research every 6h
DEPLOY_INTERVAL_MINUTES = 30          # deploy every 30 min
HEALTH_INTERVAL_MINUTES = 60          # health report + Telegram every hour
PRESENCE_INTERVAL_MINUTES = 10080     # LLM presence test weekly
AUDIT_EVERY_N_ARTICLES = 50           # full audit every 50 articles

PROJECT_DIR = Path(__file__).parent.parent


class Scheduler:
    """Tracks when tasks last ran, persisted to disk."""

    def __init__(self, state_file: Path):
        self.state_file = state_file
        self.state = self._load()

    def _load(self) -> dict:
        if self.state_file.exists():
            return json.loads(self.state_file.read_text())
        return {}

    def _save(self):
        self.state_file.write_text(json.dumps(self.state, indent=2))

    def is_due(self, task: str, interval_minutes: float) -> bool:
        last_run = self.state.get(task)
        if not last_run:
            return True
        last_dt = datetime.fromisoformat(last_run)
        return datetime.now() - last_dt > timedelta(minutes=interval_minutes)

    def mark_done(self, task: str):
        self.state[task] = datetime.now().isoformat()
        self._save()

    def get_counter(self, key: str) -> int:
        return self.state.get(key, 0)

    def increment_counter(self, key: str, by: int = 1):
        self.state[key] = self.state.get(key, 0) + by
        self._save()


def run_cli(*args) -> bool:
    """Run a seo-booster CLI command. Returns True on success."""
    cmd = ["uv", "run", "seo-booster", *args]
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"\n{'='*60}")
    print(f"[{ts}] {' '.join(cmd)}")
    print(f"{'='*60}")
    result = subprocess.run(cmd, cwd=PROJECT_DIR)
    return result.returncode == 0


def git_deploy() -> bool:
    """Commit source changes to main, then deploy built site to gh-pages."""

    # Check for changes
    status = subprocess.run(["git", "status", "--porcelain", "content/", "data/"],
                            capture_output=True, text=True, cwd=PROJECT_DIR)
    if not status.stdout.strip():
        print("  No changes to deploy.")
        return True

    lines = [l for l in status.stdout.strip().split("\n") if l.strip()]
    print(f"  {len(lines)} files changed")

    # Commit source to main
    subprocess.run(["git", "add", "content/", "data/"], cwd=PROJECT_DIR)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    result = subprocess.run(
        ["git", "commit", "-m", f"Content update {timestamp}"],
        cwd=PROJECT_DIR,
    )
    if result.returncode != 0:
        print("  Source commit failed")
        return False

    result = subprocess.run(["git", "push"], cwd=PROJECT_DIR)
    if result.returncode != 0:
        print("  Source push failed")
        return False

    # Deploy to gh-pages via deploy script
    deploy_script = PROJECT_DIR / "scripts" / "deploy.sh"
    print("  Running deploy script...")
    result = subprocess.run(["bash", str(deploy_script)], cwd=PROJECT_DIR)
    if result.returncode != 0:
        print("  Deploy failed")
        return False

    print("  Deployed to gh-pages.")
    return True


def run_daemon():
    """Main daemon loop — runs 24/7."""
    state_file = PROJECT_DIR / "data" / "_scheduler_state.json"
    scheduler = Scheduler(state_file)

    total_articles = scheduler.get_counter("total_articles")

    print(f"""
╔═══════════════════════════════════════════════════╗
║            SEO Booster Daemon Started             ║
╠═══════════════════════════════════════════════════╣
║  Scrape:    every {SCRAPE_INTERVAL_MINUTES:>3} min                        ║
║  Generate:  every {GENERATE_INTERVAL_MINUTES:>3} min ({ARTICLES_PER_BATCH} articles/batch)     ║
║  Deploy:    every {DEPLOY_INTERVAL_MINUTES:>3} min                        ║
║  Optimize:  every {OPTIMIZE_INTERVAL_MINUTES:>3} min (needs GSC creds)      ║
║  Audit:     every {AUDIT_EVERY_N_ARTICLES:>3} articles                    ║
║  Total articles so far: {total_articles:>4}                       ║
║                                                   ║
║  Target: ~10 articles/day → 1,000 in 3 months     ║
╚═══════════════════════════════════════════════════╝
    """)

    while True:
        try:
            changed = False

            # 1. Scrape sources
            if scheduler.is_due("scrape", SCRAPE_INTERVAL_MINUTES):
                if run_cli("scrape"):
                    scheduler.mark_done("scrape")

            # 2. Generate articles
            if scheduler.is_due("generate", GENERATE_INTERVAL_MINUTES):
                if run_cli("generate", "--count", str(ARTICLES_PER_BATCH)):
                    scheduler.mark_done("generate")
                    scheduler.increment_counter("total_articles", ARTICLES_PER_BATCH)
                    changed = True

                    total = scheduler.get_counter("total_articles")
                    print(f"\n  Total articles: {total}")

                    # Periodic full audit
                    if total % AUDIT_EVERY_N_ARTICLES == 0:
                        print(f"\n  Milestone: {total} articles — running full audit")
                        run_cli("audit")

            # 3. Keyword research — discover and validate new keywords
            if scheduler.is_due("research", RESEARCH_INTERVAL_MINUTES):
                if run_cli("research", "--add-opportunities"):
                    scheduler.mark_done("research")

            # 4. Optimize (if GSC configured)
            if scheduler.is_due("optimize", OPTIMIZE_INTERVAL_MINUTES):
                try:
                    if run_cli("stats"):
                        run_cli("optimize")
                        scheduler.mark_done("optimize")
                        changed = True
                    else:
                        # GSC not configured or no data yet, skip for now
                        scheduler.mark_done("optimize")
                except Exception as e:
                    print(f"  GSC optimization skipped: {e}")
                    scheduler.mark_done("optimize")

            # 5. Daily health report + Telegram notification
            if scheduler.is_due("health", HEALTH_INTERVAL_MINUTES):
                from scripts.health import run_health_check, print_health_report, save_health_history
                from scripts.notify import send_telegram, format_health_report
                report = run_health_check()
                print_health_report(report)
                save_health_history(report)
                send_telegram(format_health_report(report))
                scheduler.mark_done("health")

            # 6. Weekly LLM presence test
            if scheduler.is_due("presence", PRESENCE_INTERVAL_MINUTES):
                try:
                    from scripts.llm_presence import (
                        run_presence_test, print_presence_report,
                        save_presence_history, format_presence_telegram,
                    )
                    from scripts.notify import send_telegram
                    report = run_presence_test()
                    print_presence_report(report)
                    save_presence_history(report)
                    send_telegram(format_presence_telegram(report))
                except Exception as e:
                    print(f"  Presence test failed: {e}")
                scheduler.mark_done("presence")

            # 7. Deploy
            if changed or scheduler.is_due("deploy", DEPLOY_INTERVAL_MINUTES):
                ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                print(f"\n[{ts}] Deploying...")
                if git_deploy():
                    scheduler.mark_done("deploy")

            # Sleep until next task
            _sleep_until_next(scheduler)

        except KeyboardInterrupt:
            total = scheduler.get_counter("total_articles")
            print(f"\nDaemon stopped. Total articles: {total}")
            break
        except Exception as e:
            print(f"\n[ERROR] {e}")
            import traceback
            traceback.print_exc()
            print("Retrying in 2 minutes...")
            time.sleep(120)


def _sleep_until_next(scheduler: Scheduler):
    """Sleep until the next task is due."""
    tasks = [
        ("scrape", SCRAPE_INTERVAL_MINUTES),
        ("generate", GENERATE_INTERVAL_MINUTES),
        ("research", RESEARCH_INTERVAL_MINUTES),
        ("deploy", DEPLOY_INTERVAL_MINUTES),
        ("optimize", OPTIMIZE_INTERVAL_MINUTES),
        ("health", HEALTH_INTERVAL_MINUTES),
        ("presence", PRESENCE_INTERVAL_MINUTES),
    ]

    next_tasks = []
    for task, interval in tasks:
        last = scheduler.state.get(task)
        if not last:
            next_tasks.append((task, datetime.now()))
        else:
            next_dt = datetime.fromisoformat(last) + timedelta(minutes=interval)
            next_tasks.append((task, next_dt))

    next_tasks.sort(key=lambda x: x[1])
    next_task, next_time = next_tasks[0]
    wait = max(0, (next_time - datetime.now()).total_seconds())

    if wait > 0:
        mins = wait / 60
        print(f"\n[{datetime.now().strftime('%H:%M')}] Next: '{next_task}' in {mins:.0f}min")
        # Sleep in 30s chunks for responsive Ctrl+C
        while wait > 0:
            time.sleep(min(wait, 30))
            wait -= 30
    else:
        time.sleep(2)
