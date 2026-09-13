"""
RuhMark (如標) AI Benchmark & Corpus Preprocessor Platform
ruhmark.cli - 命令列管理與操作中樞
"""

import sys
import os
import argparse
from pathlib import Path

# 確保 Windows 終端機 UTF-8 輸出安全相容
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# 確保上一層路徑可供 Python 識別模組
CURRENT_DIR = Path(__file__).resolve().parent
PARENT_DIR = CURRENT_DIR.parent
if str(PARENT_DIR) not in sys.path:
    sys.path.insert(0, str(PARENT_DIR))

from ruhmark.models import CleanOptions
from ruhmark.pipeline import RuhMarkPipeline
from ruhmark.exporter import DatasetExporter
from ruhmark.reader import CorpusReader


def cmd_clean(args):
    """執行語料清洗前處理"""
    print(f"\n🚀 [RuhMark] 開始清洗語料: {args.input}")
    options = CleanOptions(
        min_sentence_len=args.min_len,
        max_sentence_len=args.max_len,
        deduplicate=not args.no_dedup,
        filter_news_boilerplates=not args.no_boilerplate_filter,
        require_chinese=args.chinese_only,
        vetted_color_only=getattr(args, "vetted_only", False),
    )
    pipeline = RuhMarkPipeline(options=options)
    items, stats = pipeline.process_source(
        source_path=args.input,
        output_tsv=args.output,
        category=args.category
    )

    print("\n" + "=" * 50)
    print("📊 RuhMark 語料清洗統計摘要報表")
    print("=" * 50)
    print(f"  • 原始讀取文件數  : {stats.raw_documents_count}")
    print(f"  • 原始總字元數    : {stats.raw_characters_count}")
    print(f"  • 清洗產出有效句數: {stats.clean_sentences_count}")
    print(f"  • 清洗後總字元數  : {stats.clean_characters_count}")
    print(f"  • 移除過短句子數  : {stats.dropped_short_count} (< {args.min_len} 字)")
    print(f"  • 移除超長片段數  : {stats.dropped_long_count} (> {args.max_len} 字)")
    if stats.dropped_non_chinese_count > 0:
        print(f"  • 過濾非中文語句  : {stats.dropped_non_chinese_count}")
    print(f"  • 剔除新聞廣告樣板: {stats.dropped_boilerplate_count}")
    print(f"  • 消除重複語句數  : {stats.duplicates_removed_count}")
    print(f"  • 清除 HTML 標籤  : {stats.html_tags_cleaned_count}")
    print(f"  • 清除 URL/Email  : {stats.urls_cleaned_count}")
    print(f"  • 壓縮多餘標點數  : {stats.punctuation_compressed_count}")
    print(f"  • 剔除隱形字元數  : {stats.invisible_chars_stripped_count}")
    print(f"  • 總耗時          : {stats.elapsed_seconds:.3f} 秒")
    print("=" * 50)

    if args.output:
        print(f"✅ 清洗完成之標準 TSV 已匯出至: {args.output}\n")

    if args.verbose and items:
        print("🔍 清洗樣本預覽 (前 5 句):")
        for idx, it in enumerate(items[:5]):
            print(f"  [{idx+1}] ({it.difficulty.value} | 覆蓋:{it.feasible_ruhi} | OOV:{it.oov_rate:.2%}) {it.clean_text}")
        print()


