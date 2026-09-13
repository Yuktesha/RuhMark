"""
RuhMark (如標) AI Benchmark & Canonical Terminology System
ruhmark.canonical - 巴巴靈性典籍正名規範辭典與義理昇華模組
"""

import re
from typing import Dict, List, Tuple
from dataclasses import dataclass

@dataclass
class CanonicalTerm:
    sanskrit_or_en: str     # 原文詞 (如 Tantra, Surrender, Seva)
    flawed_legacy: List[str] # 舊有有毒/爭議譯名 (如 密宗, 臣服, 帕拉尼帕塔)
    canonical_zh: str       # 推薦正名譯詞 (如 搪碴, 誠服, 協峇/服務)
    rationale: str          # 義理正名理由與語言學考證

CANONICAL_REGISTRY: List[CanonicalTerm] = [
    CanonicalTerm(
        sanskrit_or_en="Tantra",
        flawed_legacy=["密宗", "密教", "坦陀羅"],
        canonical_zh="搪碴",
        rationale="Tańam (粗鈍碴滓) tárayet (掃除抵擋) yastu sah tantrah parikiirtitah。音義兼備，破除神秘宗派誤解。"
    ),
    CanonicalTerm(
        sanskrit_or_en="Surrender",
        flawed_legacy=["臣服", "投降", "順服"],
        canonical_zh="誠服",
        rationale="去封建威權奴性之『臣』，存真摯無私託付之『誠』，呼應 Śaraṇāgati 奔向庇護之愛。"
    ),
    CanonicalTerm(
        sanskrit_or_en="Sevá",
        flawed_legacy=["協瓦", "色瓦"],
        canonical_zh="協峇",
        rationale="取台語『峇』(va / bûn-ba̍t 吻峇融洽) 韻，意兼同心協和奉獻眾生以達天人相契。通俗作『服務眾生』。"
    ),
    CanonicalTerm(
        sanskrit_or_en="Bhakti",
        flawed_legacy=["虔誠", "虔敬"],
        canonical_zh="敬慕",
        rationale="以『敬』去輕浮恐懼，以『慕』顯深情眷戀，取代封建神威下的拜神式『虔誠』。"
    ),
    CanonicalTerm(
        sanskrit_or_en="PROUT",
        flawed_legacy=["進步利用論", "利用論"],
        canonical_zh="輝透論",
        rationale="取台語 Hui-thàu 音義，潛能光輝燦爛展現、資源流通穿透無礙。學術亦稱『進步善用論』，洗除『利用』之剝削惡名。"
    ),
    CanonicalTerm(
        sanskrit_or_en="Guru",
        flawed_legacy=["邪教上師", "神棍導師"],
        canonical_zh="箍攄",
        rationale="取台語 khoo-lu 音義，『箍』聚散漫心靈、『攄』除無明障礙。義理亦作『破暗大引路者』。"
    ),
    CanonicalTerm(
        sanskrit_or_en="Neohumanism",
        flawed_legacy=["新人道主義"],
        canonical_zh="抭郎主義",
        rationale="取台語 niú-lâng 音義，『抭』扭轉超越人類中心傲慢。通俗作『超越人道主義』。"
    ),
    CanonicalTerm(
        sanskrit_or_en="Madhuvidyá",
        flawed_legacy=["蜜糖科學", "甘露思維"],
        canonical_zh="蜜融慧光",
        rationale="轉世間一切粗鈍苦楚為至上甘甜恩典，融蜜顯慧之真觀。"
    ),
    CanonicalTerm(
        sanskrit_or_en="Praṇipāta",
        flawed_legacy=["帕拉尼帕塔", "啪啦泥怕塔"],
        canonical_zh="Praṇipāta",
        rationale="拒絕無意義死音譯，直接保留標準羅馬拼音梵字。"
    ),
    CanonicalTerm(
        sanskrit_or_en="Pariprashna",
        flawed_legacy=["帕里樸拉仙那", "帕里普拉仙那"],
        canonical_zh="Pariprashna",
        rationale="拒絕無意義死音譯，直接保留標準羅馬拼音梵字。"
    ),
    CanonicalTerm(
        sanskrit_or_en="Dharma",
        flawed_legacy=["宗教", "佛法"],
        canonical_zh="法性",
        rationale="萬事萬物客觀存在之原理原則，去宗教玄學化。"
    ),
    CanonicalTerm(
        sanskrit_or_en="Sādhana",
        flawed_legacy=["苦行", "消極修行"],
        canonical_zh="靈性修持",
        rationale="心靈科學能階躍升與動態鍛鍊實踐。"
    ),
]

