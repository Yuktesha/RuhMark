"""
RuhMark (如標) AI Benchmark & Corpus Preprocessor Platform
ruhmark.fetcher.wiki_fetcher - 維基百科與知識庫純文字百科語料採集器
"""

import urllib.request
import urllib.parse
import json
import uuid
from typing import Optional, List, Dict, Any

from .models import SourceType, SourceMetadata, FetchResult
from .web_scraper import WebScraper


class WikiFetcher:
    """繁體中文維基百科 (zh.wikipedia.org) 知識條目抽取器"""

    BASE_API = "https://zh.wikipedia.org/w/api.php"

    @classmethod
    def fetch_article(cls, title: str, variant: str = "zh-tw") -> FetchResult:
        """依條目標題抓取維基百科純文字內文 (explaintext=1 自動過濾 Wiki markup 與 HTML)"""
        source_id = f"wiki_{uuid.uuid4().hex[:8]}"
        origin_url = f"https://zh.wikipedia.org/wiki/{urllib.parse.quote(title)}"
        meta = SourceMetadata(
            source_id=source_id,
            source_type=SourceType.WIKI,
            origin_url=origin_url,
            title=title,
            license="CC-BY-SA 4.0"
        )

        params = {
            "action": "query",
            "format": "json",
            "titles": title,
            "prop": "extracts",
            "explaintext": "1",      # 要求純文字輸出，不帶 HTML
            "redirects": "1",        # 自動重定向別名
            "uselang": variant       # 指定繁體中文 (zh-tw)
        }

        query_str = urllib.parse.urlencode(params)
        req_url = f"{cls.BASE_API}?{query_str}"

        headers = {
            "User-Agent": WebScraper.DEFAULT_USER_AGENT,
            "Accept": "application/json"
        }
        req = urllib.request.Request(req_url, headers=headers)

        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode("utf-8"))

            pages = data.get("query", {}).get("pages", {})
            if not pages:
                return FetchResult(success=False, source_meta=meta, error_message=f"查無條目: {title}")

            for page_id, p_info in pages.items():
                if page_id == "-1":
                    return FetchResult(success=False, source_meta=meta, error_message=f"條目不存在: {title}")

                real_title = p_info.get("title", title)
                extract_text = p_info.get("extract", "").strip()

                meta.title = real_title
                meta.char_len = len(extract_text)

                return FetchResult(
                    success=True,
                    source_meta=meta,
                    raw_content=extract_text,
                    extracted_text=f"# {real_title}\n\n{extract_text}",
                )

            return FetchResult(success=False, source_meta=meta, error_message="未獲取到有效內文")

        except Exception as e:
            return FetchResult(success=False, source_meta=meta, error_message=f"維基百科請求失敗: {e}")
