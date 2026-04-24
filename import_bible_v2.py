"""
雅思词汇真经（22章）全面导入脚本
合并6个PDF，按章节分类，处理缺失章节
"""
import re
import csv
import os
import pdfplumber

# ========== 章节映射（从PDF提取 + 补充） ==========
# 格式: chapter_num -> chapter_name
CHAPTER_NAMES = {
    1: "自然地理",
    2: "植物研究",
    3: "动物保护",
    4: "太空探索",
    5: "学校教育",
    # 6-10 缺失，从原始数据推断
    6: "文化历史",
    7: "科技发明",
    8: "娱乐运动",
    9: "语言演化",
    10: "社会角色",
    11: "时尚潮流",
    12: "饮食健康",
    13: "建筑场所",
    14: "交通旅行",
    15: "国家政府",
    16: "社会经济",
    17: "法律法规",
    18: "征战沙场",
    19: "社会关系",
    20: "行为动作",
    21: "身心健康",
    22: "时间日期",
}

# List范围 -> chapter_num
LIST_TO_CHAPTER = {
    1: 1, 2: 1, 3: 1, 4: 1,       # Chapter 1 自然地理
    5: 2, 6: 2,                   # Chapter 2 植物研究
    7: 3, 8: 3, 9: 3,            # Chapter 3 动物保护
    10: 4,                        # Chapter 4 太空探索
    11: 5, 12: 5, 13: 5, 14: 5, 15: 5, 16: 5,  # Chapter 5 学校教育
    17: 6, 18: 6, 19: 6, 20: 6, 21: 6,         # 推断: 文化历史
    22: 7, 23: 7, 24: 7, 25: 7, 26: 7, 27: 7,   # 推断: 科技发明
    28: 11, 29: 11,              # Chapter 11 时尚潮流
    30: 12, 31: 12, 32: 12,     # Chapter 12 饮食健康
    33: 13, 34: 13, 35: 13,     # Chapter 13 建筑场所
    36: 14, 37: 14,             # Chapter 14 交通旅行
    38: 15, 39: 15, 40: 15,     # Chapter 15 国家政府
    41: 16, 42: 16, 43: 16,     # Chapter 16 社会经济
    44: 17, 45: 17,             # Chapter 17 法律法规
    46: 18, 47: 18, 48: 18, 49: 18,  # Chapter 18 征战沙场
    50: 19,                     # Chapter 19 社会关系
    51: 20, 52: 20, 53: 20, 54: 20, 55: 20, 56: 20,  # Chapter 20 行为动作
    57: 21, 58: 21, 59: 21, 60: 21, 61: 21,  # Chapter 21 身心健康
    62: 22, 63: 22,             # Chapter 22 时间日期
}


def parse_bible_page(text):
    """解析雅思真经一页的内容，返回单词列表"""
    words = []
    lines = text.split('\n')

    for line in lines:
        line = line.strip()
        # 跳过标题行和非数据行
        if not line or line.startswith('Chapter') or line.startswith('序') or line.startswith('Date'):
            continue

        # 解析一行中的3个单词（格式: 序号 单词 词性 释义  序号 单词...）
        # 用正则匹配 "数字. 英文" 开头
        entries = re.findall(
            r'(?:^|\s)(\d+)\s+([a-zA-Z][^\d\s,，。/\\|]{0,40}?)\s*((?:n\.?|v\.?|adj\.?|adv\.?|conj\.?|prep\.?|pron\.?|interj\.?)\s*(?:\[\S+\])?)\s*([^\d\s][^\r\n]{0,120}?)(?=\s+\d+\.|$)',
            line + ' ', re.DOTALL
        )

        if not entries:
            continue

        for entry in entries:
            seq, word, pos, meaning = entry
            seq = seq.strip()
            word = word.strip()
            pos = pos.strip()
            meaning = meaning.strip()

            if not word or len(word) < 2:
                continue

            # 清理
            word = re.sub(r'~$', '', word)
            meaning = re.sub(r'\s+', ' ', meaning).strip(' .,;，、')

            words.append({
                'word': word,
                'phonetic': '',
                'part_of_speech': pos,
                'meaning_cn': meaning,
                'example_en': '',
                'example_cn': '',
            })

    return words


def parse_bible_page_v2(text):
    """更鲁棒的解析：一行分割为3个区域"""
    words = []
    lines = text.split('\n')

    for line in lines:
        line = line.strip()
        if not line:
            continue
        if line.startswith('Chapter') or line.startswith('序') or 'Date' in line[:20]:
            continue

        # 用3个数字位置把行分成3段
        # 行如: "1 atmosphere n. 大气层  21 destructive adj. 破坏  41 magma n. 岩浆"
        # 先找到所有 "数字." 的位置
        pos_matches = [(m.start(), m.group()) for m in re.finditer(r'\b\d+\.', line)]
        if len(pos_matches) < 3:
            continue

        # 取前3个数字位置
        positions = [p[0] for p in pos_matches[:3]]
        segments = []
        for i, start in enumerate(positions):
            end = positions[i+1] if i+1 < len(positions) else len(line)
            segments.append(line[start:end].strip())

        for seg in segments:
            seg = seg.strip()
            if not seg:
                continue
            # 第一个单词
            m = re.match(r'\d+\.\s*([a-zA-Z][^\s]{0,50})(?:\s+((?:n|v|adj|adv|conj|prep|pron|interj)\.?(?:\[\S+\])?)\s*)?(.*)', seg)
            if not m:
                continue
            word = m.group(1).strip()
            pos = (m.group(2) or '').strip()
            meaning = (m.group(3) or '').strip()

            if not word or len(word) < 2:
                continue

            word = re.sub(r'~$', '', word)
            meaning = re.sub(r'\s+', ' ', meaning).strip(' .,;，、')

            if meaning:
                words.append({
                    'word': word,
                    'phonetic': '',
                    'part_of_speech': pos,
                    'meaning_cn': meaning,
                    'example_en': '',
                    'example_cn': '',
                })

    return words


