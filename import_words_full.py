"""
完整词库导入脚本 v2
支持：GRE词汇 + 雅思词汇真经 + 雅思场景词汇
"""
import csv
import re
import os
import pdfplumber

# ============================================================
# 1. 从雅思词汇真经 PDF 提取
# ============================================================

IELTS_BOOK_CHAPTERS = [
    ("Chapter 1", "自然地理", 12, 20),
    ("Chapter 2", "植物研究", 21, 30),
    ("Chapter 3", "动物保护", 31, 44),
    ("Chapter 4", "太空探索", 45, 52),
    ("Chapter 5", "学校教育", 53, 84),
    ("Chapter 6", "科技发明", 85, 94),
    ("Chapter 7", "文化历史", 95, 102),
    ("Chapter 8", "语言演化", 103, 108),
    ("Chapter 9", "娱乐运动", 109, 122),
    ("Chapter 10", "物品材料", 123, 134),
    ("Chapter 11", "时尚潮流", 135, 144),
    ("Chapter 12", "饮食健康", 145, 158),
    ("Chapter 13", "建筑场所", 159, 170),
    ("Chapter 14", "交通旅行", 171, 182),
    ("Chapter 15", "国家政府", 183, 196),
    ("Chapter 16", "社会经济", 197, 212),
    ("Chapter 17", "法律法规", 213, 222),
    ("Chapter 18", "沙场争锋", 223, 240),
    ("Chapter 19", "社会角色", 241, 252),
    ("Chapter 20", "行为动作", 253, 274),
    ("Chapter 21", "身心健康", 275, 306),
    ("Chapter 22", "时间日期", 307, 311),
]


def extract_bible_words():
    """从雅思词汇真经提取所有单词"""
    words = []
    pdf_path = "D:/Desktop/雅思词汇真经.pdf"

    if not os.path.exists(pdf_path):
        print(f"找不到文件: {pdf_path}")
        return words

    with pdfplumber.open(pdf_path) as pdf:
        total_pages = len(pdf.pages)

        for chapter_name, chapter_label, start_page, end_page in IELTS_BOOK_CHAPTERS:
            start_idx = start_page - 1
            end_idx = min(end_page, total_pages)

            chapter_text = []
            for page_idx in range(start_idx, end_idx):
                page = pdf.pages[page_idx]
                text = page.extract_text()
                if text:
                    chapter_text.append(text)

            full_text = "\n".join(chapter_text)
            extracted = parse_bible_chapter(full_text, chapter_label)
            words.extend(extracted)
            print(f"  {chapter_label}: 提取 {len(extracted)} 词")

    return words


def parse_bible_chapter(text, chapter_label):
    """解析雅思词汇真经单章内容"""
    words = []
    lines = text.split('\n')

    current_word = None
    current_parts = []

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # 检测单词行
        word_match = re.match(r'^([a-zA-Z][a-zA-Z\-]+)\s*/([^/]+)/\s*(.*)$', line)
        if word_match:
            if current_word:
                word_data = build_bible_word(current_word, current_parts, chapter_label)
                if word_data:
                    words.append(word_data)

            current_word = word_match.group(1).lower()
            phonetic = word_match.group(2).strip()
            rest = word_match.group(3).strip()

            current_parts = [phonetic]
            pos, meaning = parse_pos_meaning(rest)
            if meaning:
                current_parts.append(pos)
                current_parts.append(meaning)

        elif current_word:
            if re.search(r'[一-鿿]', line) and not line.startswith('['):
                if line.startswith('(') or re.match(r'^[A-Z][a-z]+[\s]', line):
                    current_parts.append(line)
                elif current_parts:
                    current_parts[-1] = current_parts[-1] + line
            elif line.startswith('[') or (line.startswith('（') and not current_parts):
                pass
            elif re.match(r'^[A-Z].*,', line) and len(line) < 400:
                if not any('example' in str(p) for p in current_parts):
                    current_parts.append(line)

    if current_word:
        word_data = build_bible_word(current_word, current_parts, chapter_label)
        if word_data:
            words.append(word_data)

    return words


