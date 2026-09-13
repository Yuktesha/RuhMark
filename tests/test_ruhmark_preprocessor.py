"""
RuhMark (如標) AI Benchmark & Corpus Preprocessor Platform
tests.test_ruhmark_preprocessor - 核心清洗前處理器單元與端到端整合測試
"""

import sys
import unittest
from pathlib import Path

# 確保上一層路徑可供 Python 識別模組
CURRENT_DIR = Path(__file__).resolve().parent
RUHOS_ROOT = CURRENT_DIR.parent.parent
if str(RUHOS_ROOT) not in sys.path:
    sys.path.insert(0, str(RUHOS_ROOT))

from ruhmark.models import CleanOptions, DifficultyLevel
from ruhmark.normalizer import TextNormalizer
from ruhmark.cleaner import NoiseCleaner
from ruhmark.segmenter import SentenceSegmenter
from ruhmark.adapters.ruhi_adapter import RuhiAdapter
from ruhmark.pipeline import RuhMarkPipeline
from ruhmark.exporter import DatasetExporter


class TestRuhMarkPreprocessor(unittest.TestCase):
    """RuhMark 前處理器各模組單元測試"""

    def test_01_normalizer_invisible_and_nfkc(self):
        """測試不可見字元剔除與 NFKC 規格化"""
        raw = "中華\u200b民國\ufeff在臺灣"
        cleaned, count = TextNormalizer.strip_invisible_characters(raw)
        self.assertEqual(cleaned, "中華民國在臺灣")
        self.assertEqual(count, 2)

    def test_02_normalizer_fullwidth_alphanumeric(self):
        """測試全形英數轉換為標準半形 ASCII"""
        raw = "ＡＩ智慧２０２６年啟動！"
        res = TextNormalizer.fullwidth_alphanumeric_to_halfwidth(raw)
        self.assertEqual(res, "AI智慧2026年啟動！")

    def test_03_normalizer_dialog_quotes(self):
        """測試引號正體直角引號轉換「」與『』"""
        raw = '他說：“子曰：‘溫故而知新’，此言得之。”'
        res = TextNormalizer.normalize_dialog_quotes(raw)
        self.assertEqual(res, "他說：「子曰：『溫故而知新』，此言得之。」")

    def test_04_normalizer_contextual_punct(self):
        """測試中文情境下半形標點轉全形"""
        raw = "我們今天開始,使用許氏鍵盤自然輸入法!非常流暢."
        res = TextNormalizer.normalize_punctuation_contextual(raw)
        self.assertEqual(res, "我們今天開始，使用許氏鍵盤自然輸入法！非常流暢。")

    def test_05_cleaner_html_and_urls(self):
        """測試 HTML 標籤與 URL/Email 清除"""
        raw = '<div class="main">點擊連結 <a href="https://example.com">官網</a> 或來信 service@domain.com 洽詢！</div>'
        clean_text, stats = NoiseCleaner.clean_all(raw)
        self.assertNotIn("<div>", clean_text)
        self.assertNotIn("<a", clean_text)
        self.assertNotIn("https://example.com", clean_text)
        self.assertNotIn("service@domain.com", clean_text)
        self.assertIn("點擊連結", clean_text)
        self.assertIn("官網", clean_text)

    def test_06_cleaner_repeated_punct_and_chars(self):
        """測試重複標點與字元壓縮"""
        raw = "真的太棒了！！！！！！哈哈哈哈哈哈哈哈"
        res, stats = NoiseCleaner.clean_all(raw, max_repeat=3)
        self.assertEqual(res, "真的太棒了！哈哈哈")

    def test_07_cleaner_boilerplates(self):
        """測試新聞與廣告樣板識別"""
        b1 = "記者陳小明／台北即時報導"
        b2 = "版權所有 翻印必究。未經授權禁止轉載"
        b3 = "點我看更多精彩專題"
        normal_text = "今天天氣晴朗，適合外出踏青散步。"

        self.assertTrue(NoiseCleaner.is_boilerplate(b1))
        self.assertTrue(NoiseCleaner.is_boilerplate(b2))
        self.assertTrue(NoiseCleaner.is_boilerplate(b3))
        self.assertFalse(NoiseCleaner.is_boilerplate(normal_text))

    def test_08_segmenter_with_quote_protection(self):
        """測試智慧語意切句與引號內部終止符保護"""
        raw = "孔子曾經說道：「學而時習之，不亦說乎？有朋自遠方來，不亦樂乎！」這正是人機協同思考的最佳寫照。我們繼續向前。"
        sentences = SentenceSegmenter.segment_text(raw, protect_quotes=True)
        # 引號內部包含 ？ 與 ！，不應被截斷成破碎句子
        self.assertEqual(len(sentences), 2)
        self.assertIn("孔子曾經說道：「學而時習之，不亦說乎？有朋自遠方來，不亦樂乎！」這正是人機協同思考的最佳寫照。", sentences[0])
        self.assertEqual(sentences[1], "我們繼續向前。")

    def test_09_segmenter_length_filter_and_dedup(self):
        """測試句子長度門檻與去重"""
        sents = ["短", "太短了", "這是一句標準長度的繁體中文測試語句。", "這是一句標準長度的繁體中文測試語句。"]
        filtered, stats = SentenceSegmenter.filter_and_deduplicate(sents, min_len=6, deduplicate=True)
        self.assertEqual(len(filtered), 1)
        self.assertEqual(stats["dropped_short"], 2)
        self.assertEqual(stats["dropped_duplicate"], 1)

    def test_10_ruhi_adapter_and_profiling(self):
        """測試 Ruhi 輸入法適配器評測性與 OOV 檢驗"""
        adapter = RuhiAdapter()
        # 詞庫已收錄長詞
        s1 = "中華民國在臺灣。我們今天開始使用許氏鍵盤自然輸入法進行思考與打字。"
        p1 = adapter.profile_sentence(s1)
        self.assertTrue(p1["feasible"])
        self.assertGreater(p1["hsu_key_count"], 0)

        diff1 = adapter.determine_difficulty(s1, p1)
        if adapter.lexicon is not None:
            self.assertIn(diff1, [DifficultyLevel.L1, DifficultyLevel.L2])
        else:
            self.assertIn(diff1, [DifficultyLevel.L1, DifficultyLevel.L2, DifficultyLevel.L3])

    def test_11_end_to_end_pipeline(self):
        """端到端綜合測試：讀取 dirty_corpus_sample.txt 執行完整清洗流水線"""
        sample_file = CURRENT_DIR.parent / "sample_corpus" / "dirty_corpus_sample.txt"
        output_tsv = CURRENT_DIR.parent / "sample_corpus" / "test_output.tsv"

        pipeline = RuhMarkPipeline()
        items, stats = pipeline.process_source(
            source_path=str(sample_file),
            output_tsv=str(output_tsv),
            category="news_and_classics"
        )

        self.assertGreater(stats.clean_sentences_count, 0)
        self.assertGreater(stats.dropped_boilerplate_count, 0)
        self.assertGreater(stats.html_tags_cleaned_count, 0)
        self.assertTrue(output_tsv.exists())

        # 檢驗輸出的 TSV 內容
        with open(output_tsv, "r", encoding="utf-8") as f:
            lines = f.readlines()
            self.assertGreater(len(lines), 1)
            header = lines[0].strip().split("\t")
            self.assertEqual(header, DatasetExporter.TSV_HEADER)

        # 清理暫存檔案
        if output_tsv.exists():
            output_tsv.unlink()


if __name__ == "__main__":
    unittest.main()