def cmd_split(args):
    """將清洗好的 TSV 切分為 Calibration / Validation / Benchmark"""
    print(f"\n📦 [RuhMark] 切分資料集: {args.input} ➔ {args.output_dir}")
    import csv
    from ruhmark.models import CorpusItem, DifficultyLevel

    items = []
    with open(args.input, "r", encoding="utf-8") as f:
        reader = csv.reader(f, delimiter="\t")
        for idx, parts in enumerate(reader):
            if not parts or not any(parts):
                continue
            if idx == 0 and parts[0] == "CORPUS_ID":
                continue
            if len(parts) >= 6:
                c_id, cat, diff, length, oov, clean_t = parts[:6]
                feasible = parts[6] == "YES" if len(parts) > 6 else True
                note = parts[7] if len(parts) > 7 else ""
                diff_enum = DifficultyLevel(diff) if diff in ["L1", "L2", "L3"] else DifficultyLevel.L1
                it = CorpusItem(
                    corpus_id=c_id,
                    raw_text=clean_t,
                    clean_text=clean_t,
                    category=cat,
                    difficulty=diff_enum,
                    char_len=int(length) if length.isdigit() else len(clean_t),
                    oov_rate=float(oov) if oov.replace(".", "", 1).isdigit() else 0.0,
                    feasible_ruhi=feasible,
                    note=note
                )
                items.append(it)

    print(f"  • 讀取到 {len(items)} 筆語料")
    res = DatasetExporter.split_and_export(
        items,
        output_dir=args.output_dir,
        prefix=args.prefix,
        train_ratio=args.train_ratio,
        val_ratio=args.val_ratio,
        test_ratio=args.test_ratio
    )
    for k, p in res.items():
        print(f"  ✅ {k.upper():12s}: {p}")
    print()


def cmd_fetch(args):
    """執行語料採集並存入原始庫與登記 SourceRegistry"""
    print(f"\n🌐 [RuhFetcher] 開始採集語料: {args.target}")
    from ruhmark.fetcher import WebScraper, RSSCollector, WikiFetcher, SourceManager

    manager = SourceManager(args.output_dir)

    results = []
    if args.wiki:
        print("  • 模式: 維基百科條目抽取")
        res = WikiFetcher.fetch_article(args.target)
        results.append(res)
    elif args.rss:
        print("  • 模式: RSS / Atom 頻道訂閱")
        results = RSSCollector.fetch_feed(args.target, fetch_full_articles=args.full, max_items=args.max_items)
    else:
        print("  • 模式: 網頁正文抽取")
        res = WebScraper.fetch_url(args.target)
        results.append(res)

    saved_count = 0
    for r in results:
        if r.success:
            meta = manager.save_fetch_result(r, overwrite=args.overwrite)
            if meta:
                saved_count += 1
                print(f"  ✅ 成功採集: {meta.title or meta.origin_url} ({meta.char_len} 字) ➔ {meta.raw_file_path}")
        else:
            print(f"  ❌ 採集失敗: {r.error_message}")

    print(f"\n📊 採集完成: 成功儲存 {saved_count}/{len(results)} 筆語料至 {args.output_dir}")
    print(f"  • 來源註冊表: {manager.registry_path}\n")


def cmd_harvest(args):
    """一鍵採集即清洗流水線 (Harvest: Fetch -> Clean -> Profile -> TSV)"""
    print(f"\n🌾 [RuhMark Harvest] 一鍵採集即清洗流水線啟動: {args.target}")
    from ruhmark.fetcher import WebScraper, RSSCollector, WikiFetcher, SourceManager
    from ruhmark.pipeline import RuhMarkPipeline
    from ruhmark.models import CleanOptions, CorpusItem
    from ruhmark.exporter import DatasetExporter

    manager = SourceManager(args.raw_dir)

    # 1. 採集
    if args.wiki:
        res = WikiFetcher.fetch_article(args.target)
        fetch_items = [res]
    elif args.rss:
        fetch_items = RSSCollector.fetch_feed(args.target, fetch_full_articles=True, max_items=args.max_items)
    else:
        res = WebScraper.fetch_url(args.target)
        fetch_items = [res]

    valid_results = [r for r in fetch_items if r.success]
    if not valid_results:
        print("❌ 採集階段未獲取任何有效內容，終止清洗流水線。")
        return

    # 儲存至原始庫
    for r in valid_results:
        manager.save_fetch_result(r)

    # 2. 清洗與剖析
    options = CleanOptions(
        min_sentence_len=args.min_len,
        max_sentence_len=args.max_len,
        deduplicate=True,
        require_chinese=args.chinese_only,
    )
    pipeline = RuhMarkPipeline(options=options)

    all_items = []
    for r in valid_results:
        doc_text = r.extracted_text or r.raw_content
        sentences = pipeline.clean_single_text(doc_text)
        for s_idx, sent in enumerate(sentences):
            corpus_id = f"{r.source_meta.source_id}_{s_idx+1:04d}"
            c_item = CorpusItem(
                corpus_id=corpus_id,
                raw_text=sent,
                clean_text=sent,
                category=args.category,
                metadata={"title": r.source_meta.title, "url": r.source_meta.origin_url}
            )
            all_items.append(c_item)

    # 3. 詞庫特徵剖析
    profiled_items, profile_summary = pipeline.profiler.profile_batch(all_items)

    # 4. 匯出 TSV
    DatasetExporter.export_tsv(profiled_items, args.output)

    print("\n" + "=" * 50)
    print("🌾 Harvest 全流程採集即清洗成果報表")
    print("=" * 50)
    print(f"  • 採集來源數      : {len(valid_results)}")
    print(f"  • 產出標準評測句數: {len(profiled_items)}")
    print(f"  • 詞庫可行性比率  : {profile_summary['feasibility_percent']}%")
    print(f"  • 平均未登錄字比率: {profile_summary['avg_oov_rate']:.2%}")
    print(f"  • 難度分佈 (L1/L2/L3): {profile_summary['difficulty_distribution']}")
    print(f"  • 輸出 TSV 檔案   : {args.output}")
    print("=" * 50 + "\n")

    if args.verbose and profiled_items:
        print("🔍 採集清洗樣本 (前 5 句):")
        for idx, it in enumerate(profiled_items[:5]):
            print(f"  [{idx+1}] ({it.difficulty.value} | 覆蓋:{it.feasible_ruhi} | OOV:{it.oov_rate:.2%}) {it.clean_text}")
        print()