def parse_pos_meaning(text):
    if not text:
        return "", ""
    text = re.sub(r'\s+', ' ', text).strip()
    patterns = [
        (r'^n\.\s*(.+)', 'n.'),
        (r'^v\.\s*(.+)', 'v.'),
        (r'^adj\.\s*(.+)', 'adj.'),
        (r'^adv\.\s*(.+)', 'adv.'),
        (r'^prep\.\s*(.+)', 'prep.'),
        (r'^conj\.\s*(.+)', 'conj.'),
        (r'^pron\.\s*(.+)', 'pron.'),
        (r'^int\.\s*(.+)', 'int.'),
        (r'^num\.\s*(.+)', 'num.'),
        (r'^det\.\s*(.+)', 'det.'),
        (r'^vi\.\s*(.+)', 'vi.'),
        (r'^vt\.\s*(.+)', 'vt.'),
    ]
    for pattern, pos in patterns:
        m = re.match(pattern, text, re.IGNORECASE)
        if m:
            meaning = m.group(1).strip()
            meaning = re.sub(r'[,，.。;；]+.*$', '', meaning).strip()
            return pos, meaning
    meaning = re.sub(r'[,，.。;；]+.*$', '', text).strip()
    return "", meaning


def build_bible_word(word, parts, chapter_label):
    phonetic, pos, meaning_cn = "", "", ""
    example_en, example_cn = "", ""

    for p in parts:
        if '/' in p and not phonetic:
            phonetic = p
        elif p in ('n.', 'v.', 'adj.', 'adv.', 'prep.', 'conj.', 'pron.', 'int.', 'num.', 'det.', 'vi.', 'vt.'):
            if not pos:
                pos = p
        elif re.search(r'[一-鿿]', p):
            if not meaning_cn:
                meaning_cn = p
            else:
                meaning_cn += p
        elif p.startswith('[') or p.startswith('（'):
            pass
        elif re.match(r'^[A-Z].*,', p) and len(p) < 400:
            if not example_en:
                example_en = p
            elif not example_cn:
                example_cn = p

    if not meaning_cn:
        return None

    return {
        "word": word, "category": "IELTS_BOOK", "section": chapter_label,
        "subcategory": "", "phonetic": phonetic, "part_of_speech": pos,
        "meaning_cn": meaning_cn, "example_en": example_en, "example_cn": example_cn,
        "source": "雅思词汇真经.pdf", "difficulty": 2
    }


# ============================================================
# 2. 从雅思场景超核心词汇4000 PDF 提取
# ============================================================

def extract_scene_words():
    words = []
    pdf_path = "D:/Desktop/雅思场景超核心词汇4000.pdf"

    if not os.path.exists(pdf_path):
        print(f"找不到文件: {pdf_path}")
        return words

    with pdfplumber.open(pdf_path) as pdf:
        total_pages = len(pdf.pages)
        print(f"场景词汇PDF总页数: {total_pages}")

        all_pages = []
        for i, page in enumerate(pdf.pages):
            text = page.extract_text()
            if text:
                all_pages.append((i+1, text))

        section_ranges = {
            "听力词汇篇": (7, 32),
            "阅读词汇篇": (33, 93),
            "写作词汇篇": (95, 116),
            "口语词汇篇": (118, 221),
        }

        for section_name, (start_page, end_page) in section_ranges.items():
            print(f"\n  处理篇章: {section_name}")
            section_pages = [(pnum, text) for pnum, text in all_pages
                           if start_page <= pnum <= end_page]

            section_words = parse_scene_section(section_pages, section_name)
            words.extend(section_words)
            print(f"    共提取 {len(section_words)} 词")

    return words


