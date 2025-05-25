import csv
import common_util 
import io

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

def load_csv_file(filepath) -> list[list[str]]:
    with open(filepath, 'r', encoding='utf8') as file:
        csv_reader = csv.reader(file)
        data_list = list(csv_reader)[1:]
        return data_list


def exe_csv_to_cn_txts(csv_data:list[str]):
    cn_txts = dict()
    csv_data_str = '' . join(csv_data)
    csv_data_file_like = io.StringIO(csv_data_str)
    csv_reader = csv.reader(csv_data_file_like)
    line_number = 1
    for row in csv_reader:
        cn_txts[common_util.uid('exe', common_util.SCRIPT_ID_BASE, line_number)] = row[2]
        line_number = line_number + 1
    
    return cn_txts


def csvs_to_cn_txts(csv_data: list[str]):
    cn_txts = dict()
    csv_data_str = '' . join(csv_data)
    csv_data_file_like = io.StringIO(csv_data_str)
    csv_reader = csv.reader(csv_data_file_like)
    for row in csv_reader:
        line_cn_txt = row[2]
        global_line_id = row[5]
        if not global_line_id or global_line_id == '':
            continue
        prefix, script_id, line_id = common_util.split_uid(global_line_id)
        if script_id not in cn_txts:
            cn_txts[script_id] = dict()
        cn_txts[script_id][line_id] = line_cn_txt
    return cn_txts

def main():
    csv_file_list = ['chapter1_cn.csv', 'chapter2_cn.csv', 'chapter3_cn.csv',
                     'chapter4_cn.csv', 'chapter5_cn.csv', 'chapter6_cn.csv',
                     'chapter1_extra.csv']
    csv_data = []

    in_dir = 'text'

    for csv_file in csv_file_list:
        try:
            fin = open(in_dir + '/' + csv_file, 'r', encoding='utf8')
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