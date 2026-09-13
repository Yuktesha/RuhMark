"""
RuhMark (如標) AI Benchmark & Corpus Preprocessor Platform
ruhmark.adapters.base_adapter - 基礎語料消費與評測適配器介面
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from ..models import DifficultyLevel, TokenMeta


class BaseCorpusAdapter(ABC):
    """下游 AI 與評測適配器基底類別"""

    @abstractmethod
    def profile_sentence(self, text: str) -> Dict[str, Any]:
        """對單一語料句子進行特徵分析，回傳指標字典"""
        pass

    @abstractmethod
    def is_feasible(self, text: str, profile_info: Dict[str, Any]) -> bool:
        """判定該句子是否具備可評測性"""
        pass

    @abstractmethod
    def determine_difficulty(self, text: str, profile_info: Dict[str, Any]) -> DifficultyLevel:
        """評定語料難度等級 (L1, L2, L3)"""
        pass
