from PIL import Image, ImageFont, ImageDraw
import font_util
import csv_util
import patch_util
import gamefile_util
import argparse
import sys

# reimport localized txts to .dat file
def reimport_dat_with_cn_txts(jp_dat, cn_txts: dict):
    jp_scripts = gamefile_util.dat_to_scripts(jp_dat)
    cn_scripts = dict()
    for script_id, jp_script in jp_scripts.items():
        if script_id not in cn_txts:
            cn_script = jp_script
        else:
            cn_script = reimport_script_with_cn_txts(jp_script, cn_txts[script_id])
        cn_scripts[script_id] = cn_script
    return gamefile_util.scripts_to_dat(cn_scripts)

# reimport localized texts to script data
# NOTE: Do not call this function directly. Call reimport_dat_with_cn_txts() instead.
def reimport_script_with_cn_txts(jp_script, cn_txts: dict) -> bytearray:
    cn_script = bytearray()
    offset = 0
    while offset < len(jp_script):
        line_id = int.from_bytes(jp_script[offset:offset+4], 'little')
        jp_size = int.from_bytes(jp_script[offset+4:offset+8], 'little')
        cn_script.extend(jp_script[offset:offset+4])

        if line_id in cn_txts:
            txt_encoded = font_util.txt_to_mapped_txt(cn_txts[line_id]).encode('sjis')
            cn_size = len(txt_encoded)
            size_after_padding = (cn_size + 4) // 4 * 4
            cn_script.extend(size_after_padding.to_bytes(4, 'little'))
            cn_script.extend(txt_encoded)
            if size_after_padding - cn_size != 0:
                cn_script.extend(bytearray(size_after_padding - cn_size))
        else:
            cn_script.extend(jp_script[offset+4:offset+8+jp_size])
        
        offset = offset + 8 + jp_size
    return cn_script

def export_main_script():
    with open('event_script.dat', 'rb') as fin:
        data = fin.read()

    # all remaining scripts will be considered as chapter 6 contents.
    chapter_script_id_ranges = {
        'chapter1': [[16842753], [17039361, 17039389]],
        'chapter1_extra': [[17039561, 17039599]],
        'chapter2': [[16842754], [17039390, 17039414], [17039662]],
        'chapter3': [[16842755], [16973828, 16973830], [17039416, 17039439]],
        'chapter4': [[16842756], [17039440, 17039466], [17039761]],
        'chapter5': [[16842757], [17039467, 17039502]],
    }

    scripts = gamefile_util.dat_to_scripts(data)
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

        txts = dict()
        for script_id, script_data in scripts.items():
            txts = txts | gamefile_util.script_to_txts('main', script_id, script_data)
        if len(txts) == 0:
            continue
        with open('output_csv/%s.csv' % chapter_id, 'w', encoding='utf8', newline='') as output_csv:
            csv_util.export_txts_to_csvfile(txts, output_csv)

    chapter6_scripts = dict()
    for script_id, script_data in scripts.items():
        if script_id not in used:
            chapter6_scripts[script_id] = script_data
    txts = dict()
    for script_id, script_data in chapter6_scripts.items():
        txts = txts | gamefile_util.script_to_txts('main', script_id, script_data)
    if len(txts) == 0:
        return
    with open('output_csv/chapter6.csv', 'w', encoding='utf8', newline='') as output_csv:
        csv_util.export_txts_to_csvfile('main', chapter6_scripts, output_csv)

def export_maze_script():
    fin = open('event_mazeevent.dat', 'rb')
    data = fin.read()
    fin.close()

    scripts = gamefile_util.dat_to_scripts(data)
    txts = dict()
    for script_id, script_data in scripts.items():
        txts = txts | gamefile_util.script_to_txts('maze', script_id, script_data)
    with open('output_csv/maze.csv', 'w', encoding='utf8', newline='') as output_csv:
        csv_util.export_txts_to_csvfile(scripts, output_csv)

def reimport_main_script():
    csv_file_list = ['chapter1_cn.csv', 'chapter2_cn.csv', 'chapter3_cn.csv',
                     'chapter4_cn.csv', 'chapter5_cn.csv', 'chapter6_cn.csv',
                     'chapter1_extra.csv']
    csv_data = []

    input_dir = 'text'
    for csv_file in csv_file_list:
        try:
            fin = open(input_dir + '/' + csv_file, 'r', encoding='utf8')
            print(input_dir + '/' + csv_file)
            # ignore header
            fin.readline()
            csv_data.extend(fin.readlines())
            fin.close()
        except Exception:
            print('Warning: file %s not exists.' % csv_file)
            continue
    cn_txts = csv_util.csvs_to_cn_txts(csv_data)
    fin = open('event_script.dat', 'rb')
    jp_dat = fin.read()
    fin.close()
    cn_dat = reimport_dat_with_cn_txts(jp_dat, cn_txts)
    output_dir = 'output_dat'
    fout = open(output_dir + '/' + 'event_script_cn.dat', 'wb')
    fout.write(cn_dat)
    fout.close()

def replace_title_example():
    # replace title example
    with open('texture_test/graphic_title.exg', 'rb') as old_exg_file:
        old_title_exg = old_exg_file.read()
    with open('texture_test/graphic_title_cn.png', 'rb') as png_file:
        title_png = png_file.read()
    with open('texture_test/graphic_title_cn.exg', 'wb') as exg_file:
        exg_file.write(gamefile_util.png_to_exg(title_png, old_title_exg))

def export_datpack_sample():
    # table_tablepack script processing sample
    fin = open('table_tablepack.dat', 'rb')
    data = fin.read()
    fin.close()
    scripts = gamefile_util.datpack_to_scripts(data)
    for script_id, data in scripts.items():
        fout = open('output_tablepack/%d.dat' % script_id, 'wb')
        # for uid, txt in script_to_txts('tablepack', script_id, data).items():
            #fout.write(uid + ',' + txt + '\n')
        fout.write(data)
        fout.close()

# generate patch
def gen_patch():
    print('start generating patch files...')
    filepaths = ['resource/graphic_title_exg.zip', 'resource/event_script.dat', 'resource/fontdata_fontdata01.exp']
    filenames_short = ['title', 'script', 'font']
    patch_util.generate_patch(filepaths, filenames_short)
    print('generating patch files finished')

def main():
    parser = argparse.ArgumentParser(description='This file is the main script for the shiin localization \
                                     project.\n You SHOULD always execute this script and DON\'T execute \
                                     other scripts directly \
                                     unless you understand what you are doing.')
    parser.add_argument('--export_dat', dest='export', action='store', choices=['all', 'main', 'maze'], help='export .dat to csv files. \
                        Use "all" to export all necessary .dat files.')
    parser.add_argument('--gen_patch', dest='patch', action='store_true', help='generate patch files.')
    parser.add_argument('--reimport', dest='reimport', action='store', choices=['all', 'main', 'maze'], help='reimport localizaed \
                        files  patch files. Use "all" to export all necessary .dat files.')
    args = parser.parse_args()
    if len(sys.argv) == 1:
        parser.print_help()
        return
    if args.export:
        if args.export == 'all':
            print('export all')
    elif args.patch:
        gen_patch()
    elif args.reimport:
        if args.reimport == 'all':
            print('function "reimport all" has not been implemented yet. Please use main instead.')
        elif args.reimport == 'main':
            print('reimport main')
        elif args.reimport == 'maze':
            print('function "reimport maze" has not been implemented yet. Please use main instead.')
    # gen_patch()
    # gen_cn_dat()
    # replace_title_example()


if __name__ == '__main__':
    main()