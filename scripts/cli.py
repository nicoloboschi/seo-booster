import json

import click

from scripts.scrape import scrape_sources
from scripts.generate import generate_articles
from scripts.seo_stats import fetch_seo_stats, print_report, suggest_optimizations


@click.group()
def cli():
    """SEO Booster — AI memory content pipeline."""
    pass


@cli.command()
@click.option("--config", default="data/sources.yaml", help="Sources config file")
@click.option("--output", default="data/scraped", help="Output directory for scraped content")
def scrape(config, output):
    """Scrape content from RSS feeds, blogs, and news sources."""
    scrape_sources(config, output)


@cli.command()
@click.option("--input-dir", default="data/scraped", help="Directory with scraped content")
@click.option("--output-dir", default="content/articles", help="Hugo content output directory")
@click.option("--keywords", default="data/keywords.yaml", help="Target keywords config")
@click.option("--count", default=10, help="Number of articles to generate")
@click.option("--no-expand", is_flag=True, help="Don't auto-expand keywords with AI")
@click.option("--dry-run", is_flag=True, help="Preview without writing files")
def generate(input_dir, output_dir, keywords, count, no_expand, dry_run):
    """Generate SEO-optimized articles from scraped content using Gemini."""
    generate_articles(input_dir, output_dir, keywords, dry_run,
                      count=count, auto_expand=not no_expand)


@cli.command()
@click.option("--site-url", default="https://aiagentmemory.org/", help="Site URL in Search Console")
@click.option("--days", default=28, help="Number of days to look back")
@click.option("--output", default="data/seo-report.json", help="Output report file")
def stats(site_url, days, output):
    """Fetch SEO stats from Google Search Console (uses Application Default Credentials)."""
    data = fetch_seo_stats(None, site_url, days)
    print_report(data)
    suggestions = suggest_optimizations(data)
    for s in suggestions:
        click.echo(f"  → {s}")
    # Save report for optimize command
    from pathlib import Path
    Path(output).parent.mkdir(parents=True, exist_ok=True)
    Path(output).write_text(json.dumps(data, indent=2))
    click.echo(f"\n  Report saved to {output}")


@cli.command()
@click.option("--report", default="data/seo-report.json", help="SEO report to optimize from")
@click.option("--content-dir", default="content/articles", help="Content directory")
def optimize(report, content_dir):
    """Apply AI-suggested optimizations to underperforming articles."""
    from scripts.optimize import apply_optimizations
    apply_optimizations(report, content_dir)


@cli.command()
@click.option("--keywords", default="data/keywords.yaml", help="Keywords config file")
@click.option("--add-opportunities", is_flag=True, help="Auto-add discovered keywords to config")
@click.option("--max-add", default=20, help="Max new keywords to add")
def research(keywords, add_opportunities, max_add):
    """Research and validate keywords via Google Autocomplete."""
    from scripts.keyword_research import research_and_validate, add_opportunities_to_config
    report = research_and_validate(keywords)
    if add_opportunities and report:
        add_opportunities_to_config("data/keyword-research.json", keywords, max_add)


@cli.command()
@click.option("--content-dir", default="content/articles", help="Content directory")
def validate(content_dir):
    """Validate and fix SEO front matter on all articles."""
    from scripts.postprocess import postprocess_all
    print("Validating and fixing article front matter...\n")
    results = postprocess_all(content_dir)
    total_fixes = sum(len(f) for f in results.values())
    ok_count = sum(1 for f in results.values() if not f)
    print(f"\n{ok_count}/{len(results)} articles OK, {total_fixes} total fixes applied.")


@cli.command()
def health():
    """Run a full health check: site status, GSC data, content freshness."""
    from scripts.health import run_health_check, print_health_report, save_health_history
    report = run_health_check()
    print_health_report(report)
    save_health_history(report)


@cli.command()
def presence():
    """Test if LLMs mention Hindsight when asked about AI memory."""
    from scripts.llm_presence import run_presence_test, print_presence_report, save_presence_history
    report = run_presence_test()
    print_presence_report(report)
    save_presence_history(report)


@cli.command()
@click.option("--content-dir", default="content/articles", help="Content directory")
@click.option("--port", default=1313, help="Hugo server port")
def audit(content_dir, port):
    """Run a full SEO audit: validate front matter + check built HTML."""
    from scripts.postprocess import postprocess_all
    from scripts.seo_audit import audit_html

    print("Step 1: Validating front matter...\n")
    results = postprocess_all(content_dir)
    total_fixes = sum(len(f) for f in results.values())
    print(f"\n  {total_fixes} fixes applied.\n")

    print("Step 2: Building site and auditing HTML...\n")
    audit_html()


@cli.command()
@click.option("--scrape-interval", default=30, help="Minutes between scrapes")
@click.option("--generate-interval", default=120, help="Minutes between generation batches")
@click.option("--articles-per-batch", default=5, help="Articles per generation batch")
@click.option("--deploy-interval", default=30, help="Minutes between deploys")
@click.option("--optimize-interval", default=60, help="Minutes between GSC optimization checks")
def run(scrape_interval, generate_interval, articles_per_batch, deploy_interval, optimize_interval):
    """Run the daemon — continuously scrape, generate, audit, deploy. Runs 24/7."""
    from scripts import daemon
    daemon.SCRAPE_INTERVAL_MINUTES = scrape_interval
    daemon.GENERATE_INTERVAL_MINUTES = generate_interval
    daemon.ARTICLES_PER_BATCH = articles_per_batch
    daemon.DEPLOY_INTERVAL_MINUTES = deploy_interval
    daemon.OPTIMIZE_INTERVAL_MINUTES = optimize_interval
    daemon.run_daemon()


if __name__ == "__main__":
    cli()
