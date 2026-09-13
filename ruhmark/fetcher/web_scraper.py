"""
RuhMark (如標) AI Benchmark & Corpus Preprocessor Platform
ruhmark.fetcher.web_scraper - 雙軌網頁核心內文抽取器 (Zero-Dependency + Pluggable)
"""

import re
import urllib.request
import urllib.error
import http.client
from html.parser import HTMLParser
from typing import Tuple, Optional, Dict, Any
from pathlib import Path

from .models import SourceType, SourceMetadata, FetchResult


class ReadabilityExtractor(HTMLParser):
    """
    零依賴純標準庫核心正文抽取器：
    1. 濾除導覽列、頁尾、廣告、腳本等雜訊標籤
    2. 自動提取文章標題與主要段落內容
    """

    IGNORE_TAGS = set([
        "script", "style", "noscript", "svg", "nav", "header", "footer",
        "aside", "form", "button", "input", "select", "textarea", "iframe"
    ])

    BLOCK_TAGS = set(["p", "div", "article", "section", "blockquote", "li", "h1", "h2", "h3", "h4", "h5", "h6"])

    def __init__(self):
        super().__init__()
        self.ignore_depth = 0
        self.in_title = False
        self.title_parts = []
        self.paragraphs = []
        self.current_block = []
        self.heading_prefix = ""

    def handle_starttag(self, tag: str, attrs: list):
        tag_lower = tag.lower()
        if tag_lower in self.IGNORE_TAGS:
            self.ignore_depth += 1
            return

        if self.ignore_depth > 0:
            return

        if tag_lower == "title":
            self.in_title = True

        if tag_lower in ["h1", "h2", "h3", "h4", "h5", "h6"]:
            level = int(tag_lower[1])
            self.heading_prefix = "#" * level + " "

        if tag_lower in self.BLOCK_TAGS:
            self._flush_current_block()

    def handle_endtag(self, tag: str):
        tag_lower = tag.lower()
        if tag_lower in self.IGNORE_TAGS:
            if self.ignore_depth > 0:
                self.ignore_depth -= 1
            return

        if self.ignore_depth > 0:
            return

        if tag_lower == "title":
            self.in_title = False

        if tag_lower in self.BLOCK_TAGS:
            self._flush_current_block()
            self.heading_prefix = ""

    def handle_data(self, data: str):
        if self.ignore_depth > 0:
            return

        if self.in_title:
            self.title_parts.append(data.strip())
            return

        text = data.strip()
        if text:
            if self.heading_prefix and not self.current_block:
                self.current_block.append(self.heading_prefix)
            self.current_block.append(text)

    def _flush_current_block(self):
        if self.current_block:
            line = " ".join(self.current_block).strip()
            # 濾除過短的無意義雜訊字串 (如純符號或空行)
            if len(line) >= 4 or line.startswith("#"):
                self.paragraphs.append(line)
            self.current_block = []

    def get_extracted_content(self) -> Tuple[str, str]:
        self._flush_current_block()
        title = " ".join(self.title_parts).strip()
        body = "\n\n".join(self.paragraphs)
        return title, body


class WebScraper:
    """網頁爬取與結構化正文抽取器"""

    DEFAULT_USER_AGENT = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/128.0.0.0 Safari/537.36 RuhOS/1.0"
    )

    @classmethod
    def fetch_url(cls, url: str, timeout: int = 15) -> FetchResult:
        """從網路 URL 抓取網頁原始 HTML 並抽取乾淨正文"""
        import uuid
        source_id = f"web_{uuid.uuid4().hex[:8]}"
        meta = SourceMetadata(
            source_id=source_id,
            source_type=SourceType.WEB,
            origin_url=url,
        )

        headers = {
            "User-Agent": cls.DEFAULT_USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7",
        }

        req = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                raw_bytes = resp.read()
                content_type = resp.headers.get("Content-Type", "")

                # 嘗試推測編碼
                encoding = "utf-8"
                if "charset=" in content_type.lower():
                    m = re.search(r"charset=([\w\-]+)", content_type, re.IGNORECASE)
                    if m:
                        encoding = m.group(1).lower()

                try:
                    html_text = raw_bytes.decode(encoding)
                except (UnicodeDecodeError, LookupError):
                    for enc in ["utf-8", "big5", "cp950", "gb18030", "latin-1"]:
                        try:
                            html_text = raw_bytes.decode(enc)
                            encoding = enc
                            break
                        except UnicodeDecodeError:
                            continue
                    else:
                        html_text = raw_bytes.decode("utf-8", errors="replace")
                        encoding = "utf-8-replace"

                meta.encoding = encoding

                # 抽取核心正文
                title, extracted_text = cls.extract_content(html_text)
                meta.title = title
                meta.char_len = len(extracted_text)

                return FetchResult(
                    success=True,
                    source_meta=meta,
                    raw_content=html_text,
                    extracted_text=extracted_text,
                )

        except Exception as e:
            return FetchResult(
                success=False,
                source_meta=meta,
                error_message=f"抓取失敗: {str(e)}"
            )

    @classmethod
    def extract_content(cls, html_text: str) -> Tuple[str, str]:
        """優先嘗試外掛 Trafilatura，若未安裝則自動調用內建 ReadabilityExtractor"""
        # 1. 嘗試高階可插拔引擎
        try:
            import trafilatura
            extracted = trafilatura.extract(html_text, output_format="txt")
            if extracted:
                # 抽取標題
                m = re.search(r"<title>(.*?)</title>", html_text, re.IGNORECASE | re.DOTALL)
                title = m.group(1).strip() if m else ""
                return title, extracted
        except ImportError:
            pass

        # 2. 內建零依賴 ReadabilityExtractor
        extractor = ReadabilityExtractor()
        try:
            extractor.feed(html_text)
            title, body = extractor.get_extracted_content()
            return title, body
        except Exception:
            # 極端狀況下正規表達式純文本提取
            plain = re.sub(r"<[^>]+>", " ", html_text)
            return "", plain.strip()
