"""
RuhMark (如標) AI Benchmark & Corpus Preprocessor Platform
ruhmark.reader - 多來源格式與自動編碼相容讀取器
"""

import os
import json
import csv
from pathlib import Path
from typing import Generator, Tuple, Dict, Any, List, Optional


class CorpusReader:
    """支援多種文字格式與編碼感知之語料讀取器"""

    CANDIDATE_ENCODINGS = ["utf-8", "utf-8-sig", "big5", "cp950", "gb18030", "utf-16"]

    @classmethod
    def read_file_with_fallback(cls, file_path: str) -> Tuple[str, str]:
        """嘗試以多種編碼讀取檔案，回傳 (內容, 成功偵測之編碼)"""
        with open(file_path, "rb") as f:
            raw_bytes = f.read()

        for enc in cls.CANDIDATE_ENCODINGS:
            try:
                text = raw_bytes.decode(enc)
                return text, enc
            except (UnicodeDecodeError, LookupError):
                continue

        # 最後一道防線：使用 utf-8 搭配 replace 容錯替換
        return raw_bytes.decode("utf-8", errors="replace"), "utf-8-replace"

    @staticmethod
    def _is_green_color(hex_val: str) -> bool:
        """判定色彩是否為校正對齊之嫩綠色 (如 81D41A, 00A933 等)"""
        if not hex_val or hex_val.lower() == "auto" or len(hex_val) != 6:
            return False
        try:
            r = int(hex_val[0:2], 16)
            g = int(hex_val[2:4], 16)
            b = int(hex_val[4:6], 16)
            return g > r * 1.1 and g > b * 1.1 and g > 75
        except Exception:
            return False

    @classmethod
    def iterate_source(
        cls,
        path_str: str,
        recursive: bool = True,
        vetted_color_only: bool = False
    ) -> Generator[Tuple[str, str, Dict[str, Any]], None, None]:
        """
        遞迴或單一讀取目標路徑，產出 (doc_id, text, metadata)
        支援: .txt, .md, .tsv, .csv, .json, .jsonl, .docx, .odt
        """
        p = Path(path_str)
        if not p.exists():
            raise FileNotFoundError(f"找不到指定路徑: {path_str}")

        if p.is_file():
            yield from cls._process_single_file(p, vetted_color_only=vetted_color_only)
        elif p.is_dir():
            pattern = "**/*" if recursive else "*"
            for item in sorted(p.glob(pattern)):
                if item.is_file() and not item.name.startswith("."):
                    yield from cls._process_single_file(item, vetted_color_only=vetted_color_only)

    @classmethod
    def _process_single_file(
        cls,
        file_path: Path,
        vetted_color_only: bool = False
    ) -> Generator[Tuple[str, str, Dict[str, Any]], None, None]:
        suffix = file_path.suffix.lower()
        doc_id_base = file_path.stem

        if suffix in [".txt", ".md", ".text"]:
            text, enc = cls.read_file_with_fallback(str(file_path))
            meta = {"file_path": str(file_path), "encoding": enc, "format": suffix}
            yield (doc_id_base, text, meta)

        elif suffix == ".jsonl":
            text, enc = cls.read_file_with_fallback(str(file_path))
            for idx, line in enumerate(text.splitlines()):
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                    # 常見文字欄位抽取: text, content, raw, sentence
                    content = ""
                    for k in ["text", "content", "sentence", "raw", "article"]:
                        if k in obj and isinstance(obj[k], str):
                            content = obj[k]
                            break
                    if not content and isinstance(obj, str):
                        content = obj

                    doc_id = f"{doc_id_base}_{idx+1}"
                    meta = {"file_path": str(file_path), "line_idx": idx, "encoding": enc, "json_raw": obj}
                    yield (doc_id, content, meta)
                except json.JSONDecodeError:
                    continue

        elif suffix == ".json":
            text, enc = cls.read_file_with_fallback(str(file_path))
            try:
                data = json.loads(text)
                if isinstance(data, list):
                    for idx, item in enumerate(data):
                        content = item if isinstance(item, str) else item.get("text", item.get("content", str(item)))
                        doc_id = f"{doc_id_base}_{idx+1}"
                        meta = {"file_path": str(file_path), "item_idx": idx, "encoding": enc}
                        yield (doc_id, content, meta)
                elif isinstance(data, dict):
                    content = data.get("text", data.get("content", data.get("article", "")))
                    if not content:
                        content = str(data)
                    meta = {"file_path": str(file_path), "encoding": enc}
                    yield (doc_id_base, content, meta)
            except json.JSONDecodeError:
                pass

        elif suffix in [".tsv", ".csv"]:
            delimiter = "\t" if suffix == ".tsv" else ","
            text, enc = cls.read_file_with_fallback(str(file_path))
            reader = csv.reader(text.splitlines(), delimiter=delimiter)
            header = None
            for idx, row in enumerate(reader):
                if not row or not any(row):
                    continue
                if idx == 0 and ("text" in "".join(row).lower() or "word" in "".join(row).lower() or "語料" in "".join(row)):
                    header = [c.strip().lower() for c in row]
                    continue
                
                # 嘗試依標頭抓 text 欄位，否則預設取第一或第二欄
                content = ""
                if header and "text" in header:
                    content = row[header.index("text")]
                elif header and "clean_text" in header:
                    content = row[header.index("clean_text")]
                elif len(row) > 1 and len(row[1]) > len(row[0]):
                    content = row[1]
                else:
                    content = row[0]

                doc_id = f"{doc_id_base}_{idx+1}"
                meta = {"file_path": str(file_path), "row_idx": idx, "encoding": enc}
                yield (doc_id, content, meta)

        elif suffix == ".docx":
            import zipfile
            import xml.etree.ElementTree as ET
            try:
                with zipfile.ZipFile(str(file_path)) as z:
                    xml_data = z.read("word/document.xml")
                    root = ET.fromstring(xml_data)
                    paragraphs = []
                    for p_elem in root.iter("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}p"):
                        texts = []
                        for r_elem in p_elem.iter("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}r"):
                            if vetted_color_only:
                                color_elem = r_elem.find(".//{http://schemas.openxmlformats.org/wordprocessingml/2006/main}color")
                                c_val = color_elem.attrib.get("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val", "auto") if color_elem is not None else "auto"
                                if not cls._is_green_color(c_val):
                                    continue
                            for t in r_elem.iter("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t"):
                                if t.text:
                                    texts.append(t.text)
                        line = "".join(texts).strip()
                        if line:
                            paragraphs.append(line)
                    text = "\n".join(paragraphs)
                    meta = {"file_path": str(file_path), "encoding": "docx_xml", "format": suffix, "vetted_only": vetted_color_only}
                    yield (doc_id_base, text, meta)
            except Exception:
                pass

        elif suffix == ".odt":
            import zipfile
            import xml.etree.ElementTree as ET
            try:
                with zipfile.ZipFile(str(file_path)) as z:
                    xml_data = z.read("content.xml")
                    root = ET.fromstring(xml_data)
                    paragraphs = []
                    for elem in root.iter():
                        if elem.tag.endswith("}p") or elem.tag.endswith("}h"):
                            text_content = "".join(elem.itertext()).strip()
                            if text_content:
                                paragraphs.append(text_content)
                    text = "\n".join(paragraphs)
                    meta = {"file_path": str(file_path), "encoding": "odt_xml", "format": suffix}
                    yield (doc_id_base, text, meta)
            except Exception:
                pass
