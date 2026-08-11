"""
Stage 1: Trend Discovery
Sumber utama: trendspyg - discovery-first, TANPA seed keyword.
Ambil topik apapun yang lagi viral di Indonesia (lintas-domain:
politik, hiburan, olahraga, hukum, dst), baru difilter manual
mana yang punya celah keuangan di Stage 2.
"""

from trendspyg import download_google_trends_rss
import time


def get_viral_topics(geo='ID', limit=20):
    try:
        trends = download_google_trends_rss(geo=geo)
    except Exception as e:
        print(f"Error ambil trending: {e}")
        return []

    results = []
    for t in trends[:limit]:
        entry = {
            'trend': t.get('trend'),
            'traffic': t.get('traffic'),
            'headline': None,
            'news_url': None
        }
        articles = t.get('news_articles')
        if articles:
            entry['headline'] = articles[0].get('headline')
            entry['news_url'] = articles[0].get('url')
        results.append(entry)

    return results


def print_viral_topics(topics):
    print(f"=== {len(topics)} Topik Viral Indonesia ===\n")
    for i, t in enumerate(topics, 1):
        print(f"{i}. {t['trend']} (traffic: {t['traffic']})")
        if t['headline']:
            print(f"   -> {t['headline']}")
        print()


def discover_trends(geo='ID', limit=20):
    topics = get_viral_topics(geo=geo, limit=limit)
    print_viral_topics(topics)
    return topics


if __name__ == "__main__":
    discover_trends()
