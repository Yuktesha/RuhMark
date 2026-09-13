"""
RuhMark (如標) AI Benchmark & Corpus Preprocessor Platform
ruhmark.fetcher.source_manager - 來源註冊表與原始語料倉儲 (100% TSV 標準)
"""

import os
import csv
import re
from pathlib import Path
from typing import List, Dict, Optional, Tuple

from .models import SourceMetadata, FetchResult, SourceType


class SourceManager:
    """語料來源中繼資料與原始倉儲管理器"""

    REGISTRY_FILENAME = "source_registry.tsv"
    TSV_HEADER = [
        "SOURCE_ID",
        "SOURCE_TYPE",
        "ORIGIN_URL",
        "TITLE",
        "FETCH_TIME",
        "ENCODING",
        "CHAR_LEN",
        "LICENSE",
        "RAW_FILE",
    ]

    def __init__(self, storage_dir: str):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.registry_path = self.storage_dir / self.REGISTRY_FILENAME
        self._ensure_registry()

    def _ensure_registry(self):
        """若無註冊表則初始化建立表頭"""
        if not self.registry_path.exists():
            with open(self.registry_path, "w", encoding="utf-8", newline="") as f:
                writer = csv.writer(f, delimiter="\t")
                writer.writerow(self.TSV_HEADER)

    @staticmethod
    def _sanitize_filename(name: str, max_len: int = 40) -> str:
        """過濾檔名非法字元"""
        clean = re.sub(r'[\\/*?:"<>|]', "", name).strip().replace(" ", "_")
        return clean[:max_len] if clean else "untitled"

    def is_url_registered(self, url: str) -> bool:
        """檢查該 URL 是否已抓取登記過"""
        if not self.registry_path.exists():
            return False
        with open(self.registry_path, "r", encoding="utf-8") as f:
            reader = csv.reader(f, delimiter="\t")
            for idx, row in enumerate(reader):
                if idx == 0 or len(row) < 3:
                    continue
                if row[2] == url:
                    return True
        return False

    def save_fetch_result(self, result: FetchResult, overwrite: bool = False) -> Optional[SourceMetadata]:
        """將抓取結果之原始文字儲存為檔案，並於 TSV 註冊表追加一筆紀錄"""
        if not result.success:
            return None

        meta = result.source_meta
        if not overwrite and self.is_url_registered(meta.origin_url):
            return meta

        safe_title = self._sanitize_filename(meta.title or "corpus")
        raw_filename = f"{meta.source_id}_{safe_title}.txt"
        file_path = self.storage_dir / raw_filename

        # 寫入文字檔案
        content_to_save = result.extracted_text or result.raw_content
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content_to_save)

        meta.raw_file_path = str(file_path)
        meta.char_len = len(content_to_save)

        # 登記至 TSV
        with open(self.registry_path, "a", encoding="utf-8", newline="") as f:
            writer = csv.writer(f, delimiter="\t")
            safe_title_tsv = meta.title.replace("\t", " ").replace("\n", " ")
            writer.writerow([
                meta.source_id,
                meta.source_type.value,
                meta.origin_url,
                safe_title_tsv,
                meta.fetch_time,
                meta.encoding,
                meta.char_len,
                meta.license,
                raw_filename,
            ])

        return meta

    def list_sources(self) -> List[Dict[str, str]]:
        """讀取所有已登記之來源清單"""
        if not self.registry_path.exists():
            return []
        sources = []
        with open(self.registry_path, "r", encoding="utf-8") as f:
            reader = csv.reader(f, delimiter="\t")
            header = None
            for idx, row in enumerate(reader):
                if not row or not any(row):
                    continue
                if idx == 0:
                    header = row
                    continue
                if header and len(row) == len(header):
                    sources.append(dict(zip(header, row)))
        return sources
