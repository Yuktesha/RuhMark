"""
RuhMark (如標) AI Benchmark & Corpus Preprocessor Platform
ruhmark.bilingual - 英漢平行對齊雙語語料庫抽取器 (Bilingual Parallel Aligner)
"""

import re
import csv
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass

from .cleaner import NoiseCleaner
from .normalizer import TextNormalizer


@dataclass
class BilingualPair:
    """單一雙語對齊語料配對"""
    pair_id: str
    source_file: str
    en_text: str
    zh_text: str
    it_text: str = ""
    citation_en: str = ""
    citation_zh: str = ""
    metadata: Dict[str, Any] = None


class BilingualAligner:
    """英漢雙語對齊語料庫抽取與建構器"""

    TSV_HEADER = [
        "PAIR_ID",
        "SOURCE_FILE",
        "EN_TEXT",
        "ZH_TEXT",
        "IT_TEXT",
        "CITATION_EN",
        "CITATION_ZH",
        "EN_CHAR_LEN",
        "ZH_CHAR_LEN",
    ]

    @classmethod
    def parse_txt_card_file(cls, file_path: Path) -> Optional[BilingualPair]:
        """解析單一圖卡 TXT 檔案，萃取英、義、中三語正文與出處引用"""
        try:
            raw_text = file_path.read_text(encoding="utf-8", errors="replace").strip()
        except Exception:
            return None

        if not raw_text:
            return None

        # 依空行分割區塊
        blocks = [b.strip() for b in re.split(r"\n\s*\n\s*\n|\n\s*\n", raw_text) if b.strip()]
        if len(blocks) < 2:
            return None

        en_quote = ""
        en_citation = ""
        it_quote = ""
        it_citation = ""
        zh_quote = ""
        zh_citation = ""

        # 啟發式識別各語言區塊
        # 義大利文特徵字
        it_markers = [" della ", " degli ", " spirituale ", " perché ", " nel ", " quando ", " vita quotidiana ", " parte del "]

        i = 0
        n = len(blocks)
        while i < n:
            b = blocks[i]

            # 忽略純 URL
            if b.startswith("http://") or b.startswith("https://"):
                i += 1
                continue

            # 1. 中文區塊
            if re.search(r"[\u4e00-\u9fff]{10,}", b):
                if not zh_quote:
                    zh_quote = b
                    # 下一區塊若為短行中文字則視為出處引用
                    if i + 1 < n and len(blocks[i + 1]) < 180 and ("卷" in blocks[i + 1] or "大法會" in blocks[i + 1] or "Shrii" in blocks[i + 1] or "P." in blocks[i + 1]):
                        zh_citation = blocks[i + 1]
                        i += 1
                i += 1
                continue

            # 2. 義大利文區塊
            if any(m in f" {b.lower()} " for m in it_markers):
                if not it_quote:
                    it_quote = b
                    if i + 1 < n and len(blocks[i + 1]) < 180 and ("DMC" in blocks[i + 1] or "Subh" in blocks[i + 1] or "Parte" in blocks[i + 1] or "Shrii" in blocks[i + 1]):
                        it_citation = blocks[i + 1]
                        i += 1
                i += 1
                continue

            # 3. 英文區塊 (無中文且非義大利文)
            if re.search(r"^[A-Za-z0-9\s,\.\–\-\'\’\(\)\"\:\;\?\!]{25,}", b):
                if not en_quote:
                    en_quote = b
                    if i + 1 < n and len(blocks[i + 1]) < 180 and ("DMC" in blocks[i + 1] or "Part" in blocks[i + 1] or "Discourse" in blocks[i + 1] or "Shrii" in blocks[i + 1]):
                        en_citation = blocks[i + 1]
                        i += 1
                i += 1
                continue

            i += 1

        # 若同時具備英文與中文
        if en_quote and zh_quote:
            # 清洗常規化
            en_clean, _ = NoiseCleaner.clean_all(en_quote)
            zh_clean, _ = TextNormalizer.normalize_all(zh_quote)
            it_clean, _ = NoiseCleaner.clean_all(it_quote) if it_quote else ("", {})

            return BilingualPair(
                pair_id=f"pair_{file_path.stem}",
                source_file=file_path.name,
                en_text=en_clean.replace("\n", " ").strip(),
                zh_text=zh_clean.replace("\n", " ").strip(),
                it_text=it_clean.replace("\n", " ").strip() if isinstance(it_clean, str) else "",
                citation_en=en_citation.replace("\n", " | ").strip(),
                citation_zh=zh_citation.replace("\n", " | ").strip(),
            )

        return None

    @classmethod
    def align_directory(cls, dir_path: str, output_tsv: str) -> Tuple[List[BilingualPair], int]:
        """批次讀取資料夾並匯出高品質英漢對齊 TSV 語料庫"""
        p = Path(dir_path)
        pairs = []
        total_scanned = 0

        # 優先搜尋 .txt 檔案
        for txt_f in sorted(p.glob("**/*.txt")):
            total_scanned += 1
            pair = cls.parse_txt_card_file(txt_f)
            if pair:
                pairs.append(pair)

        # 匯出 TSV
        out_p = Path(output_tsv)
        out_p.parent.mkdir(parents=True, exist_ok=True)

        with open(out_p, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f, delimiter="\t", quoting=csv.QUOTE_MINIMAL)
            writer.writerow(cls.TSV_HEADER)

            for pr in pairs:
                writer.writerow([
                    pr.pair_id,
                    pr.source_file,
                    pr.en_text.replace("\t", " "),
                    pr.zh_text.replace("\t", " "),
                    pr.it_text.replace("\t", " "),
                    pr.citation_en.replace("\t", " "),
                    pr.citation_zh.replace("\t", " "),
                    len(pr.en_text),
                    len(pr.zh_text),
                ])

        return pairs, total_scanned
