"""
RuhMark (如標) AI Benchmark & Corpus Preprocessor Platform
ruhmark.normalizer - Unicode NFKC、隱形字元與標點全半形常規化器
"""

import re
import unicodedata
from typing import Tuple


class TextNormalizer:
    """文字與字元規範化中樞"""

    # 不可見字元清單：零寬空白、零寬非連字、零寬連字、方向標記、BOM、軟連字號等
    INVISIBLE_CHARS_REGEX = re.compile(
        r"[\u200b\u200c\u200d\u200e\u200f\ufeff\u00ad\u2060\u202a-\u202e\x00-\x08\x0b\x0c\x0e-\x1f\x7f]"
    )

    # 全形英數對照表 (！到～)
    FULLWIDTH_ASCII_START = 0xFF01
    FULLWIDTH_ASCII_END = 0xFF5E

    # 中文標點標準映射 (在中文上下文中的半形轉全形)
    CHINESE_PUNCT_MAP = {
        ",": "，",
        ";": "；",
        "!": "！",
        "?": "？",
        ":": "：",
        "~": "～",
        "(": "（",
        ")": "）",
        "[": "【",
        "]": "】",
    }

    @classmethod
    def strip_invisible_characters(cls, text: str) -> Tuple[str, int]:
        """清除所有不可見控制字元與 BOM，並回傳清除數量"""
        new_text, count = cls.INVISIBLE_CHARS_REGEX.subn("", text)
        return new_text, count

    @classmethod
    def normalize_unicode(cls, text: str) -> str:
        """Unicode NFKC 規整"""
        return unicodedata.normalize("NFKC", text)

    @classmethod
    def fullwidth_alphanumeric_to_halfwidth(cls, text: str) -> str:
        """將全形英數字（Ａ-Ｚ、ａ-ｚ、０-９）轉為標準半形 ASCII"""
        result = []
        for char in text:
            code = ord(char)
            # 全形空格
            if code == 0x3000:
                result.append(" ")
            # 全形 ASCII 範圍 0xFF01 - 0xFF5E
            elif 0xFF01 <= code <= 0xFF5E:
                # 若為全形英數字則轉換
                half = chr(code - 0xFEE0)
                if half.isalnum():
                    result.append(half)
                else:
                    result.append(char)
            else:
                result.append(char)
        return "".join(result)

    @classmethod
    def normalize_dialog_quotes(cls, text: str) -> str:
        """
        將對話引號轉換為正體中文直角引號「」與『』：
        “...” ➔ 「...」
        ‘...’ ➔ 『...』
        """
        # 先處理外層雙引號
        # 匹配成對的雙引號 “ ... ” 或 " ... " (緊鄰中文或中文語境)
        def replace_outer_quotes(m):
            content = m.group(1)
            # 檢查內部是否有第二層單引號
            content = re.sub(r"[‘']([^'’]+)[’']", r"『\1』", content)
            return f"「{content}」"

        # 匹配 “xxx”
        text = re.sub(r"[“\"]([^\"“”\n\r]+)[”\"]", replace_outer_quotes, text)
        # 匹配未配對或殘留的單引號
        text = re.sub(r"[‘']([^'’\n\r]{2,})[’']", r"『\1』", text)
        return text

    @classmethod
    def normalize_punctuation_contextual(cls, text: str) -> str:
        """
        語意情境標點轉換：
        當逗號、句號、驚嘆號等出現在中文字元相鄰處時，強制轉換為全形；
        英文與數字之間的句點 (如 3.14, google.com) 嚴格保持半形。
        """
        # 1. 省略號與破折號規整
        text = re.sub(r"\.{3,}|…{2,}", "……", text)
        text = re.sub(r"-{2,}|—{2,}", "——", text)

        # 2. 中文相鄰的逗號、問號、驚嘆號、分號、冒號
        # 中文字範圍: [\u4e00-\u9fff\u3400-\u4dbf]
        zh_char = r"[\u4e00-\u9fff\u3400-\u4dbf]"
        
        # 句號：中文後的半形句點 . 轉全形 。 (排除數字後的點)
        text = re.sub(f"({zh_char})\\s*\\.\\s*", r"\1。", text)
        text = re.sub(f"\\s*\\.\\s*({zh_char})", r"。\1", text)

        # 逗號：中文前後的逗號 , 轉全形 ，
        text = re.sub(f"({zh_char})\\s*,\\s*", r"\1，", text)
        text = re.sub(f"\\s*,\\s*({zh_char})", r"，\1", text)

        # 問號與驚嘆號
        text = re.sub(f"({zh_char})\\s*\\?\\s*", r"\1？", text)
        text = re.sub(f"({zh_char})\\s*!\\s*", r"\1！", text)

        # 分號與冒號
        text = re.sub(f"({zh_char})\\s*;\\s*", r"\1；", text)
        text = re.sub(f"({zh_char})\\s*:\\s*(?![0-9/])", r"\1：", text)

        # 括號
        text = re.sub(f"\\((\\s*{zh_char}[^)]*)\\)", r"（\1）", text)

        # 清除中文與中文之間的多餘半形空白 (例如 "這 是 測試" -> "這是測試")
        text = re.sub(f"({zh_char})\\s+({zh_char})", r"\1\2", text)

        return text

    @classmethod
    def normalize_all(cls, text: str) -> Tuple[str, int]:
        """一鍵執行完整常規化流程，回傳 (清洗後字串, 移除非可見字元數)"""
        text, inv_count = cls.strip_invisible_characters(text)
        text = cls.normalize_unicode(text)
        text = cls.fullwidth_alphanumeric_to_halfwidth(text)
        text = cls.normalize_dialog_quotes(text)
        text = cls.normalize_punctuation_contextual(text)
        return text.strip(), inv_count
