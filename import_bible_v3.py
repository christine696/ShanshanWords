"""
雅思词汇真经（22章）全面导入脚本 v3
修复解析逻辑后重新实现
"""
import re, csv, os, sys
import pdfplumber
from collections import Counter

sys.stdout.reconfigure(encoding='utf-8')

# ========== 章节映射 ==========
CHAPTER_NAMES = {
    1: "自然地理", 2: "植物研究", 3: "动物保护", 4: "太空探索",
    5: "学校教育", 6: "文化历史", 7: "科技发明", 8: "娱乐运动",
    9: "语言演化", 10: "社会角色", 11: "时尚潮流", 12: "饮食健康",
    13: "建筑场所", 14: "交通旅行", 15: "国家政府", 16: "社会经济",
    17: "法律法规", 18: "征战沙场", 19: "社会关系", 20: "行为动作",
    21: "身心健康", 22: "时间日期",
}

LIST_TO_CHAPTER = {}
# Ch1: Lists 1-4
for l in range(1, 5): LIST_TO_CHAPTER[l] = 1
# Ch2: Lists 5-6
for l in range(5, 7): LIST_TO_CHAPTER[l] = 2
# Ch3: Lists 7-9
for l in range(7, 10): LIST_TO_CHAPTER[l] = 3
# Ch4: List 10
LIST_TO_CHAPTER[10] = 4
# Ch5: Lists 11-16
for l in range(11, 17): LIST_TO_CHAPTER[l] = 5
# Ch6-10 (推断): Lists 17-27
for l in range(17, 28): LIST_TO_CHAPTER[l] = l - 16  # maps to 1-11
# Ch11: Lists 28-29
for l in range(28, 30): LIST_TO_CHAPTER[l] = 11
# Ch12: Lists 30-32
for l in range(30, 33): LIST_TO_CHAPTER[l] = 12
# Ch13: Lists 33-35
for l in range(33, 36): LIST_TO_CHAPTER[l] = 13
# Ch14: Lists 36-37
for l in range(36, 38): LIST_TO_CHAPTER[l] = 14
# Ch15: Lists 38-40
for l in range(38, 41): LIST_TO_CHAPTER[l] = 15
# Ch16: Lists 41-43
for l in range(41, 44): LIST_TO_CHAPTER[l] = 16
# Ch17: Lists 44-45
for l in range(44, 46): LIST_TO_CHAPTER[l] = 17
# Ch18: Lists 46-49
for l in range(46, 50): LIST_TO_CHAPTER[l] = 18
# Ch19: List 50
LIST_TO_CHAPTER[50] = 19
# Ch20: Lists 51-56
for l in range(51, 57): LIST_TO_CHAPTER[l] = 20
# Ch21: Lists 57-61
for l in range(57, 62): LIST_TO_CHAPTER[l] = 21
# Ch22: Lists 62-63
for l in range(62, 64): LIST_TO_CHAPTER[l] = 22


def parse_page(line):
    """解析一行（一个List页中一条单词行），返回单词列表"""
    words = []
    # 找所有数字序号位置
    nums = [(m.start(), int(m.group())) for m in re.finditer(r'(?<!\d)\d{1,2}(?!\d)', line)]
    if len(nums) < 2:
        return words

    for i in range(len(nums) - 1):
        start, num = nums[i]
        end = nums[i + 1][0]
        seg = line[start:end].strip()
        seg2 = re.sub(r'^\d+\s*', '', seg).strip()

        # 提取单词
        wm = re.match(r"([a-zA-Z][a-zA-Z'-]{0,40})\b", seg2)
        if not wm:
            continue
        word = wm.group(1).rstrip("'-")
        after_word = seg2[wm.end():].lstrip()

        # 提取词性
        pos = ''
        meaning = after_word
        pm = re.match(r'([a-z]+)\.?\s*', after_word)
        if pm:
            pos = pm.group(1) + '.'
            meaning = after_word[pm.end():].strip()

        if not word or len(word) < 2:
            continue

        word = re.sub(r'~$', '', word).strip()
        meaning = re.sub(r'\s+', ' ', meaning).strip()

        if not meaning:
            continue

        words.append((word, pos, meaning))

    return words


def extract_bible():
    """从所有PDF提取单词"""
    all_words = []

    pdf_configs = [
        (r'D:\Desktop\雅思词汇真经\list1-10.pdf',    range(1, 11)),
        (r'D:\Desktop\雅思词汇真经\list11-16.pdf',   range(11, 17)),
        (r'D:\Desktop\雅思词汇真经\list28-37.pdf',  range(28, 38)),
        (r'D:\Desktop\雅思词汇真经\list38-47.pdf',  range(38, 48)),
        (r'D:\Desktop\雅思词汇真经\list48-56.pdf',  range(48, 57)),
        (r'D:\Desktop\雅思词汇真经\list57~63.pdf',  range(57, 64)),
    ]

    for pdf_path, list_range in pdf_configs:
        if not os.path.exists(pdf_path):
            continue
        with pdfplumber.open(pdf_path) as pdf:
            for page_idx, page in enumerate(pdf.pages):
                list_num = list_range.start + page_idx
                chapter_num = LIST_TO_CHAPTER.get(list_num)
                if not chapter_num:
                    continue
                chapter_name = CHAPTER_NAMES.get(chapter_num, f'第{chapter_num}章')
                section = f'Chapter {chapter_num} {chapter_name}'

                text = page.extract_text() or ''
                for line in text.split('\n'):
                    line = line.strip()
                    if not line or 'Chapter' in line[:15] or line.startswith('序') or 'Date' in line[:20]:
                        continue
                    words = parse_page(line)
                    for word, pos, meaning in words:
                        all_words.append({
                            'word': word,
                            'category': 'IELTS_BOOK',
                            'section': section,
                            'subcategory': chapter_name,
                            'phonetic': '',
                            'part_of_speech': pos,
                            'meaning_cn': meaning,
                            'example_en': '',
                            'example_cn': '',
                            'source': f'bible List{list_num}',
                            'difficulty': 1,
                        })

    return all_words


if __name__ == '__main__':
    print('开始提取...')
    words = extract_bible()
    print(f'共提取 {len(words)} 个单词')

    # 章节统计
    sections = Counter(w['section'] for w in words)
    for s, c in sorted(sections.items(), key=lambda x: x[0]):
        print(f'  {s}: {c}词')

    # 写入CSV
    csv_path = os.path.join('data', 'words_master.csv')
    with open(csv_path, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'word', 'category', 'section', 'subcategory',
            'phonetic', 'part_of_speech', 'meaning_cn',
            'example_en', 'example_cn', 'source', 'difficulty'
        ])
        writer.writeheader()
        writer.writerows(words)

    print(f'\n已写入: {csv_path}')