def parse_scene_section(pages, section_name):
    """解析场景词汇篇章"""
    words = []
    current_subcategory = ""

    for page_num, text in pages:
        lines = text.split('\n')

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # 检测章节标题
            if is_section_title(line):
                new_sub = extract_subcategory(line)
                if new_sub:
                    current_subcategory = new_sub
                continue

            # 跳过非内容行
            if is_skip_line(line):
                continue

            # 写作词汇篇使用不同的格式（中文在前，英文在后）
            if section_name == "写作词汇篇":
                parsed = parse_writing_word(line, section_name, current_subcategory)
                if parsed:
                    words.extend(parsed)
                continue

            # 解析单词

            word_data = parse_scene_word(line, section_name, current_subcategory)
            if word_data:
                words.append(word_data)

    return words


def is_section_title(line):
    """判断是否是章节标题行"""
    # 听力/阅读/写作/口语 词汇篇
    if re.match(r'^(听力|阅读|写作|口语)词汇篇$', line):
        return True
    # 第一节 XXX场景
    if re.match(r'^第[一二三四五六七八九十\d]+节\s*[一-鿿a-zA-Z]+', line):
        return True
    # 一、核心词
    if re.match(r'^[一-鿿\d]+\s*[、.]\s*[一-鿿a-zA-Z]+', line) and len(line) < 25:
        return True
    # 第一节 XXX
    if re.match(r'^第[一二三四五六七八九十]+节\s+[一-鿿]+', line):
        return True
    return False


def parse_writing_word(line, section_name, subcategory):
    """解析写作词汇篇的单词行（中文在前，英文在后，中间无空格）
    例如: 获取知识acquire/gain/attain/obtain/getaccessto knowledge
    """
    results = []
    # 移除开头的非ASCII字母前缀（如bullet字符）
    m = re.match(r'^[^\x00-\x7F]*', line)
    if not m:
        return results
    stripped = line[m.end():].strip()
    if not stripped:
        return results

    # 找中文结束、英文开始的位置
    # 策略：找第一个字母前面紧挨着的位置
    chinese_end = 0
    for i in range(1, len(stripped)):
        if re.match(r'[a-zA-Z]', stripped[i]):
            # 检查前面是否有中文
            if re.match(r'[一-鿿]', stripped[i-1]):
                chinese_end = i
                break
            # 也检查更前面是否有中文（跳过标点等）
            for j in range(i-1, -1, -1):
                if re.match(r'[a-zA-Z]', stripped[j]):
                    break
                if re.match(r'[一-鿿]', stripped[j]):
                    chinese_end = i
                    break
            if chinese_end > 0:
                break

    if chinese_end == 0:
        return results

    chinese_meaning = stripped[:chinese_end]
    chinese_meaning = re.sub(r'[,，。；:！?]+.*$', '', chinese_meaning).strip()
    chinese_meaning = re.sub(r'\s+', '', chinese_meaning).strip()

    if not chinese_meaning or len(chinese_meaning) < 2:
        return results

    english_text = stripped[chinese_end:]
    english_text = re.sub(r'[,，。；:！?\s]+', ' ', english_text).strip()

    if not english_text:
        return results

    # 按 / 分割英文
    if '/' in english_text:
        english_words = english_text.split('/')
    else:
        english_words = re.split(r'[,\s]+', english_text)

    for ew in english_words:
        ew = ew.strip()
        ew = re.sub(r'^[,\s]+|[,\s]+$', '', ew)
        ew = re.sub(r'^(to|the|a|an|of|and|or|in|on|at|for|with|by)$', '', ew, flags=re.IGNORECASE)
        if re.match(r"^[a-zA-Z][a-zA-Z\-']{1,}$", ew, re.IGNORECASE):
            ew_lower = ew.lower()
            if len(ew_lower) >= 3 and ew_lower not in ('the', 'and', 'for', 'with', 'from', 'that', 'this', 'have', 'been'):
                results.append({
                    "word": ew_lower,
                    "category": "IELTS_SCENE",
                    "section": section_name,
                    "subcategory": subcategory,
                    "phonetic": "",
                    "part_of_speech": "",
                    "meaning_cn": chinese_meaning,
                    "example_en": "",
                    "example_cn": "",
                    "source": "雅思场景超核心词汇4000.pdf",
                    "difficulty": 2
                })

    return results


