"""
RuhMark (如標) AI Benchmark & Corpus Preprocessor Platform
ruhmark.fetcher - 語料採集與來源管理器模組
"""

from .models import SourceType, SourceMetadata, FetchResult
from .web_scraper import WebScraper, ReadabilityExtractor
from .rss_collector import RSSCollector
from .wiki_fetcher import WikiFetcher
from .source_manager import SourceManager

__all__ = [
    "SourceType",
    "SourceMetadata",
    "FetchResult",
    "WebScraper",
    "ReadabilityExtractor",
    "RSSCollector",
    "WikiFetcher",
    "SourceManager",
]
