"""
RuhMark Quickstart Example
Demonstrates reading, cleaning, sentence segmentation, complexity profiling, and dataset export.
"""

import sys
from pathlib import Path
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ruhmark import (
    CorpusItem,
    RuhMarkPipeline,
    CleanOptions,
    CorpusProfiler,
    DatasetExporter,
    BilingualAligner,
)

def main():
    raw_text = """
    【特別報導】據某社群媒體透露（https://example.com/news）：
    「真正的靈性修持（Sádhaná），不是逃避世間苦難，而是直面生命。」巴巴如是說。！！！
    這難道不是宇宙進步的最高哲學嗎？？？
    """

    print("=== 1. Initializing RuhMark Pipeline ===")
    pipeline = RuhMarkPipeline(
        options=CleanOptions(
            remove_urls=True,
            remove_html_tags=True,
            filter_news_boilerplates=True,
            protect_dialog_quotes=True,
            compress_repeated_punctuation=True,
        )
    )

    print("=== 2. Cleaning & Sentence Segmentation ===")
    sentences = pipeline.clean_single_text(raw_text)
    for i, s in enumerate(sentences, 1):
        print(f"[{i}] {s}")

    print("\n=== 3. Corpus Profiling ===")
    profiler = CorpusProfiler()
    item = CorpusItem(
        corpus_id="sample_01",
        raw_text=raw_text,
        clean_text=" ".join(sentences),
    )
    profiled = profiler.profile_item(item)
    print(f"Total Characters: {profiled.char_len}")
    print(f"OOV Rate: {profiled.oov_rate:.4f}")
    print(f"Estimated Difficulty: {profiled.difficulty.value}")
    print(f"Profile Notes: {profiled.note}")

    print("\n=== RuhMark Pipeline Finished Successfully! ===")

if __name__ == "__main__":
    main()
