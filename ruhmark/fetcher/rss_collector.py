"""
RuhMark (如標) AI Benchmark & Corpus Preprocessor Platform
ruhmark.fetcher.rss_collector - RSS / Atom 頻道訂閱與語料採集器
"""

import xml.etree.ElementTree as ET
import urllib.request
import re
from typing import List, Dict, Any, Optional
import uuid

from .models import SourceType, SourceMetadata, FetchResult
from .web_scraper import WebScraper


class RSSCollector:
    """RSS / Atom 內容收集器"""

    @classmethod
    def parse_feed_xml(cls, xml_text: str, feed_url: str = "") -> List[Dict[str, str]]:
        """解析 RSS 2.0 或 Atom XML 字串，回傳條目清單"""
        items = []
        try:
            root = ET.fromstring(xml_text)
        except ET.ParseError as e:
            # 去除可能的無效標頭再嘗試一次
            clean_xml = re.sub(r"^[^<]+", "", xml_text).strip()
            try:
                root = ET.fromstring(clean_xml)
            except Exception:
                return []

        # 1. 嘗試 RSS 2.0 (channel -> item)
        channel = root.find("channel")
        if channel is not None:
            for it in channel.findall("item"):
                title_el = it.find("title")
                link_el = it.find("link")
                desc_el = it.find("description")
                content_el = it.find("{http://purl.org/rss/1.0/modules/content/}encoded")

                title = title_el.text.strip() if title_el is not None and title_el.text else ""
                link = link_el.text.strip() if link_el is not None and link_el.text else ""
                
                content = ""
                if content_el is not None and content_el.text:
                    content = content_el.text.strip()
                elif desc_el is not None and desc_el.text:
                    content = desc_el.text.strip()

                items.append({
                    "title": title,
                    "link": link,
                    "content": content,
                    "type": "rss2.0"
                })
            return items

        # 2. 嘗試 Atom 1.0 (feed -> entry)
        # 處理命名空間
        ns = {"atom": "http://www.w3.org/2005/Atom"}
        entries = root.findall("atom:entry", ns) or root.findall("entry")
        for ent in entries:
            title_el = ent.find("atom:title", ns) or ent.find("title")
            link_el = ent.find("atom:link", ns) or ent.find("link")
            summary_el = ent.find("atom:summary", ns) or ent.find("summary")
            content_el = ent.find("atom:content", ns) or ent.find("content")

            title = title_el.text.strip() if title_el is not None and title_el.text else ""
            link = ""
            if link_el is not None:
                link = link_el.attrib.get("href", link_el.text or "").strip()

            content = ""
            if content_el is not None and content_el.text:
                content = content_el.text.strip()
            elif summary_el is not None and summary_el.text:
                content = summary_el.text.strip()

            items.append({
                "title": title,
                "link": link,
                "content": content,
                "type": "atom"
            })

        return items

    @classmethod
    def fetch_feed(cls, feed_url: str, fetch_full_articles: bool = False, max_items: int = 10) -> List[FetchResult]:
        """抓取並解析 RSS/Atom 頻道，若 fetch_full_articles 為 True，則會進一步抓取文章完整內文"""
        headers = {
            "User-Agent": WebScraper.DEFAULT_USER_AGENT,
            "Accept": "application/rss+xml, application/atom+xml, text/xml;q=0.9, */*;q=0.8"
        }
        req = urllib.request.Request(feed_url, headers=headers)
        
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                xml_bytes = resp.read()
                xml_text = xml_bytes.decode("utf-8", errors="replace")
        except Exception as e:
            err_meta = SourceMetadata(
                source_id=f"rss_err_{uuid.uuid4().hex[:6]}",
                source_type=SourceType.RSS,
                origin_url=feed_url
            )
            return [FetchResult(success=False, source_meta=err_meta, error_message=f"RSS 請求失敗: {e}")]

        feed_items = cls.parse_feed_xml(xml_text, feed_url=feed_url)
        results = []

        for it in feed_items[:max_items]:
            link = it.get("link", "")
            title = it.get("title", "")
            snippet_content = it.get("content", "")

            source_id = f"rss_{uuid.uuid4().hex[:8]}"
            meta = SourceMetadata(
                source_id=source_id,
                source_type=SourceType.RSS,
                origin_url=link or feed_url,
                title=title,
            )

            # 若需要抓取全文且有連結
            if fetch_full_articles and link and link.startswith("http"):
                full_res = WebScraper.fetch_url(link)
                if full_res.success:
                    meta.char_len = len(full_res.extracted_text)
                    results.append(FetchResult(
                        success=True,
                        source_meta=meta,
                        raw_content=full_res.raw_content,
                        extracted_text=full_res.extracted_text
                    ))
                    continue

            # 否則使用摘要正文
            # 清理摘要內可能含有的 HTML tags
            from ..cleaner import NoiseCleaner
            clean_snippet, _ = NoiseCleaner.clean_all(snippet_content)
            meta.char_len = len(clean_snippet)
            results.append(FetchResult(
                success=True,
                source_meta=meta,
                raw_content=snippet_content,
                extracted_text=f"# {title}\n\n{clean_snippet}" if title else clean_snippet
            ))

        return results