def cmd_align(args):
    """執行雙語平行語料庫對齊抽取"""
    print(f"\n🌐 [RuhMark Align] 開始抽取英漢雙語平行語料: {args.input}")
    from ruhmark.bilingual import BilingualAligner

    pairs, total_scanned = BilingualAligner.align_directory(args.input, args.output)
    print("\n" + "=" * 50)
    print("📊 RuhMark 雙語平行對齊統計報表")
    print("=" * 50)
    print(f"  • 掃描檔案總數    : {total_scanned}")
    print(f"  • 成功配對對齊數  : {len(pairs)}")
    print(f"  • 匯出 TSV 檔案   : {args.output}")
    print("=" * 50 + "\n")

    if args.verbose and pairs:
        print("🔍 對齊樣本預覽 (前 3 筆):")
        for idx, p in enumerate(pairs[:3]):
            print(f"  [{idx+1}] ({p.pair_id})")
            print(f"      EN: {p.en_text[:80]}...")
            print(f"      ZH: {p.zh_text[:80]}...")
        print()


def main():
    parser = argparse.ArgumentParser(
        prog="ruhmark",
        description="RuhMark (如標) AI 語料採集、清洗前處理器與基準評測框架"
    )
    subparsers = parser.add_subparsers(dest="subcommand", help="子命令")

    # clean 子命令
    parser_clean = subparsers.add_parser("clean", help="清洗並規整原始語料為標準 TSV")
    parser_clean.add_argument("input", type=str, help="輸入檔案路徑或目錄")
    parser_clean.add_argument("-o", "--output", type=str, default="cleaned_corpus.tsv", help="輸出 TSV 路徑")
    parser_clean.add_argument("--category", type=str, default="general", help="語料類別分類")
    parser_clean.add_argument("--min-len", type=int, default=6, help="最短句子長度 (預設 6)")
    parser_clean.add_argument("--max-len", type=int, default=120, help="最長句子長度 (預設 120)")
    parser_clean.add_argument("--no-dedup", action="store_true", help="關閉自動去重")
    parser_clean.add_argument("--no-boilerplate-filter", action="store_true", help="關閉新聞廣告樣板過濾")
    parser_clean.add_argument("--chinese-only", action="store_true", help="強制只保留含中文字元的句子 (過濾純外語行)")
    parser_clean.add_argument("--vetted-only", action="store_true", help="針對 Docx 僅抽取嫩綠色人工校對正文 (過濾預設機翻黑色)")
    parser_clean.add_argument("-v", "--verbose", action="store_true", help="詳細輸出樣本")

    # split 子命令
    parser_split = subparsers.add_parser("split", help="切分 TSV 為 Train / Valid / Benchmark")
    parser_split.add_argument("input", type=str, help="輸入已清洗之 TSV 檔案")
    parser_split.add_argument("-o", "--output-dir", type=str, default="./splits", help="輸出目錄")
    parser_split.add_argument("--prefix", type=str, default="ruhmark", help="檔案名稱前綴")
    parser_split.add_argument("--train-ratio", type=float, default=0.8, help="訓練/校正集比例 (預設 0.8)")
    parser_split.add_argument("--val-ratio", type=float, default=0.1, help="驗證集比例 (預設 0.1)")
    parser_split.add_argument("--test-ratio", type=float, default=0.1, help="測試基準集比例 (預設 0.1)")

    # fetch 子命令
    parser_fetch = subparsers.add_parser("fetch", help="從網路、RSS 或維基百科採集語料至原始倉儲")
    parser_fetch.add_argument("target", type=str, help="採集目標 (網址 URL、RSS Feed、或維基條目名)")
    parser_fetch.add_argument("-o", "--output-dir", type=str, default="./raw_corpus", help="原始語料儲存目錄")
    parser_fetch.add_argument("--wiki", action="store_true", help="指定目標為維基百科條目名")
    parser_fetch.add_argument("--rss", action="store_true", help="指定目標為 RSS/Atom 訂閱頻道")
    parser_fetch.add_argument("--full", action="store_true", help="RSS 模式下進一步抓取文章全文")
    parser_fetch.add_argument("--max-items", type=int, default=10, help="RSS 抓取條目上限 (預設 10)")
    parser_fetch.add_argument("--overwrite", action="store_true", help="強制重新抓取覆寫現有登記")

    # harvest 子命令 (一鍵採集即清洗)
    parser_harvest = subparsers.add_parser("harvest", help="一鍵採集即清洗流水線 (Fetch ➔ Clean ➔ TSV)")
    parser_harvest.add_argument("target", type=str, help="採集目標 (網址 URL、RSS Feed、或維基條目名)")
    parser_harvest.add_argument("-o", "--output", type=str, default="harvested_benchmark.tsv", help="輸出標準 TSV 路徑")
    parser_harvest.add_argument("--raw-dir", type=str, default="./raw_corpus", help="原始語料存檔目錄")
    parser_harvest.add_argument("--category", type=str, default="web_harvest", help="語料類別")
    parser_harvest.add_argument("--wiki", action="store_true", help="指定目標為維基百科條目名")
    parser_harvest.add_argument("--rss", action="store_true", help="指定目標為 RSS/Atom 訂閱頻道")
    parser_harvest.add_argument("--max-items", type=int, default=10, help="RSS 抓取條目上限")
    parser_harvest.add_argument("--min-len", type=int, default=6, help="最短句子長度")
    parser_harvest.add_argument("--max-len", type=int, default=120, help="最長句子長度")
    parser_harvest.add_argument("--chinese-only", action="store_true", help="強制只保留含中文字元的句子 (過濾純外語行)")
    parser_harvest.add_argument("-v", "--verbose", action="store_true", help="詳細輸出樣本")

    # align 子命令 (英漢雙語平行對齊抽取)
    parser_align = subparsers.add_parser("align", help="抽取英漢雙語平行對齊語料庫")
    parser_align.add_argument("input", type=str, help="輸入雙語文檔目錄 (例如 _TXT 目錄)")
    parser_align.add_argument("-o", "--output", type=str, default="bilingual_parallel.tsv", help="輸出 TSV 路徑")
    parser_align.add_argument("-v", "--verbose", action="store_true", help="詳細輸出樣本")

    args = parser.parse_args()
    if args.subcommand == "clean":
        cmd_clean(args)
    elif args.subcommand == "split":
        cmd_split(args)
    elif args.subcommand == "fetch":
        cmd_fetch(args)
    elif args.subcommand == "harvest":
        cmd_harvest(args)
    elif args.subcommand == "align":
        cmd_align(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
