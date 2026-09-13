"""
RuhMark (如標) AI Benchmark & Corpus Preprocessor Platform
專為 RuhOS 本地 AI 層、端側語言模型與 Ruhi 智慧輸入法打造的高品質語料前處理與基準評測框架。
"""

__version__ = "0.1.0"
__author__ = "RuhOS AI Team & Da-Shi (大十)"

from .models import CorpusItem, CleanOptions, CleaningStats, DifficultyLevel, TokenMeta
from .reader import CorpusReader
from .normalizer import TextNormalizer
from .cleaner import NoiseCleaner
from .segmenter import SentenceSegmenter
from .profiler import CorpusProfiler
from .exporter import DatasetExporter
from .pipeline import RuhMarkPipeline

from .bilingual import BilingualAligner, BilingualPair
from .canonical import CanonicalTerm, CANONICAL_REGISTRY

__all__ = [
    "CorpusItem",
    "CleanOptions",
    "CleaningStats",
    "DifficultyLevel",
    "TokenMeta",
    "CorpusReader",
    "TextNormalizer",
    "NoiseCleaner",
    "SentenceSegmenter",
    "CorpusProfiler",
    "DatasetExporter",
    "RuhMarkPipeline",
    "BilingualAligner",
    "BilingualPair",
    "CanonicalTerm",
    "CANONICAL_REGISTRY",
]
