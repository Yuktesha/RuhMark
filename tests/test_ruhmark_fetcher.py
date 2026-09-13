"""
RuhMark (如標) AI Benchmark & Corpus Preprocessor Platform
tests.test_ruhmark_fetcher - 語料採集器 (RuhFetcher) 單元與端到端測試
"""

import sys
import unittest
import shutil
from pathlib import Path

# 確保上一層路徑可供 Python 識別模組
CURRENT_DIR = Path(__file__).resolve().parent
RUHOS_ROOT = CURRENT_DIR.parent.parent
if str(RUHOS_ROOT) not in sys.path:
    sys.path.insert(0, str(RUHOS_ROOT))

from ruhmark.fetcher.models import SourceType, SourceMetadata, FetchResult
from ruhmark.fetcher.web_scraper import ReadabilityExtractor, WebScraper
from ruhmark.fetcher.rss_collector import RSSCollector
from ruhmark.fetcher.source_manager import SourceManager


class TestRuhFetcher(unittest.TestCase):
    """RuhFetcher 各模組單元測試"""

    def setUp(self):
        self.test_dir = CURRENT_DIR / "tmp_fetcher_test"
        self.test_dir.mkdir(parents=True, exist_ok=True)

    def tearDown(self):
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

    def test_01_readability_extractor(self):
        """測試零依賴內建 ReadabilityExtractor 剝除雜訊標籤與抽取內文"""
        sample_html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>測試新聞標題：RuhOS 正式啟航</title>
            <style>.banner { color: red; }</style>
            <script>console.log("ads tracking");</script>
        </head>
        <body>
            <header><nav><a href="/">首頁</a> <a href="/news">新聞</a></nav></header>
            <div class="sidebar"><aside>這是側邊欄推薦文章</aside></div>
            <main>
                <h1>自適應空間接管第一原理</h1>
                <p>在愛爾蘭語中，rud 意為事物本質與船之龍骨，象徵自適應系統的穩固基石。</p>
                <blockquote>隨物賦形，天下皆適。</blockquote>
            </main>
            <footer><p>版權所有 © 2026 RuhOS 團隊</p></footer>
        </body>
        </html>
        """
        title, body = WebScraper.extract_content(sample_html)
        self.assertIn("RuhOS 正式啟航", title)
        self.assertIn("自適應空間接管第一原理", body)
        self.assertIn("在愛爾蘭語中，rud 意為事物本質與船之龍骨", body)
        self.assertNotIn("ads tracking", body)
        self.assertNotIn("這是側邊欄推薦文章", body)
        self.assertNotIn("首頁", body)

    def test_02_rss_parser(self):
        """測試 RSS 2.0 XML 解析器"""
        rss_xml = """<?xml version="1.0" encoding="UTF-8"?>
        <rss version="2.0">
            <channel>
                <title>科技新知 RSS</title>
                <link>https://example.com</link>
                <description>每日科技精選</description>
                <item>
                    <title>第一則新聞：AI 革命到來</title>
                    <link>https://example.com/news/1</link>
                    <description>這是第一則科技快訊的詳細摘要內容。</description>
                </item>
                <item>
                    <title>第二則新聞：許氏鍵盤自然打字</title>
                    <link>https://example.com/news/2</link>
                    <description>雙拼狀態機與大十閉環語意調校技術。</description>
                </item>
            </channel>
        </rss>
        """
        items = RSSCollector.parse_feed_xml(rss_xml)
        self.assertEqual(len(items), 2)
        self.assertEqual(items[0]["title"], "第一則新聞：AI 革命到來")
        self.assertEqual(items[0]["link"], "https://example.com/news/1")
        self.assertIn("詳細摘要內容", items[0]["content"])
        self.assertEqual(items[1]["title"], "第二則新聞：許氏鍵盤自然打字")

    def test_03_source_manager_registry(self):
        """測試 SourceManager 儲存語料與登記 source_registry.tsv"""
        manager = SourceManager(str(self.test_dir))
        self.assertTrue(manager.registry_path.exists())

        meta = SourceMetadata(
            source_id="web_test01",
            source_type=SourceType.WEB,
            origin_url="https://test.example.com/article/1",
            title="測試文章",
            license="CC-BY-SA 4.0"
        )
        res = FetchResult(
            success=True,
            source_meta=meta,
            raw_content="<p>原始 HTML 內容</p>",
            extracted_text="這是抽取出來的高純度正文測試文本。"
        )

        saved_meta = manager.save_fetch_result(res)
        self.assertIsNotNone(saved_meta)
        self.assertTrue(Path(saved_meta.raw_file_path).exists())

        # 檢驗 TSV 註冊表
        sources = manager.list_sources()
        self.assertEqual(len(sources), 1)
        self.assertEqual(sources[0]["SOURCE_ID"], "web_test01")
        self.assertEqual(sources[0]["ORIGIN_URL"], "https://test.example.com/article/1")
        self.assertEqual(sources[0]["TITLE"], "測試文章")
        self.assertEqual(sources[0]["LICENSE"], "CC-BY-SA 4.0")

        # 測試去重：重複 URL 不重複追加
        saved_again = manager.save_fetch_result(res, overwrite=False)
        self.assertEqual(len(manager.list_sources()), 1)

    def test_04_bilingual_aligner(self):
        """測試 BilingualAligner 解析英漢平行對齊卡片文本"""
        from ruhmark.bilingual import BilingualAligner

        sample_card = self.test_dir / "sample_bilingual_card.txt"
        content = """No attachment to worldly objects will be developed if we observe Yama and Niyama. Hence your mind becomes absorbed in Brahma.

Shrii Shrii Ánandamúrti
c. 1955 DMC
08 The Form of Sádhaná
Subháśita Saḿgraha Part 1

如果我們能遵循外在行為的控制和內在行為的控制，就會發展出對世俗事物沒有執著之心。心靈就會融入至上意識──靈性修持的最終目標。

Shrii Shrii Ánandamúrti
約1955年於某大法會
09 云何靈性修持
靈性科學集成 卷1，P.119

https://example.com/share/test
"""
        sample_card.write_text(content, encoding="utf-8")

        pair = BilingualAligner.parse_txt_card_file(sample_card)
        self.assertIsNotNone(pair)
        self.assertIn("No attachment to worldly objects", pair.en_text)
        self.assertIn("如果我們能遵循外在行為的控制", pair.zh_text)
        self.assertIn("The Form of Sádhaná", pair.citation_en)
        self.assertIn("云何靈性修持", pair.citation_zh)
        self.assertNotIn("https://", pair.zh_text)


if __name__ == "__main__":
    unittest.main()