def extract_subcategory(line):
    """从标题行提取小节名"""
    # "一、核心词" -> "核心词"
    m = re.match(r'^[一-鿿\d]+\s*[、.]\s*(.+)$', line)
    if m:
        return m.group(1).strip()
    # "第一节 租房场景" -> "租房场景"
    m = re.match(r'^第[一二三四五六七八九十\d]+节\s+(.+)$', line)
    if m:
        return m.group(1).strip()
    return ""


def is_skip_line(line):
    """判断是否是需要跳过的行"""
    if re.match(r'^\d+$', line):
        return True
    if re.match(r'^[·.\s]{5,}$', line):
        return True
    if '听力词汇篇' in line or '阅读词汇篇' in line or '写作词汇篇' in line or '口语词汇篇' in line:
        if '词汇篇' in line and not re.search(r'[a-zA-Z]', line):
            return True
    if not re.search(r'[a-zA-Z]', line):
        return True
    return False


def parse_scene_word(line, section_name, subcategory):
    """解析场景词汇单词行"""
    # 移除开头的任意非字母前缀（PDF中bullet可能是特殊编码字符）
    m = re.match(r'^[^a-zA-Z]*([a-zA-Z].+)$', line)
    if not m:
        return None
    clean = m.group(1)

    # 格式1: word/phonetic/n. meaning  (听力/口语)
    m1 = re.match(r'^([a-zA-Z][a-zA-Z0-9\-]+)\s*/([^/]+)/\s*(.*)$', clean, re.IGNORECASE)
    if m1:
        word = m1.group(1).lower()
        phonetic = m1.group(2).strip()
        rest = m1.group(3).strip()
        pos, meaning = parse_scene_pos_meaning(rest)
        meaning = meaning.split('[')[0].strip()
        meaning = re.sub(r'[,，.。;；]+.*$', '', meaning).strip()
        if word and meaning and len(word) > 1:
            return {
                "word": word, "category": "IELTS_SCENE", "section": section_name,
                "subcategory": subcategory, "phonetic": phonetic, "part_of_speech": pos,
                "meaning_cn": meaning, "example_en": "", "example_cn": "",
                "source": "雅思场景超核心词汇4000.pdf", "difficulty": 2
            }

    # 格式2: word[phonetic]pos. meaning  (阅读)
    m2 = re.match(r'^([a-zA-Z][a-zA-Z0-9\-]+)\[([^\]]+)\]\s*(.*)$', clean, re.IGNORECASE)
    if m2:
        word = m2.group(1).lower()
        phonetic = m2.group(2).strip()
        rest = m2.group(3).strip()
        pos, meaning = parse_scene_pos_meaning(rest)
        meaning = meaning.split('[')[0].strip()
        meaning = re.sub(r'[,，.。;；]+.*$', '', meaning).strip()
        if word and meaning and len(word) > 1:
            return {
                "word": word, "category": "IELTS_SCENE", "section": section_name,
                "subcategory": subcategory, "phonetic": phonetic, "part_of_speech": pos,
                "meaning_cn": meaning, "example_en": "", "example_cn": "",
                "source": "雅思场景超核心词汇4000.pdf", "difficulty": 2
            }

    # 格式3: word meaning（无音标）
    m3 = re.match(r'^([a-zA-Z][a-zA-Z0-9\-]+)\s+([一-鿿].+)$', clean, re.IGNORECASE)
    if m3:
        word = m3.group(1).lower()
        meaning = m3.group(2).strip()
        pos, meaning2 = parse_scene_pos_meaning(meaning)
        if meaning2:
            meaning = meaning2
        meaning = meaning.split('[')[0].strip()
        meaning = re.sub(r'[,，.。;；]+.*$', '', meaning).strip()
        if word and meaning and len(word) > 1:
            return {
                "word": word, "category": "IELTS_SCENE", "section": section_name,
                "subcategory": subcategory, "phonetic": "", "part_of_speech": pos or "n.",
                "meaning_cn": meaning, "example_en": "", "example_cn": "",
                "source": "雅思场景超核心词汇4000.pdf", "difficulty": 2
            }

    return None



