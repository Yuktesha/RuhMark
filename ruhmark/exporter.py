"""
RuhMark (如標) AI Benchmark & Corpus Preprocessor Platform
ruhmark.exporter - 標準 TSV 試算表匯出與基準資料集切分器
"""

import os
import csv
import random
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from .models import CorpusItem, DifficultyLevel, CleaningStats


class DatasetExporter:
    """遵循 ATGprjs 100% TSV 第一標準之資料集匯出與切分器"""

    TSV_HEADER = [
        "CORPUS_ID",
        "CATEGORY",
        "DIFFICULTY",
        "CHAR_LEN",
        "OOV_RATE",
        "CLEAN_TEXT",
        "FEASIBLE_RUHI",
        "NOTE",
    ]

    @classmethod
    def export_tsv(cls, items: List[CorpusItem], output_path: str) -> str:
        """將語料清單匯出為標準 TSV 檔案"""
        p = Path(output_path)
        p.parent.mkdir(parents=True, exist_ok=True)

        with open(p, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f, delimiter="\t", quoting=csv.QUOTE_MINIMAL)
            writer.writerow(cls.TSV_HEADER)

            for it in items:
                # 確保文字中的跳位字元與換行已被轉義，保護 TSV 結構
                safe_text = it.clean_text.replace("\t", " ").replace("\r", "").replace("\n", " ")
                writer.writerow([
                    it.corpus_id,
                    it.category,
                    it.difficulty.value,
                    it.char_len,
                    f"{it.oov_rate:.4f}",
                    safe_text,
                    "YES" if it.feasible_ruhi else "NO",
                    it.note.replace("\t", " "),
                ])

        return str(p)

    @classmethod
    def split_and_export(
        cls,
        items: List[CorpusItem],
        output_dir: str,
        prefix: str = "ruhmark",
        train_ratio: float = 0.8,
        val_ratio: float = 0.1,
        test_ratio: float = 0.1,
        shuffle: bool = True,
        seed: int = 42
    ) -> Dict[str, str]:
        """
        將語料集切分為 calibration / validation / benchmark 三大集合並分別匯出 TSV
        """
        if shuffle:
            items_copy = list(items)
            random.seed(seed)
            random.shuffle(items_copy)
        else:
            items_copy = items

        total = len(items_copy)
        train_end = int(total * train_ratio)
        val_end = train_end + int(total * val_ratio)

        train_items = items_copy[:train_end]
        val_items = items_copy[train_end:val_end]
        test_items = items_copy[val_end:]

        out_dir = Path(output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)

        res = {}
        res["calibration"] = cls.export_tsv(train_items, str(out_dir / f"{prefix}_calibration.tsv"))
        res["validation"] = cls.export_tsv(val_items, str(out_dir / f"{prefix}_validation.tsv"))
        res["benchmark"] = cls.export_tsv(test_items, str(out_dir / f"{prefix}_benchmark_gold.tsv"))

        return res
