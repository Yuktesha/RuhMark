# RuhMark (如標) ⚡

**High-Performance AI Training Corpus Preprocessor, Bilingual Parallel Aligner, and Benchmark Suite for LLMs & SLMs**

[![Python Version](https://img.shields.io/badge/python-3.9%20%7C%203.10%20%7C%203.11%20%7C%203.12%20%7C%203.14-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Code Style](https://img.shields.io/badge/code%20style-clean%20architecture-orange.svg)](https://github.com/Yuktesha/RuhMark)

> 專為大型語言模型 (LLMs)、端側輕量語言模型 (SLMs) 與智慧文字系統打造的高品質語料深度前處理、對齊與基準評測框架。

---

## 🌟 Key Highlights (核心特色)

1. **Zero-Loss Unicode & Punctuation Normalization (高精度標準化)**
   - 全角/半角自動常規化、CJK 標點符號階層統一。
   - 智能過濾多餘重複標點與網路火星字元，完整保留語氣核心。
2. **Quote-Preserving Sentence Segmentation (智慧引號保護斷句)**
   - 解決傳統 NLP 工具（如 NLTK, spaCy）在處理長對話、引號包覆多句、書名號時經常誤切的痛點。
   - 確保引文、對話在訓練時保持完整語意邊界。
3. **Multi-Source & Auto-Encoding Fallback Reader (全格式編碼容錯讀取)**
   - 自動容錯感知 `UTF-8`, `UTF-8-SIG`, `Big5`, `CP950`, `GB18030`, `UTF-16`。
   - 原生支援 `.txt`, `.md`, `.docx`, `.odt`, `.tsv`, `.csv`, `.json`, `.jsonl` 等檔案格式，無需額外繁重的外部依賴。
   - 特色感知：支援特定標註色彩（如校訂綠色文字）精準萃取。
4. **Bilingual Parallel Alignment (英漢/多語平行對齊引擎)**
   - 自動抽取引文出處、英文正文、中文出版譯文並完成段落級高精確度對稱校驗。
5. **Corpus Profiler & Complexity Metrics (語料品質評估與難度分級)**
   - 即時計算 Type-Token Ratio (TTR 詞彙多樣性)、資訊熵、難度等級（Elementary, Intermediate, Advanced, Master）。
6. **One-Click Dataset Exporter (一鍵匯出 AI 訓練格式)**
   - 一鍵產出 **Alpaca**, **ShareGPT**, **DPO**, **JSONL**, **TSV** 等主流微調格式。

---

## 💡 RuhMark vs. Microsoft MarkItDown & Others

| 評測維度 (Dimension) | Microsoft MarkItDown | 傳統 NLP 工具 (NLTK / spaCy) | **RuhMark (如標)** |
| :--- | :--- | :--- | :--- |
| **核心定位** | 文檔格式轉換 (Doc ➔ Markdown) | 基礎語法與詞性標記 | **LLM/SLM 訓練語料深度前處理與評測** |
| **格式支援** | Office, PDF 轉純文字 Markdown | 通常僅支援純字串輸入 | 原生讀取 Office/ODT/JSONL/TSV + 自動多重編碼容錯 |
| **引號保護切句** | ❌ 無 (僅輸出純文字) | ⚠️ 常在引號內部誤斷句 | **✅ 專利級配對引號保護智慧切句** |
| **繁簡標點常規化** | ❌ 無 | ⚠️ 需自寫規則正則表達式 | **✅ 內建 CJK 與雙語標點標準化規則引擎** |
| **雙語平行對齊** | ❌ 無 | ❌ 無 | **✅ 內建段落/篇章級英漢平行對齊器** |
| **AI 訓練格式匯出** | ❌ 無 | ❌ 無 | **✅ 原生匯出 Alpaca, ShareGPT, DPO** |
| **難度分級與質檢** | ❌ 無 | ⚠️ 僅有基本詞頻統計 | **✅ TTR 詞彙多樣性與語言學難度分級** |

> **設計哲學**：微軟的 MarkItDown 優秀地解決了「如何把各類文檔轉為 Markdown」的前半段格式問題；而 **RuhMark** 則接力解決了「**如何將雜亂的文本進一步提煉、去噪、對齊並分級為大模型可以直接吃的高品質訓練資料**」的核心問題。

---

## 🚀 Quick Start (快速上手)

### 1. Installation (安裝)

```bash
git clone https://github.com/Yuktesha/RuhMark.git
cd RuhMark
pip install -e .
```

### 2. Python API Usage (代碼範例)

```python
from ruhmark import (
    RuhMarkPipeline,
    CleanOptions,
    CorpusProfiler,
    DatasetExporter,
)

# 1. 建立前處理流水線
pipeline = RuhMarkPipeline(
    options=CleanOptions(
        remove_urls=True,
        remove_html_tags=True,
        filter_news_boilerplates=True,
        protect_dialog_quotes=True,
        compress_repeated_punctuation=True,
    )
)

raw_text = """
【專題報導】引自官方消息（https://example.com/item）：
「真正的修行者，在動態的世界中保持心靈的和諧。」這是一段深邃的指引！！！
難道不是至上的哲學嗎？？？
"""

# 2. 深度清洗與引號保護切句
sentences = pipeline.clean_single_text(raw_text)
for i, s in enumerate(sentences, 1):
    print(f"[{i}] {s}")

# 3. 語料難度與品質評估
profiler = CorpusProfiler()
profile = profiler.profile_text(" ".join(sentences))
print(f"詞彙多樣性 (TTR): {profile.ttr:.4f}")
print(f"預估語言難度: {profile.difficulty}")
```

### 3. CLI Command Line Interface (命令列工具)

```bash
# 1. 批量清洗資料夾下所有文本並輸出乾淨 TSV
python -m ruhmark.cli clean --input ./raw_data --output ./cleaned_data.tsv

# 2. 執行語料庫品質與難度檢測
python -m ruhmark.cli profile --input ./cleaned_data.tsv

# 3. 轉換為 Alpaca 微調格式
python -m ruhmark.cli export --input ./cleaned_data.tsv --format alpaca --output train.json
```

---

## 📂 Architecture & Directory Structure (專案架構)

```text
RuhMark/
├── ruhmark/
│   ├── reader.py          # 多格式 (docx/odt/txt/tsv/json) 與自動編碼容錯讀取
│   ├── cleaner.py         # 深度雜訊清洗 (HTML, URL, 樣板過濾, 標點壓縮)
│   ├── normalizer.py      # Unicode 與全半形標準化引擎
│   ├── segmenter.py       # 引號保護智慧語意斷句器
│   ├── profiler.py        # TTR 詞彙多樣性、複雜度與難度分級引擎
│   ├── exporter.py        # Alpaca / ShareGPT / DPO / JSONL 匯出器
│   ├── bilingual.py       # 英漢雙語平行對齊引擎
│   ├── canonical.py       # 哲學與專用術語正名辭典
│   └── pipeline.py        # 全流程自動化 Pipeline 核心
├── examples/
│   └── quickstart.py      # 快速入門示範腳本
├── tests/                 # 單元測試集 (pytest)
├── pyproject.toml         # 標準 Python 打包配置
├── setup.py               # 安裝腳本
└── LICENSE                # MIT 開源許可證
```

---

## 🤝 Contributing & Community

歡迎提交 Issue 與 Pull Request！
若您在 LLM 微調、端側模型語料清洗、雙語對齊等場景中有任何建議，歡迎共同交流。

## 📄 License

本專案採用 [MIT License](LICENSE) 開源授權。
