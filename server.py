"""
content-research-mcp — MCP server for content creators
Combines Naver DataLab + Blog/News + Papago + Unsplash into one research tool.

Run: content-research-mcp --env /path/to/.env
"""

import argparse
import sys
import datetime

from mcp.server.fastmcp import FastMCP

import core.naver as naver
import core.unsplash as unsplash

mcp = FastMCP("content-research")


# ──────────────────────────────────────────────
# API Status Tool
# ──────────────────────────────────────────────

@mcp.tool()
def api_status() -> str:
    """Check which APIs are configured and available."""
    naver_ok = naver.is_available()
    unsplash_ok = unsplash.is_available()

    lines = ["## API Status\n"]
    lines.append(f"  Naver (Blog/News/Trend/Translate): {'[OK] Ready' if naver_ok else '[--] Not configured (https://developers.naver.com)'}")
    lines.append(f"  Unsplash (Images):                 {'[OK] Ready' if unsplash_ok else '[--] Not configured (https://unsplash.com/developers)'}")
    lines.append("")

    available = sum([naver_ok, unsplash_ok])
    if available == 2:
        lines.append("All APIs configured. Full functionality available.")
    elif available == 0:
        lines.append("No API keys configured. Add keys to .env file to enable features.")
        lines.append("Run: python setup_wizard.py")
    else:
        lines.append(f"{available}/2 APIs configured. Missing APIs will be skipped in research reports.")

    return "\n".join(lines)


# ──────────────────────────────────────────────
# Individual Tools
# ──────────────────────────────────────────────

@mcp.tool()
def trend_keywords(keywords: list[str], months: int = 6) -> str:
    """Analyze Naver search trends for given keywords.

    - keywords: List of keywords to compare (max 5)
    - months: How many months back to analyze (default: 6)
    """
    end = datetime.date.today()
    start = end - datetime.timedelta(days=months * 30)

    keyword_groups = [[kw] for kw in keywords[:5]]

    try:
        data = naver.get_trend(
            keyword_groups,
            start_date=start.isoformat(),
            end_date=end.isoformat(),
            time_unit="month" if months > 3 else "week",
        )
    except Exception as e:
        return f"[Error] Trend analysis failed: {e}"

    results = data.get("results", [])
    if not results:
        return "No trend data found for the given keywords."

    lines = ["## Naver Search Trend Analysis\n"]
    lines.append(f"Period: {start.isoformat()} ~ {end.isoformat()}\n")

    for group in results:
        name = group.get("title", "")
        data_points = group.get("data", [])
        lines.append(f"### {name}")

        if data_points:
            latest = data_points[-1].get("ratio", 0)
            earliest = data_points[0].get("ratio", 0)
            change = latest - earliest
            direction = "UP" if change > 0 else "DOWN" if change < 0 else "STABLE"
            lines.append(f"  Latest: {latest:.1f} | Change: {change:+.1f} ({direction})")

            peak = max(data_points, key=lambda d: d.get("ratio", 0))
            lines.append(f"  Peak: {peak.get('ratio', 0):.1f} ({peak.get('period', '')})")
        lines.append("")

    return "\n".join(lines)


@mcp.tool()
def search_blogs(query: str, count: int = 5) -> str:
    """Search Naver blogs for a topic. Great for finding popular content and angles.

    - query: Search keyword
    - count: Number of results (default: 5, max: 20)
    """
    try:
        results = naver.search_blog(query, display=min(count, 20))
    except Exception as e:
        return f"[Error] Blog search failed: {e}"

    if not results:
        return f"No blog posts found for '{query}'."

    lines = [f"## Naver Blog Search: '{query}'\n"]
    for i, post in enumerate(results, 1):
        lines.append(f"### {i}. {post['title']}")
        lines.append(f"  By: {post['bloggername']} | Date: {post['postdate']}")
        lines.append(f"  Summary: {post['description']}")
        lines.append(f"  Link: {post['link']}")
        lines.append("")

    return "\n".join(lines)


