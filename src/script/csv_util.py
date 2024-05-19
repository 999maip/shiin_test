import csv
import common_util 

ranges = [
  {"from": ord(u"\u3300"), "to": ord(u"\u33ff")},         # compatibility ideographs
  {"from": ord(u"\ufe30"), "to": ord(u"\ufe4f")},         # compatibility ideographs
  {"from": ord(u"\uf900"), "to": ord(u"\ufaff")},         # compatibility ideographs
  {"from": ord(u"\U0002F800"), "to": ord(u"\U0002fa1f")}, # compatibility ideographs
  {'from': ord(u'\u3040'), 'to': ord(u'\u309f')},         # Japanese Hiragana
  {"from": ord(u"\u30a0"), "to": ord(u"\u30ff")},         # Japanese Katakana
  {"from": ord(u"\u2e80"), "to": ord(u"\u2eff")},         # cjk radicals supplement
  {"from": ord(u"\u4e00"), "to": ord(u"\u9fff")},
  {"from": ord(u"\u3400"), "to": ord(u"\u4dbf")},
  {"from": ord(u"\U00020000"), "to": ord(u"\U0002a6df")},
  {"from": ord(u"\U0002a700"), "to": ord(u"\U0002b73f")},
  {"from": ord(u"\U0002b740"), "to": ord(u"\U0002b81f")},
  {"from": ord(u"\U0002b820"), "to": ord(u"\U0002ceaf")},  # included as of Unicode 8.0
  {"from": ord(u"\uff10"), "to": ord(u"\uff19")},
  {"from": ord(u"\uff21"), "to": ord(u"\uff3a")},
  {"from": ord(u"\uff41"), "to": ord(u"\uff5a")},
  {"from": ord(u"\u300c"), "to": ord(u"\u300d")}
]

def is_cjk(char):
  return any([range["from"] <= ord(char) <= range["to"] for range in ranges])

def exist_cjk(l):
    for i in l:
        if is_cjk(i): 
            return True
    return False

def remove_ln(l):
    if l[-1] == '\n':
        return l[:-1]
    else:
        return l

def export_txts_to_csvfile(txts: dict, csvfile):
    writer = csv.writer(csvfile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
    writer.writerow(['location', 'source', 'target', 'ID',
                     'fuzzy', 'context', 'translator_comments', 'developer_comments'])
    for uid, txt in txts.items():
        writer.writerow(['', txt, '', '', '', uid, '', ''])

def csvs_to_cn_txts(csv_data: list[str]):
    cn_txts = dict()
    for line in csv_data:
        line = line.strip()
        if len(line) == 0:
            continue
        line_data = line.split(',')
        line_cn_txt = line_data[2]
        global_line_id = line_data[5]
        prefix, script_id, line_id = common_util.split_uid(global_line_id)
        if script_id not in cn_txts:
            cn_txts[script_id] = dict()
        cn_txts[script_id][line_id] = line_cn_txt
    return cn_txts

def main():
    csv_file_list = ['chapter1.csv', 'chapter2.csv', 'chapter3.csv',
                     'chapter4.csv', 'chapter5.csv', 'chapter6.csv',
                     'chapter1_extra.csv']
    csv_data = []

    for csv_file in csv_file_list:
        try:
            fin = open(csv_file, 'r', encoding='utf8')
            # ignore header
            fin.readline()
            csv_data.extend(fin.readlines())
            fin.close()
        except Exception:
            print('Warning: file %s not exists.' % csv_file)
            continue
    cn_txts = csvs_to_cn_txts(csv_data)
    # export_main_script()
    # export_maze_script()

if __name__ == '__main__':
    main()