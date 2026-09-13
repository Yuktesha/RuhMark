"""
RuhMark (如標) AI Benchmark & Corpus Preprocessor Platform
ruhmark.segmenter - 智慧語意分句、引號邊界保護與長度約束器
"""

import re
from typing import List, Tuple, Set, Dict, Any, Optional


class SentenceSegmenter:
    """具備對話引號跨句保護之中文斷句分詞器"""

    # 中文語意終止標點
    TERMINATORS = set(["。", "！", "？", "；", "\n"])

    # 對話引號成對標記
    QUOTE_PAIRS = {
        "「": "」",
        "『": "』",
        "“": "”",
        "《": "》",
        "【": "】",
        "（": "）",
    }
    REVERSE_QUOTE_PAIRS = {v: k for k, v in QUOTE_PAIRS.items()}

    @classmethod
    def segment_text(
        cls,
        text: str,
        protect_quotes: bool = True
    ) -> List[str]:
        """
        將長段落依語意終止符切分為獨立句子，
        若 protect_quotes 為 True，則引號內部的終止符不會被裁斷。
        """
        if not text:
            return []

        sentences = []
        current_buf = []
        quote_stack = []

        n = len(text)
        i = 0
        while i < n:
            char = text[i]
            current_buf.append(char)

            if protect_quotes:
                # 處理引號入棧與出棧
                if char in cls.QUOTE_PAIRS:
                    quote_stack.append(char)
                elif char in cls.REVERSE_QUOTE_PAIRS:
                    if quote_stack and quote_stack[-1] == cls.REVERSE_QUOTE_PAIRS[char]:
                        quote_stack.pop()

            # 檢查是否為斷句終止符，且當前不在引號閉合區間內
            in_quote = len(quote_stack) > 0 if protect_quotes else False
            if char in cls.TERMINATORS and not in_quote:
                # 貪婪吸收緊隨其後的右引號、後引號或連續標點 (例如 。」 或 ！」)
                while i + 1 < n and (text[i + 1] in cls.REVERSE_QUOTE_PAIRS or text[i + 1] in cls.TERMINATORS):
                    i += 1
                    next_c = text[i]
                    current_buf.append(next_c)
                    if protect_quotes and quote_stack and next_c in cls.REVERSE_QUOTE_PAIRS:
                        if quote_stack[-1] == cls.REVERSE_QUOTE_PAIRS[next_c]:
                            quote_stack.pop()

                sentence_str = "".join(current_buf).strip()
                if sentence_str:
                    sentences.append(sentence_str)
                current_buf = []

            i += 1

        # 殘留字元
        if current_buf:
            remainder = "".join(current_buf).strip()
            if remainder:
                sentences.append(remainder)

        return sentences

    @classmethod
    def filter_and_deduplicate(
        cls,
        sentences: List[str],
        min_len: int = 6,
        max_len: int = 120,
        deduplicate: bool = True,
        require_chinese: bool = False,
        existing_seen: Optional[Set[str]] = None
    ) -> Tuple[List[str], Dict[str, int]]:
        """
        對句子清單進行長度門檻約束與全域去重
        回傳: (合格句子清單, 統計過濾數量字典)
        """
        seen: Set[str] = existing_seen if existing_seen is not None else set()
        accepted = []
        stats = {
            "dropped_short": 0,
            "dropped_long": 0,
            "dropped_non_chinese": 0,
            "dropped_duplicate": 0,
        }

        for s in sentences:
            clean_s = s.strip()
            # 計算實質文字長度 (去除純空白)
            c_len = len(clean_s)

            if c_len < min_len:
                stats["dropped_short"] += 1
                continue
            if max_len > 0 and c_len > max_len:
                stats["dropped_long"] += 1
                continue

            # 若強制要求中文字元
            if require_chinese and not any("\u4e00" <= c <= "\u9fff" for c in clean_s):
                stats["dropped_non_chinese"] += 1
                continue

            # 去重比對
            if deduplicate:
                if clean_s in seen:
                    stats["dropped_duplicate"] += 1
                    continue
                seen.add(clean_s)

            accepted.append(clean_s)

        return accepted, stats
