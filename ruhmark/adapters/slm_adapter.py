"""
RuhMark (如標) AI Benchmark & Corpus Preprocessor Platform
ruhmark.adapters.slm_adapter - 本地小語言模型 (SLM) 與端側 Tokenizer 適配器 (預留架構)
"""

import math
from typing import Dict, Any, List, Optional
from collections import Counter

from .base_adapter import BaseCorpusAdapter
from ..models import DifficultyLevel, TokenMeta


class SLMAdapter(BaseCorpusAdapter):
    """端側小語言模型 (SLM) 語料適配器：評估字元熵 (Entropy)、詞元密度與語法多樣性"""

    def __init__(self, vocab_size: int = 32000):
        self.vocab_size = vocab_size

    def calculate_char_entropy(self, text: str) -> float:
        """計算字元 Shannon 熵 (Shannon Entropy)，評估語料多樣性與重複度"""
        if not text:
            return 0.0
        counts = Counter(text)
        n = len(text)
        entropy = 0.0
        for cnt in counts.values():
            p = cnt / n
            entropy -= p * math.log2(p)
        return round(entropy, 3)

    def profile_sentence(self, text: str) -> Dict[str, Any]:
        """計算端側模型關注之特徵"""
        entropy = self.calculate_char_entropy(text)
        total_len = len(text)
        
        # 粗略估計 BPE/WordPiece Token 數量 (中文約 1.2-1.5 字/Token)
        estimated_tokens = int(total_len * 0.85)

        return {
            "char_entropy": entropy,
            "estimated_tokens": max(1, estimated_tokens),
            "repetition_ratio": round(1.0 - (len(set(text)) / max(1, total_len)), 3),
            "feasible": total_len > 0 and entropy > 1.5,
        }

    def is_feasible(self, text: str, profile_info: Dict[str, Any]) -> bool:
        """若重複率過高 (熵過低) 則判定為無訓練價值之垃圾文本"""
        return profile_info.get("feasible", True)

    def determine_difficulty(self, text: str, profile_info: Dict[str, Any]) -> DifficultyLevel:
        entropy = profile_info.get("char_entropy", 0.0)
        total_len = len(text)

        if entropy < 3.5 and total_len < 40:
            return DifficultyLevel.L1
        elif entropy < 4.8 and total_len < 80:
            return DifficultyLevel.L2
        else:
            return DifficultyLevel.L3
