"""
RuhMark (如標) AI Benchmark & Corpus Preprocessor Platform
ruhmark.pipeline - 全流程語料清洗前處理流水線引擎
"""

import time
from typing import List, Optional, Tuple, Dict, Any, Set
from pathlib import Path

from .models import CorpusItem, CleanOptions, CleaningStats, DifficultyLevel
from .reader import CorpusReader
from .normalizer import TextNormalizer
from .cleaner import NoiseCleaner
from .segmenter import SentenceSegmenter
from .profiler import CorpusProfiler
from .exporter import DatasetExporter


class RuhMarkPipeline:
    """RuhMark 全自動語料清洗前處理流水線中樞"""

    def __init__(self, options: Optional[CleanOptions] = None, profiler: Optional[CorpusProfiler] = None):
        self.options = options or CleanOptions()
        self.profiler = profiler or CorpusProfiler()

    def clean_single_text(self, raw_text: str) -> List[str]:
        """
        對單一原始文字字串執行完整清洗與斷句，回傳乾淨句子清單
        """
        # 1. 雜訊清洗 (HTML, URL, Markdown, 社群標籤)
        cleaned, _ = NoiseCleaner.clean_all(
            raw_text,
            remove_html=self.options.remove_html_tags,
            remove_urls=self.options.remove_urls,
            remove_social=self.options.remove_social_tags,
            compress_punct=self.options.compress_repeated_punctuation,
            max_repeat=self.options.max_repeated_chars,
        )

        # 2. Unicode 與標點常規化
        normalized, _ = TextNormalizer.normalize_all(cleaned)

        # 3. 逐行樣板檢查 (移除新聞樣板/版權宣告)
        valid_lines = []
        for line in normalized.splitlines():
            line_str = line.strip()
            if not line_str:
                continue
            if self.options.filter_news_boilerplates and NoiseCleaner.is_boilerplate(line_str):
                continue
            valid_lines.append(line_str)

        combined_text = "\n".join(valid_lines)

        # 4. 智慧語意切句 (保護對話引號)
        raw_sentences = SentenceSegmenter.segment_text(
            combined_text,
            protect_quotes=self.options.protect_dialog_quotes
        )

        # 5. 長度約束與去重
        accepted_sentences, _ = SentenceSegmenter.filter_and_deduplicate(
            raw_sentences,
            min_len=self.options.min_sentence_len,
            max_len=self.options.max_sentence_len,
            deduplicate=self.options.deduplicate,
            require_chinese=self.options.require_chinese
        )

        return accepted_sentences

    def process_source(
        self,
        source_path: str,
        output_tsv: Optional[str] = None,
        category: str = "general"
    ) -> Tuple[List[CorpusItem], CleaningStats]:
        """
        批次處理來源檔案或資料夾，回傳 (語料項目清單, 清洗統計數據)
        若指定 output_tsv，則自動匯出為 TSV。
        """
        start_time = time.time()
        stats = CleaningStats()
        items: List[CorpusItem] = []
        global_seen: Set[str] = set()

        # 1. 讀取多來源
        for doc_id, raw_content, meta in CorpusReader.iterate_source(
            source_path,
            vetted_color_only=self.options.vetted_color_only
        ):
            stats.raw_documents_count += 1
            stats.raw_characters_count += len(raw_content)

            # 2. 雜訊清洗
            cleaned_text, clean_meta = NoiseCleaner.clean_all(
                raw_content,
                remove_html=self.options.remove_html_tags,
                remove_urls=self.options.remove_urls,
                remove_social=self.options.remove_social_tags,
                compress_punct=self.options.compress_repeated_punctuation,
                max_repeat=self.options.max_repeated_chars,
            )
            stats.html_tags_cleaned_count += clean_meta["html_tags"]
            stats.urls_cleaned_count += clean_meta["urls_and_emails"]
            stats.punctuation_compressed_count += clean_meta["punct_compressed"]

            # 3. 字元與標點常規化
            normalized_text, inv_cnt = TextNormalizer.normalize_all(cleaned_text)
            stats.invisible_chars_stripped_count += inv_cnt

            # 4. 逐行樣板檢查 (移除新聞媒體與版權聲明)
            valid_lines = []
            for line in normalized_text.splitlines():
                line_str = line.strip()
                if not line_str:
                    continue
                if self.options.filter_news_boilerplates and NoiseCleaner.is_boilerplate(line_str):
                    stats.dropped_boilerplate_count += 1
                    continue
                valid_lines.append(line_str)

            doc_text = "\n".join(valid_lines)

            # 5. 語意切句
            sentences = SentenceSegmenter.segment_text(
                doc_text,
                protect_quotes=self.options.protect_dialog_quotes
            )

            # 6. 長度過濾與去重
            filtered_sentences, filter_stats = SentenceSegmenter.filter_and_deduplicate(
                sentences,
                min_len=self.options.min_sentence_len,
                max_len=self.options.max_sentence_len,
                deduplicate=self.options.deduplicate,
                require_chinese=self.options.require_chinese,
                existing_seen=global_seen
            )
            stats.dropped_short_count += filter_stats["dropped_short"]
            stats.dropped_long_count += filter_stats["dropped_long"]
            stats.dropped_non_chinese_count += filter_stats.get("dropped_non_chinese", 0)
            stats.duplicates_removed_count += filter_stats["dropped_duplicate"]

            # 7. 封裝為 CorpusItem
            for s_idx, sent in enumerate(filtered_sentences):
                corpus_id = f"{doc_id}_{s_idx+1:04d}"
                c_item = CorpusItem(
                    corpus_id=corpus_id,
                    raw_text=sent,
                    clean_text=sent,
                    category=category,
                    metadata={"source_doc": doc_id, "meta": meta}
                )
                items.append(c_item)

        # 8. 詞庫覆蓋與特徵輪廓剖析
        if self.options.enable_lexicon_profiling:
            items, profile_summary = self.profiler.profile_batch(items)

        # 統計更新
        stats.clean_sentences_count = len(items)
        stats.clean_characters_count = sum(it.char_len for it in items)
        stats.elapsed_seconds = time.time() - start_time

        # 9. 匯出 TSV
        if output_tsv:
            DatasetExporter.export_tsv(items, output_tsv)

        return items, stats