def parse_bible_page_v3(text):
    """最稳健的解析：按3个数字分组"""
    words = []
    lines = text.split('\n')

    for line in lines:
        line = line.strip()
        if not line:
            continue
        if 'Chapter' in line[:10] or 'Date' in line[:20] or line.startswith('序'):
            continue

        # 找到所有 "\d+." 位置
        nums = [(m.start(), int(m.group()[:-1])) for m in re.finditer(r'\b\d+\.', line)]
        if len(nums) < 2:
            continue

        for i in range(len(nums) - 1):
            num, start = nums[i]
            end = nums[i+1][0]
            seg = line[start:end].strip()

            # 解析 [序号] 英文 词性 释义
            m = re.match(
                r'\d+\.\s*'          # 序号+点
                r'([a-zA-Z][^\s,，。/\\]{0,50})'  # 单词
                r'(?:\s+((?:n|v|adj|adv|conj|prep|pron|interj)\.?(?:\[\S+\])?))?'  # 词性
                r'\s+(.*)',           # 释义
                seg, re.DOTALL
            )
            if not m:
                continue

            word = m.group(1).strip()
            pos = (m.group(2) or '').strip()
            meaning = (m.group(3) or '').strip()

            if not word or len(word) < 2:
                continue

            word = re.sub(r'~$', '', word)
            meaning = re.sub(r'\s+', ' ', meaning).strip()

            if meaning and len(meaning) > 0:
                words.append({
                    'word': word,
                    'phonetic': '',
                    'part_of_speech': pos,
                    'meaning_cn': meaning,
                    'example_en': '',
                    'example_cn': '',
                })

    return words


def extract_bible_words():
    """从所有PDF提取单词"""
    all_words = []

    pdf_configs = [
        (r'D:\Desktop\雅思词汇真经\list1-10.pdf', range(1, 11)),
        (r'D:\Desktop\雅思词汇真经\list11-16.pdf', range(11, 17)),
        (r'D:\Desktop\雅思词汇真经\list28-37.pdf', range(28, 38)),
        (r'D:\Desktop\雅思词汇真经\list38-47.pdf', range(38, 48)),
        (r'D:\Desktop\雅思词汇真经\list48-56.pdf', range(48, 57)),
        (r'D:\Desktop\雅思词汇真经\list57~63.pdf', range(57, 64)),
    ]

    for pdf_path, list_range in pdf_configs:
        if not os.path.exists(pdf_path):
            print(f'[WARN] PDF不存在: {pdf_path}')
            continue

        print(f'处理: {os.path.basename(pdf_path)}')
        with pdfplumber.open(pdf_path) as pdf:
            for page_idx, page in enumerate(pdf.pages):
                list_num = list_range.start + page_idx
                chapter_num = LIST_TO_CHAPTER.get(list_num)
                if chapter_num is None:
                    continue

                chapter_name = CHAPTER_NAMES.get(chapter_num, f'第{chapter_num}章')
                section_name = f'Chapter {chapter_num} {chapter_name}'

                text = page.extract_text() or ''
                words = parse_bible_page_v3(text)

                for w in words:
                    w['category'] = 'IELTS_BOOK'
                    w['section'] = section_name
                    w['subcategory'] = chapter_name
                    w['source'] = f'bible List{list_num}'
                    w['difficulty'] = 1

                print(f'  List {list_num} (Chapter {chapter_num} {chapter_name}): {len(words)} 词')
                all_words.extend(words)

    return all_words


def build_csv(bible_words):
    """构建完整CSV"""
    csv_path = os.path.join('data', 'words_master.csv')

    with open(csv_path, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'word', 'category', 'section', 'subcategory',
            'phonetic', 'part_of_speech', 'meaning_cn',
            'example_en', 'example_cn', 'source', 'difficulty'
        ])
        writer.writeheader()

        for w in bible_words:
            writer.writerow(w)

    print(f'\n写入 CSV: {csv_path}')
    return csv_path


if __name__ == '__main__':
    print('开始提取雅思词汇真经...')
    words = extract_bible_words()
    print(f'\n共提取 {len(words)} 个单词（仅含新PDF数据）')
    build_csv(words)

    # 统计各章词数
    from collections import Counter
    sections = Counter(w['section'] for w in words)
    print('\n各章节词数:')
    for s, c in sorted(sections.items(), key=lambda x: x[0]):
        print(f'  {s}: {c}')