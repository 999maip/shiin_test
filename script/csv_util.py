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

def export_to_csv(prefix: str, scripts: dict, output_csv):
    writer = csv.writer(output_csv, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
    writer.writerow(['location', 'source', 'target', 'ID',
                     'fuzzy', 'context', 'translator_comments', 'developer_comments'])
    for script_id, script_data in scripts.items():
        txts = shiin.script_to_txts(prefix, script_id, script_data)
        if len(txts) == 0:
            continue
        for uid, txt in txts.items():
            writer.writerow(['', txt, '', '', '', uid, '', ''])

def export_main_script():
    fin = open('event_script.dat', 'rb')
    data = fin.read()
    fin.close()

    # all remaining scripts will be considered as chapter 6 contents.
    chapter_script_id_ranges = {
        'chapter1': [[16842753], [17039361, 17039389]],
        'chapter1_extra': [[17039561, 17039599]],
        'chapter2': [[16842754], [17039390, 17039414], [17039662]],
        'chapter3': [[16842755], [16973828, 16973830], [17039416, 17039439]],
        'chapter4': [[16842756], [17039440, 17039466], [17039761]],
        'chapter5': [[16842757], [17039467, 17039502]],
    }

    scripts = shiin.dat_to_scripts(data)
    used = dict()

    for chapter_id, script_id_ranges in chapter_script_id_ranges.items():
        chapter_scripts = dict()
        for script_id_range in script_id_ranges:
            if len(script_id_range) == 1:
                # single script
                chapter_scripts[script_id_range[0]] = scripts[script_id_range[0]]
                used[script_id_range[0]] = True
            else:
                # script range
                for script_id in range(script_id_range[0], script_id_range[1] + 1):
                    if script_id in scripts:
                        chapter_scripts[script_id] = scripts[script_id]
                        used[script_id] = True

        output_csv = open('output_csv/%s.csv' % chapter_id, 'w', encoding='utf8', newline='')
        export_to_csv('main', chapter_scripts, output_csv)
        output_csv.close()

    chapter6_scripts = dict()
    for script_id, script_data in scripts.items():
        if script_id not in used:
            chapter6_scripts[script_id] = script_data
    output_csv = open('output_csv/chapter6.csv', 'w', encoding='utf8', newline='')
    export_to_csv('main', chapter6_scripts, output_csv)
    output_csv.close()

def export_maze_script():
    fin = open('event_mazeevent.dat', 'rb')
    data = fin.read()
    fin.close()

    scripts = shiin.dat_to_scripts(data)

    output_csv = open('output_csv/maze.csv', 'w', encoding='utf8', newline='')
    export_to_csv('main', scripts, output_csv)
    output_csv.close()

def csvs_to_cn_txts(csv_data: list[str]):
    cn_txts = dict()
    for line in csv_data:
        line = line.strip()
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