@mcp.tool()
def search_news(query: str, count: int = 5) -> str:
    """Search latest news articles on Naver.

    - query: Search keyword
    - count: Number of results (default: 5, max: 20)
    """
    try:
        results = naver.search_news(query, display=min(count, 20))
    except Exception as e:
        return f"[Error] News search failed: {e}"

    if not results:
        return f"No news found for '{query}'."

    lines = [f"## Latest News: '{query}'\n"]
    for i, article in enumerate(results, 1):
        lines.append(f"### {i}. {article['title']}")
        lines.append(f"  Date: {article['pubDate']}")
        lines.append(f"  Summary: {article['description']}")
        lines.append(f"  Link: {article['originallink']}")
        lines.append("")

    return "\n".join(lines)


@mcp.tool()
def translate_text(text: str, source: str = "en", target: str = "ko") -> str:
    """Translate text using Naver Papago.

    - text: Text to translate
    - source: Source language code (en, ko, ja, zh-CN, etc.)
    - target: Target language code
    """
    try:
        result = naver.translate(text, source, target)
    except Exception as e:
        return f"[Error] Translation failed: {e}"

    return f"## Translation ({source} -> {target})\n\n{result}"


@mcp.tool()
def search_images(query: str, count: int = 5) -> str:
    """Search free-to-use images on Unsplash.

    - query: Search keyword (English recommended for better results)
    - count: Number of images (default: 5)
    """
    try:
        results = unsplash.search_photos(query, per_page=min(count, 10))
    except Exception as e:
        return f"[Error] Image search failed: {e}"

    if not results:
        return f"No images found for '{query}'."

    lines = [f"## Free Images: '{query}'\n"]
    lines.append("License: Unsplash (free for commercial use, credit appreciated)\n")

    for i, photo in enumerate(results, 1):
        lines.append(f"### {i}. {photo['description'] or 'Untitled'}")
        lines.append(f"  Photographer: {photo['photographer']}")
        lines.append(f"  Profile: {photo['photographer_url']}")
        lines.append(f"  Preview: {photo['url_small']}")
        lines.append(f"  Full size: {photo['url_regular']}")
        lines.append(f"  Download: {photo['download_link']}")
        lines.append("")

    return "\n".join(lines)


# ──────────────────────────────────────────────
# Combined Research Tool (the killer feature)
# ──────────────────────────────────────────────

