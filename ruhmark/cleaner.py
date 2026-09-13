"""
RuhMark (如標) AI Benchmark & Corpus Preprocessor Platform
ruhmark.cleaner - 雜訊、HTML標籤、廣告樣板與極端重複清洗器
"""

import re
import html
from typing import Tuple, Dict, Any, List


class NoiseCleaner:
    """網頁雜訊、垃圾文本與媒體罐頭樣板過濾器"""

    # HTML 標籤正則
    HTML_TAGS_REGEX = re.compile(r"<[^>]+>", re.DOTALL)
    # HTML 實體
    HTML_ENTITIES_REGEX = re.compile(r"&[a-zA-Z]+;|&#\d+;")

    # URL 正則 (http, https, ftp, www)
    URL_REGEX = re.compile(
        r"(https?://\S+|www\.[a-zA-Z0-9-]+\.[a-zA-Z0-9-.\~]+|ftp://\S+)",
        re.IGNORECASE
    )

    # Email 正則
    EMAIL_REGEX = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")

    # IP 位址
    IP_REGEX = re.compile(r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b")

    # Markdown 超連結與圖片 [標題](url) / ![圖片](url)
    MARKDOWN_LINK_REGEX = re.compile(r"!*\[([^\]]*)\]\([^)]+\)")

    # 社群 Hashtag 與 @提及
    HASHTAG_REGEX = re.compile(r"#[\w\u4e00-\u9fff]+(?:\s|$)")
    MENTION_REGEX = re.compile(r"@[\w.-]+(?:\s|$)")

    # 新聞媒體常見結尾/樣板黑名單 (正則列表)
    BOILERPLATE_PATTERNS = [
        re.compile(r"^\s*(?:記者|責任編輯|編譯|專題報導|即時中心).*?(?:／|/|報導|整理報導|電|述|攝)\s*.*$"),
        re.compile(r".*版權所有.*?(?:翻印必究|未經授權|嚴禁轉載).*"),
        re.compile(r".*(?:點(?:我|擊)?(?:下載|閱讀|看更多|看|收看)|延伸閱讀|相關新聞|看更多(?:新聞)?|加入好友).*"),
        re.compile(r"^\s*(?:廣告|贊助內容|Sponsored|ADVERTISEMENT)\s*$", re.IGNORECASE),
        re.compile(r".*(?:追蹤我們|請鎖定|請訂閱|歡迎分享).*"),
        re.compile(r"^[-=_*]{3,}$"),  # 分隔線
    ]

    # 重複標點正規化
    REPEATED_PUNCT_PATTERNS = [
        (re.compile(r"！{2,}"), "！"),
        (re.compile(r"？{2,}"), "？"),
        (re.compile(r"。{2,}"), "。"),
        (re.compile(r"，{2,}"), "，"),
        (re.compile(r"、{2,}"), "、"),
        (re.compile(r"；{2,}"), "；"),
        (re.compile(r"：{2,}"), "："),
        (re.compile(r"～{2,}"), "～"),
    ]

    @classmethod
    def clean_html(cls, text: str) -> Tuple[str, int]:
        """清除 HTML 標籤與反轉義 HTML 實體 (如 &amp; -> &)"""
        # 先去除 <script> 和 <style> 及其內容
        text = re.sub(r"<(script|style)[^>]*>.*?</\1>", "", text, flags=re.DOTALL | re.IGNORECASE)
        # 清除所有 HTML tags
        new_text, tag_count = cls.HTML_TAGS_REGEX.subn(" ", text)
        # 解碼實體字符
        new_text = html.unescape(new_text)
        return new_text, tag_count

    @classmethod
    def clean_markdown(cls, text: str) -> str:
        """清除 Markdown 連結只保留文字，並去除表格線"""
        # [文字](網址) -> 文字
        text = cls.MARKDOWN_LINK_REGEX.sub(r"\1", text)
        # 移除表格線 |---|---|
        text = re.sub(r"\|(?:\s*:?-+:?\s*\|)+", "", text)
        return text

    @classmethod
    def clean_urls_and_emails(cls, text: str, replace_with: str = "") -> Tuple[str, int]:
        """清除或替換 URL 與 Email"""
        text, url_count = cls.URL_REGEX.subn(replace_with, text)
        text, email_count = cls.EMAIL_REGEX.subn(replace_with, text)
        text, ip_count = cls.IP_REGEX.subn(replace_with, text)
        return text, (url_count + email_count + ip_count)

    @classmethod
    def clean_social_tags(cls, text: str) -> str:
        """清除社群 hashtag 與 @ 提及"""
        text = cls.HASHTAG_REGEX.sub("", text)
        text = cls.MENTION_REGEX.sub("", text)
        return text

    @classmethod
    def compress_repeated_punctuation(cls, text: str) -> Tuple[str, int]:
        """壓縮連續多餘標點符號 (例如 ！！！ -> ！)"""
        total_compressed = 0
        for pattern, replacement in cls.REPEATED_PUNCT_PATTERNS:
            text, cnt = pattern.subn(replacement, text)
            total_compressed += cnt
        return text, total_compressed

    @classmethod
    def compress_repeated_characters(cls, text: str, max_repeat: int = 3) -> str:
        """限制中英文字元連續重複上限 (例如 "哈哈哈哈哈哈" 限制為 "哈哈哈")"""
        pattern = re.compile(r"(.)\1{" + str(max_repeat) + r",}")
        return pattern.sub(lambda m: m.group(1) * max_repeat, text)

    @classmethod
    def is_boilerplate(cls, line: str) -> bool:
        """檢查單行文字是否為廣告/新聞樣板/版權聲明"""
        clean_line = line.strip()
        if not clean_line:
            return True
        for pat in cls.BOILERPLATE_PATTERNS:
            if pat.match(clean_line):
                return True
        return False

    @classmethod
    def clean_all(
        cls,
        text: str,
        remove_html: bool = True,
        remove_urls: bool = True,
        remove_social: bool = True,
        compress_punct: bool = True,
        max_repeat: int = 3
    ) -> Tuple[str, Dict[str, int]]:
        """執行綜合雜訊清洗，回傳 (清洗後字串, 統計資訊)"""
        stats = {
            "html_tags": 0,
            "urls_and_emails": 0,
            "punct_compressed": 0,
        }

        if remove_html:
            text, h_cnt = cls.clean_html(text)
            stats["html_tags"] = h_cnt

        text = cls.clean_markdown(text)

        if remove_urls:
            text, u_cnt = cls.clean_urls_and_emails(text)
            stats["urls_and_emails"] = u_cnt

        if remove_social:
            text = cls.clean_social_tags(text)

        if compress_punct:
            text, p_cnt = cls.compress_repeated_punctuation(text)
            stats["punct_compressed"] = p_cnt

        if max_repeat > 0:
            text = cls.compress_repeated_characters(text, max_repeat=max_repeat)

        return text.strip(), stats
