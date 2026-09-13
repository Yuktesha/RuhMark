"""
RuhMark (如標) AI Benchmark & Corpus Preprocessor Platform
ruhmark.diacritics - 梵語羅馬拼音尖音符與打字機符號自動正字轉換器 (基於 曹大十 巴巴轉換.bas)
"""

import re
from typing import Dict, List, Tuple


class DiacriticsConverter:
    """將打字機重音符號 (例如 a', s', m') 自動常規化為國際標準 Unicode 梵文轉寫字母"""

    # 完整對照表 (繼承自 曹大十 巴巴轉換.bas 並擴充)
    ACCENT_MAP: List[Tuple[str, str]] = [
        ("a'", "á"), ("A'", "Á"),
        ("e'", "é"), ("E'", "É"),
        ("i'", "í"), ("I'", "Í"),
        ("o'", "ó"), ("O'", "Ó"),
        ("u'", "ú"), ("U'", "Ú"),
        ("d'", "d́"), ("D'", "D́"),
        ("m'", "ḿ"), ("M'", "Ḿ"),
        ("n'", "ń"), ("N'", "Ń"),
        ("s'", "ś"), ("S'", "Ś"),
        ("t'", "t́"), ("T'", "T́"),
        ("r'", "ŕ"), ("R'", "Ŕ"),
        ("l'", "ĺ"), ("L'", "Ĺ"),
        ("c'", "ć"), ("C'", "Ć"),
    ]

    @classmethod
    def convert_text(cls, text: str) -> str:
        """一鍵替換文字中所有打字機單引號重音為 Unicode 尖音符號"""
        for src, target in cls.ACCENT_MAP:
            text = text.replace(src, target)
        return text

    @classmethod
    def normalize_discourse_layout(cls, raw_text: str) -> str:
        """
        對齊整理原始複製文本：
        1. 移除行尾 " $"
        2. 壓縮多餘空白 (2+ 空格轉單一空格或段落)
        3. 重音符號常規化
        """
        # 1. 移除行尾 " $"
        text = re.sub(r" +\$", "", raw_text)
        # 2. 移除行尾空白
        text = re.sub(r"[ \t]+$", "", text, flags=re.MULTILINE)
        # 3. 執行重音替換
        text = cls.convert_text(text)
        return text.strip()
