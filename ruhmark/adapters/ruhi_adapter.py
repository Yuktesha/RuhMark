"""
RuhMark (如標) AI Benchmark & Corpus Preprocessor Platform
ruhmark.adapters.ruhi_adapter - Ruhi (如喜) 許氏鍵盤與注音輸入法評測適配器
"""

import sys
import os
from pathlib import Path
from typing import Dict, Any, List, Optional, Set
import re

# 自動確保 RuhOS 根目錄在 sys.path 中以支援 ruhi 模組引用
RUHOS_ROOT = Path(__file__).resolve().parent.parent.parent
if str(RUHOS_ROOT) not in sys.path:
    sys.path.insert(0, str(RUHOS_ROOT))

from .base_adapter import BaseCorpusAdapter
from ..models import DifficultyLevel, TokenMeta


class RuhiAdapter(BaseCorpusAdapter):
    """Ruhi (如喜) 輸入法評測適配器：檢驗注音覆蓋率、許氏擊鍵轉化與 OOV 率"""

    def __init__(self, lexicon_path: Optional[str] = None):
        self.lexicon = None
        self.converter = None
        self.known_words: Set[str] = set()
        self.known_chars: Set[str] = set()

        # 預設指向 ruhi/ruhi_lexicon/data/lexicon_core.tsv
        if not lexicon_path:
            default_path = RUHOS_ROOT / "ruhi" / "ruhi_lexicon" / "data" / "lexicon_core.tsv"
            if default_path.exists():
                lexicon_path = str(default_path)

        self.lexicon_path = lexicon_path
        self._init_ruhi_engine()

    def _init_ruhi_engine(self):
        """延遲載入 Ruhi 詞庫與擊鍵轉換引擎"""
        try:
            from ruhi.ruhi_lexicon.lexicon_manager import LexiconManager
            from ruhi.ruhi_evaluator.text_to_keystrokes import TextToHsuKeystrokes

            self.lexicon = LexiconManager()
            if self.lexicon_path and os.path.exists(self.lexicon_path):
                self.lexicon.load_tsv(self.lexicon_path)

            self.converter = TextToHsuKeystrokes(self.lexicon)

            # 建立快取索引
            for entry in self.lexicon.entries:
                self.known_words.add(entry.word)
                for c in entry.word:
                    self.known_chars.add(c)
        except Exception as e:
            # 若無 ruhi 模組則優雅降級為空詞庫
            pass

    def profile_sentence(self, text: str) -> Dict[str, Any]:
        """
        評估句子對 Ruhi 的適配度：
        1. 計算中文字元數、標點數、英數數
        2. 計算未在詞庫中之字元數 (OOV)
        3. 測試許氏擊鍵流轉換長度與轉換率
        """
        total_chars = len(text)
        if total_chars == 0:
            return {
                "oov_rate": 0.0,
                "feasible": False,
                "hsu_key_count": 0,
                "chinese_char_count": 0,
            }

        chinese_chars = [c for c in text if "\u4e00" <= c <= "\u9fff"]
        zh_count = len(chinese_chars)

        oov_chars = [c for c in chinese_chars if c not in self.known_chars]
        oov_count = len(oov_chars)
        oov_rate = (oov_count / max(1, zh_count)) if zh_count > 0 else 0.0

        # 測試轉換為許氏擊鍵流
        hsu_keys = []
        is_feasible = True
        if self.converter:
            try:
                hsu_keys = self.converter.text_to_hsu_stream(text)
            except Exception:
                is_feasible = False
        else:
            # 降級估計擊鍵數 (中文平均每字 2.2 鍵，標點 1 鍵)
            hsu_keys = ["x"] * int(zh_count * 2.2 + (total_chars - zh_count))

        # 檢查是否有無法轉化之生僻非 ASCII 字符殘留
        key_count = len(hsu_keys)
        expansion_ratio = round(key_count / max(1, total_chars), 2)

        return {
            "total_chars": total_chars,
            "chinese_chars": zh_count,
            "oov_chars": oov_chars,
            "oov_count": oov_count,
            "oov_rate": round(oov_rate, 4),
            "hsu_key_count": key_count,
            "expansion_ratio": expansion_ratio,
            "feasible": is_feasible and (zh_count > 0 or total_chars > 0),
        }

    def is_feasible(self, text: str, profile_info: Dict[str, Any]) -> bool:
        """若完全無法轉化為擊鍵或全為未知符號，則標記為不可評測"""
        return profile_info.get("feasible", False)

    def determine_difficulty(self, text: str, profile_info: Dict[str, Any]) -> DifficultyLevel:
        """
        根據 OOV 率、長度與詞性複雜度分級：
        L1: 零 OOV (100% 收錄)，長度 40 字以內
        L2: OOV <= 0.15，長度 80 字以內
        L3: OOV > 0.15 或長度 > 80 字
        """
        oov_rate = profile_info.get("oov_rate", 0.0)
        total_len = profile_info.get("total_chars", len(text))

        if oov_rate == 0.0 and total_len <= 45:
            return DifficultyLevel.L1
        elif oov_rate <= 0.15 and total_len <= 85:
            return DifficultyLevel.L2
        else:
            return DifficultyLevel.L3