@mcp.tool()
def research_topic(topic: str, english_topic: str = "") -> str:
    """All-in-one content research: trends + blogs + news + images for a topic.
    This is the main tool — it combines all APIs into a single research report.

    - topic: Research topic in Korean (e.g. '인공지능')
    - english_topic: Same topic in English for image search (e.g. 'artificial intelligence').
                     If empty, uses the Korean topic.
    """
    img_query = english_topic or topic
    sections = []

    sections.append(f"# Content Research Report: {topic}\n")
    sections.append(f"Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
    sections.append("---\n")

    naver_ok = naver.is_available()
    unsplash_ok = unsplash.is_available()

    if not naver_ok and not unsplash_ok:
        sections.append("## No API keys configured\n")
        sections.append("Add API keys to use this tool:")
        sections.append("  - Naver: https://developers.naver.com")
        sections.append("  - Unsplash: https://unsplash.com/developers")
        sections.append("\nRun: python setup_wizard.py")
        return "\n".join(sections)

    # 1. Trend analysis
    sections.append("## 1. Search Trend Analysis\n")
    if naver_ok:
        try:
            end = datetime.date.today()
            start = end - datetime.timedelta(days=180)
            trend_data = naver.get_trend(
                [[topic]],
                start_date=start.isoformat(),
                end_date=end.isoformat(),
                time_unit="month",
            )
            results = trend_data.get("results", [])
            if results and results[0].get("data"):
                data_points = results[0]["data"]
                sections.append(f"Keyword: '{topic}' | Period: {start} ~ {end}\n")
                for dp in data_points:
                    bar = "#" * int(dp.get("ratio", 0) / 2)
                    sections.append(f"  {dp.get('period', '')}: {dp.get('ratio', 0):5.1f} {bar}")
                latest = data_points[-1].get("ratio", 0)
                earliest = data_points[0].get("ratio", 0)
                change = latest - earliest
                direction = "UP" if change > 0 else "DOWN" if change < 0 else "STABLE"
                sections.append(f"\n  Trend: {direction} ({change:+.1f})\n")
            else:
                sections.append("  No trend data available.\n")
        except Exception as e:
            sections.append(f"  [Skipped] Trend analysis error: {e}\n")
    else:
        sections.append("  [Skipped] Naver API key not configured.\n")

    sections.append("---\n")

    # 2. Top blog posts
    sections.append("## 2. Top Blog Posts\n")
    if naver_ok:
        try:
            blogs = naver.search_blog(topic, display=5)
            if blogs:
                for i, post in enumerate(blogs, 1):
                    sections.append(f"  {i}. **{post['title']}**")
                    sections.append(f"     By {post['bloggername']} ({post['postdate']})")
                    sections.append(f"     {post['description'][:120]}...")
                    sections.append(f"     Link: {post['link']}")
                    sections.append("")
            else:
                sections.append("  No blog posts found.\n")
        except Exception as e:
            sections.append(f"  [Skipped] Blog search error: {e}\n")
    else:
        sections.append("  [Skipped] Naver API key not configured.\n")

    sections.append("---\n")

    # 3. Latest news
    sections.append("## 3. Latest News\n")
    if naver_ok:
        try:
            news = naver.search_news(topic, display=5)
            if news:
                for i, article in enumerate(news, 1):
                    sections.append(f"  {i}. **{article['title']}**")
                    sections.append(f"     {article['pubDate']}")
                    sections.append(f"     {article['description'][:120]}...")
                    sections.append(f"     Link: {article['originallink']}")
                    sections.append("")
            else:
                sections.append("  No news found.\n")
        except Exception as e:
            sections.append(f"  [Skipped] News search error: {e}\n")
    else:
        sections.append("  [Skipped] Naver API key not configured.\n")

    sections.append("---\n")

    # 4. Free images
    sections.append("## 4. Free Images (Unsplash)\n")
    if unsplash_ok:
        try:
            photos = unsplash.search_photos(img_query, per_page=3)
            if photos:
                sections.append("License: Free for commercial use (credit appreciated)\n")
                for i, photo in enumerate(photos, 1):
                    sections.append(f"  {i}. {photo['description'] or 'Untitled'}")
                    sections.append(f"     By: {photo['photographer']}")
                    sections.append(f"     Preview: {photo['url_small']}")
                    sections.append(f"     Download: {photo['download_link']}")
                    sections.append("")
            else:
                sections.append("  No images found.\n")
        except Exception as e:
            sections.append(f"  [Skipped] Image search error: {e}\n")
    else:
        sections.append("  [Skipped] Unsplash API key not configured.\n")

    sections.append("---\n")
    sections.append("*Report generated by content-research-mcp*")

    return "\n".join(sections)


# ──────────────────────────────────────────────
# Entry point
# ──────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Content Research MCP Server")
    parser.add_argument(
        "--env",
        default="",
        help="Path to .env file with API keys",
    )
    args = parser.parse_args()

    if args.env:
        from dotenv import load_dotenv
        load_dotenv(args.env)
        print(f"content-research-mcp: loaded env from '{args.env}'", file=sys.stderr)
    else:
        # Try loading .env from the script's directory
        from dotenv import load_dotenv
        env_path = str(__import__("pathlib").Path(__file__).parent / ".env")
        load_dotenv(env_path)

    print("content-research-mcp: server starting", file=sys.stderr)
    mcp.run()


if __name__ == "__main__":
    main()
