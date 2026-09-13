"""
RuhMark (如標) AI Benchmark & Corpus Preprocessor Platform
ruhmark.fetcher.models - 語料採集資料模型與來源中繼結構
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Any, Optional
import time


class SourceType(str, Enum):
    """語料來源類型"""
    WEB = "WEB"    # 一般網頁 / 新聞 / 部落格
    RSS = "RSS"    # RSS / Atom 頻道
    WIKI = "WIKI"  # 維基百科 / 百科辭條
    FILE = "FILE"  # 本地檔案 / 電子書


@dataclass
class SourceMetadata:
    """來源中繼資料 (Source Metadata & Licensing)"""
    source_id: str
    source_type: SourceType
    origin_url: str
    title: str = ""
    author: str = ""
    fetch_time: str = ""
    encoding: str = "utf-8"
    char_len: int = 0
    license: str = "Unknown"  # 例如: CC-BY-SA 4.0, Public Domain, Fair Use
    raw_file_path: str = ""
    extra: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.fetch_time:
            self.fetch_time = time.strftime("%Y-%m-%d %H:%M:%S")


@dataclass
class FetchResult:
    """抓取操作結果物件"""
    success: bool
    source_meta: SourceMetadata
    raw_content: str = ""
    extracted_text: str = ""
    error_message: str = ""