def parse_scene_pos_meaning(text):
    """从文本中解析词性和中文释义"""
    if not text:
        return "", ""

    text = text.strip()
    pos_patterns = [
        (r'^(n\.|v\.|adj\.|adv\.|prep\.|conj\.|pron\.|int\.|num\.|det\.|vi\.|vt\.|a\.)', ['n.', 'v.', 'adj.', 'adv.', 'prep.', 'conj.', 'pron.', 'int.', 'num.', 'det.', 'vi.', 'vt.']),
    ]

    for pos in ['n.', 'v.', 'adj.', 'adv.', 'prep.', 'conj.', 'pron.', 'int.', 'num.', 'det.', 'vi.', 'vt.']:
        if text.startswith(pos):
            pos_str = pos
            meaning = text[len(pos):].strip()
            return pos_str, meaning

    return "", text


# ============================================================
# 3. 读取现有GRE词汇
# ============================================================

def read_existing_words():
    words = []
    csv_path = "data/words_master.csv"

    if not os.path.exists(csv_path):
        return words

    with open(csv_path, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            category = (row.get("category") or "").strip()
            if category == "GRE":
                words.append({
                    "word": (row.get("word") or "").strip(),
                    "category": "GRE",
                    "section": (row.get("section") or "GRE核心词").strip(),
                    "subcategory": (row.get("subcategory") or "").strip(),
                    "phonetic": (row.get("phonetic") or "").strip(),
                    "part_of_speech": (row.get("part_of_speech") or "").strip(),
                    "meaning_cn": (row.get("meaning_cn") or "").strip(),
                    "example_en": (row.get("example_en") or "").strip(),
                    "example_cn": (row.get("example_cn") or "").strip(),
                    "source": (row.get("source") or "").strip(),
                    "difficulty": int(row.get("difficulty") or 1),
                })

    return words


# ============================================================
# 4. 主函数
# ============================================================

def main():
    print("=" * 60)
    print("开始提取词库...")
    print("=" * 60)

    all_words = []

    print("\n[1] 读取现有GRE词汇...")
    gre_words = read_existing_words()
    print(f"  GRE词汇: {len(gre_words)} 个")
    all_words.extend(gre_words)

    print("\n[2] 从雅思词汇真经提取...")
    bible_words = extract_bible_words()
    print(f"  雅思词汇真经: {len(bible_words)} 个")
    all_words.extend(bible_words)

    print("\n[3] 从雅思场景词汇提取...")
    scene_words = extract_scene_words()
    print(f"  雅思场景词汇: {len(scene_words)} 个")
    all_words.extend(scene_words)

    print(f"\n[4] 去重合并...")
    seen = set()
    deduped = []
    for w in all_words:
        key = (w["word"].lower(), w["category"], w.get("section", ""), w.get("subcategory", ""))
        if key not in seen and w["word"]:
            seen.add(key)
            deduped.append(w)

    print(f"  去重后总计: {len(deduped)} 个词")

    print(f"\n[5] 写入 data/words_master.csv...")
    output_path = "data/words_master.csv"
    fieldnames = ["word", "category", "section", "subcategory", "phonetic",
                  "part_of_speech", "meaning_cn", "example_en", "example_cn",
                  "source", "difficulty"]

    with open(output_path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for w in deduped:
            writer.writerow(w)

    print(f"  写入完成: {output_path}")

    print("\n" + "=" * 60)
    print("词库统计")
    print("=" * 60)
    cats = {}
    for w in deduped:
        cats[w["category"]] = cats.get(w["category"], 0) + 1
    for cat, cnt in sorted(cats.items()):
        print(f"  {cat}: {cnt} 个")
    print(f"\n总计: {len(deduped)} 个单词")
    print("完成!")


if __name__ == "__main__":
    main()
