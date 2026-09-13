"""
RuhMark (如標) AI Benchmark & Corpus Preprocessor Platform
ruhmark.models - 核心資料模型與設定結構
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any
import time


class DifficultyLevel(str, Enum):
    """語料難度分級"""
    L1 = "L1"  # 初級 / 日常生活高頻詞，100% 詞庫收錄
    L2 = "L2"  # 中級 / 一般新聞、文學、多字詞組
    L3 = "L3"  # 高級 / 專業領域、生僻字詞、長句難句


@dataclass
class TokenMeta:
    """詞元 / 字符級特徵詮釋資料"""
    text: str
    is_chinese: bool
    bopomofo: Optional[str] = None
    is_oov: bool = False
    extra: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CorpusItem:
    """單一語料項目 (句子或語義塊)"""
    corpus_id: str
    raw_text: str
    clean_text: str = ""
    category: str = "general"
    difficulty: DifficultyLevel = DifficultyLevel.L1
    char_len: int = 0
    token_count: int = 0
    oov_rate: float = 0.0
    feasible_ruhi: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)
    tokens: List[TokenMeta] = field(default_factory=list)
    note: str = ""

    def __post_init__(self):
        if not self.clean_text:
            self.clean_text = self.raw_text
        if not self.char_len:
            self.char_len = len(self.clean_text)


@dataclass
class CleanOptions:
    """語料清洗與規整參數選項"""
    # 字元規整
    do_nfkc: bool = True
    remove_invisible_chars: bool = True
    normalize_punctuation: bool = True
    normalize_quotes: bool = True
    keep_ascii_halfwidth: bool = True

    # 雜訊過濾
    remove_html_tags: bool = True
    remove_urls: bool = True
    remove_emails: bool = True
    remove_social_tags: bool = True
    compress_repeated_punctuation: bool = True
    max_repeated_chars: int = 3
    filter_news_boilerplates: bool = True

    # 智慧斷句
    min_sentence_len: int = 6
    max_sentence_len: int = 120
    protect_dialog_quotes: bool = True
    deduplicate: bool = True
    require_chinese: bool = False  # 是否強制要求句子必須包含中文字元

    # 詞庫與評測檢驗
    enable_lexicon_profiling: bool = True
    lexicon_path: Optional[str] = None
    vetted_color_only: bool = False  # 是否僅抽取 Docx 中綠色標註之人工校對正文


@dataclass
class CleaningStats:
    """清洗流水線執行統計統計報表"""
    raw_documents_count: int = 0
    raw_characters_count: int = 0
    clean_sentences_count: int = 0
    clean_characters_count: int = 0
    dropped_short_count: int = 0
    dropped_long_count: int = 0
    dropped_non_chinese_count: int = 0
    dropped_boilerplate_count: int = 0
    duplicates_removed_count: int = 0
    html_tags_cleaned_count: int = 0
    urls_cleaned_count: int = 0
    punctuation_compressed_count: int = 0
    invisible_chars_stripped_count: int = 0
    elapsed_seconds: float = 0.0

    def summary_dict(self) -> Dict[str, Any]:
        return {
            "raw_documents": self.raw_documents_count,
            "raw_characters": self.raw_characters_count,
            "clean_sentences": self.clean_sentences_count,
            "clean_characters": self.clean_characters_count,
            "dropped_short": self.dropped_short_count,
            "dropped_long": self.dropped_long_count,
            "dropped_non_chinese": self.dropped_non_chinese_count,
            "dropped_boilerplate": self.dropped_boilerplate_count,
            "duplicates_removed": self.duplicates_removed_count,
            "html_tags_cleaned": self.html_tags_cleaned_count,
            "urls_cleaned": self.urls_cleaned_count,
            "punctuation_compressed": self.punctuation_compressed_count,
            "invisible_chars_stripped": self.invisible_chars_stripped_count,
            "elapsed_seconds": round(self.elapsed_seconds, 3),
        }
