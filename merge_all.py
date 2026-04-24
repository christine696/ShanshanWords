"""
合并三个词库：IELTS_BOOK(22章) + IELTS_SCENE(4篇) + GRE
"""
import csv, sqlite3, sys
sys.stdout.reconfigure(encoding='utf-8')

FIELDS = ['word','category','section','subcategory','phonetic','part_of_speech',
          'meaning_cn','example_en','example_cn','source','difficulty']

conn = sqlite3.connect('words.db')
cur = conn.cursor()

# 读取GRE和SCENE完整数据（带section/subcategory）
cur.execute("SELECT word,category,section,subcategory,phonetic,part_of_speech,meaning_cn,example_en,example_cn,source,difficulty FROM words WHERE category IN ('GRE','IELTS_SCENE')")
existing = [dict(zip(FIELDS, r)) for r in cur.fetchall()]
conn.close()

# 读取新生成的IELTS_BOOK
new_words = []
with open('data/words_master.csv', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    for row in reader:
        new_words.append(row)

# 合并（IELTS_BOOK只含新数据，需要带上section/subcategory字段）
all_words = existing + new_words
print(f'合并后总计: {len(all_words)} 词 (GRE/SCENE={len(existing)} + IELTS_BOOK={len(new_words)})')

# 写入新CSV
with open('data/words_master.csv', 'w', encoding='utf-8-sig', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=FIELDS)
    writer.writeheader()
    writer.writerows(all_words)

print('已写入: data/words_master.csv')