class CanonicalTerminology:
    """正名規則引擎：升級既有舊語料，並提供大模型系統指令提示"""

    @classmethod
    def refine_legacy_chinese(cls, text: str) -> Tuple[str, Dict[str, int]]:
        """將舊有譯文中的爭議名詞自動升級為正名規範"""
        stats = {}
        result = text
        
        # 替換封建/爭議詞彙與死音譯
        replacements = [
            (r"臣服", "誠服"),
            (r"密宗", "搪碴 (Tantra)"),
            (r"進步利用論", "輝透論 (PROUT)"),
            (r"帕拉尼帕塔\s*(\([^)]*Pra[^)]*\))?", "Praṇipāta"),
            (r"帕里[樸普]拉仙那\s*(\([^)]*Pariprashna[^)]*\))?", "Pariprashna"),
            (r"協瓦\s*(\([^)]*se[^)]*\))?", "協峇 (Sevá)"),
        ]

        for pat, repl in replacements:
            matches = len(re.findall(pat, result))
            if matches > 0:
                result = re.sub(pat, repl, result)
                stats[pat] = matches

        return result, stats

    @classmethod
    def get_llm_system_prompt(cls) -> str:
        """產生注入大模型 (Gemma 4) 的專屬正名引導 System Prompt"""
        return (
            "你是一位專精於 Shrii Shrii Ánandamúrti 靈性典籍的首席翻譯家與靈性科學家。\n"
            "在翻譯時必須遵守以下最高語言學與靈性正名準則：\n"
            "1. 【拒絕無意義死音譯】：如 Praṇipāta, Pariprashna, Sādhana, Citta, Ahaṁ, Mahat 等專名，優先保留標準羅馬拼音梵字。\n"
            "2. 【正名昇華】：\n"
            "   - 將 Tantra 譯為『搪碴』(取掃除粗鈍之意) 或保留原文，絕不可使用容易混淆唐密藏密的『密宗』。\n"
            "   - 將 Surrender 譯為『誠服』(真誠信賴託付)，絕不可使用帶有封建奴役色彩的『臣服』。\n"
            "   - 將 Sevá 譯為『服務眾生』或雅稱『協峇』(取台語相峇 bûn-ba̍t 吻合融洽、同心奉獻之實相)。\n"
            "   - 將 Bhakti 譯為『敬慕』(敬重且深情思慕)，取代封建拜神恐懼式的『虔誠』。\n"
            "   - 將 PROUT 譯為『輝透論』(取台語 Hui-thàu 燦爛展現、暢通無阻) 或『進步善用論』，絕不用帶有剝削貶義的『利用論』。\n"
            "   - 將 Dharma 譯為中性客觀的『法性』或『存在本則』(萬事萬物客觀原理原則)，絕不用『宗教』或局限於佛教之字眼。\n"
            "   - 將 Neohumanism 譯為『超越人道主義』或『抭郎主義』(扭轉人類中心主義)。\n"
            "   - 將 Guru 尊稱為『破暗大引路者』，亦可借台語『箍攄』(聚散心、攄無明)，絕不落入造神迷信。\n"
            "3. 文風典雅莊重，純淨正體中文，具備微言大義的靈性科學美感。"
        )
