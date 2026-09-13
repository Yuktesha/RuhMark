"""
RuhMark (如標) AI Benchmark & Corpus Preprocessor Platform
ruhmark.profiler - 語料特徵輪廓、品質評分與難度分級標註器
"""

from typing import List, Dict, Any, Optional, Tuple
from .models import CorpusItem, DifficultyLevel
from .adapters.base_adapter import BaseCorpusAdapter
from .adapters.ruhi_adapter import RuhiAdapter


class CorpusProfiler:
    """語料特徵輪廓與品質剖析器"""

    def __init__(self, adapter: Optional[BaseCorpusAdapter] = None):
        # 預設使用 Ruhi 適配器以評測輸入法與自然語意
        self.adapter = adapter or RuhiAdapter()

    def profile_item(self, item: CorpusItem) -> CorpusItem:
        """對單一語料項目執行深度剖析並更新屬性"""
        text = item.clean_text
        profile_info = self.adapter.profile_sentence(text)

        item.char_len = len(text)
        item.oov_rate = profile_info.get("oov_rate", 0.0)
        item.feasible_ruhi = self.adapter.is_feasible(text, profile_info)
        item.difficulty = self.adapter.determine_difficulty(text, profile_info)
        item.metadata.update(profile_info)

        # 填寫備註
        if item.oov_rate > 0:
            oov_sample = "".join(profile_info.get("oov_chars", [])[:5])
            item.note = f"含未登錄字({oov_sample})"
        else:
            item.note = "詞庫全覆蓋"

        return item

    def profile_batch(self, items: List[CorpusItem]) -> Tuple[List[CorpusItem], Dict[str, Any]]:
        """批次剖析語料項目並產出總結報告"""
        profiled_items = []
        difficulty_counts = {DifficultyLevel.L1: 0, DifficultyLevel.L2: 0, DifficultyLevel.L3: 0}
        total_oov_sum = 0.0
        feasible_count = 0

        for it in items:
            p_item = self.profile_item(it)
            profiled_items.append(p_item)

            difficulty_counts[p_item.difficulty] += 1
            total_oov_sum += p_item.oov_rate
            if p_item.feasible_ruhi:
                feasible_count += 1

        total = len(items)
        summary = {
            "total_sentences": total,
            "avg_oov_rate": round(total_oov_sum / max(1, total), 4),
            "feasible_count": feasible_count,
            "feasibility_percent": round((feasible_count / max(1, total)) * 100.0, 2),
            "difficulty_distribution": {
                "L1_easy": difficulty_counts[DifficultyLevel.L1],
                "L2_medium": difficulty_counts[DifficultyLevel.L2],
                "L3_hard": difficulty_counts[DifficultyLevel.L3],
            }
        }
        return profiled_items, summary
