from PIL import Image, ImageFont, ImageDraw
import font_util
import csv_util
import patch_util
import gamefile_util
import common_util 
import argparse
import sys
import os
from config import *
from zipfile import ZipFile
import zipfile

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
    with open(GAME_RESOURCE_DIR + '/' + 'event_script.dat', 'rb') as fin:
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
        with open(OUTPUT_DIR + '/%s.csv' % chapter_id, 'w', encoding='utf8', newline='') as output_csv:
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
    with open(OUTPUT_DIR + '/chapter6.csv', 'w', encoding='utf8', newline='') as output_csv:
        csv_util.export_txts_to_csvfile(txts, output_csv)

def export_maze_script():
    with open(GAME_RESOURCE_DIR + '/event_mazeevent.dat', 'rb') as fin:
        data = fin.read()

    scripts = gamefile_util.dat_to_scripts(data)
    txts = dict()
    for script_id, script_data in scripts.items():
        txts = txts | gamefile_util.script_to_txts('maze', script_id, script_data)
    with open(OUTPUT_DIR + '/maze.csv', 'w', encoding='utf8', newline='') as output_csv:
        csv_util.export_txts_to_csvfile(txts, output_csv)

def reimport_main_script():
    csv_data = []
    for csv_file in CSV_FILE_LIST:
        try:
            fin = open(TEXT_DIR + '/' + csv_file, 'r', encoding='utf8')
            print(TEXT_DIR + '/' + csv_file)
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
    fout = open(OUTPUT_DIR + '/' + 'event_script_cn.dat', 'wb')
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

def export_item_txt():
    with open('output_tablepack/4.dat', 'rb') as item_file:
        items_data = item_file.read()
    line_number = 1
    txts = dict()
    offset = 0
    # item block data structure:
    # total size: 0x170
    # 0x00: item_name
    # 0x1A: item_description
    while offset < len(items_data):
        inner_offset = 0
        while offset < len(items_data) and inner_offset < 0x1A and items_data[offset+inner_offset] != 0x00:
            inner_offset = inner_offset + 1
        item_name = items_data[offset:offset+inner_offset].decode('shift-jis')
        txts[common_util.uid('item', common_util.SCRIPT_ID_BASE, line_number)] = item_name
        line_number = line_number + 1
        inner_offset = 0x1A
        while offset < len(items_data) and inner_offset < 0x170 and items_data[offset+inner_offset] != 0x00:
            inner_offset = inner_offset + 1
        item_description = items_data[offset+0x1A:offset+inner_offset].decode('shift-jis')
        txts[common_util.uid('item', common_util.SCRIPT_ID_BASE, line_number)] = item_description
        line_number = line_number + 1
        offset = offset + 0x170
    with open(OUTPUT_DIR + '/%s.csv' % 'item', 'w', encoding='utf8', newline='') as output_csv:
        csv_util.export_txts_to_csvfile(txts, output_csv)

def export_battle_txt():
    with open('output_tablepack/11.dat', 'rb') as battle_file:
        battle_data = battle_file.read()
    line_number = 1
    txts = dict()
    offset = 0
    # battle action block data structure:
    # total size: 0x64
    # 0x00-0x03: unknown
    # 0x04-0x07: action id
    # 0x08-0x0b: unknown
    # 0x0c: action name
    # 0x24: action description
    while offset < len(battle_data):
        inner_offset = 0x04
        action_id = int.from_bytes(battle_data[offset+inner_offset:offset+inner_offset+4], 'little')
        inner_offset = 0x0c
        while offset < len(battle_data) and inner_offset < 0x24 and battle_data[offset+inner_offset] != 0x00:
            inner_offset = inner_offset + 1
        action_name = battle_data[offset+0x0c:offset+inner_offset].decode('shift-jis')
        txts[common_util.uid('battle', common_util.SCRIPT_ID_BASE, line_number)] = action_name 
        line_number = line_number + 1
        inner_offset = 0x24
        while offset < len(battle_data) and inner_offset < 0x64 and battle_data[offset+inner_offset] != 0x00:
            inner_offset = inner_offset + 1
        action_description = battle_data[offset+0x24:offset+inner_offset].decode('shift-jis')
        txts[common_util.uid('battle', common_util.SCRIPT_ID_BASE, line_number)] = action_description 
        line_number = line_number + 1
        offset = offset + 0x64
    with open(OUTPUT_DIR + '/%s.csv' % 'battle', 'w', encoding='utf8', newline='') as output_csv:
        csv_util.export_txts_to_csvfile(txts, output_csv)

def export_battle_comb_txt():
    with open('output_tablepack/12.dat', 'rb') as battle_file:
        battle_data = battle_file.read()
    line_number = 1
    txts = dict()
    offset = 0x48
    # battle comb-action block data structure:
    # total size: 0x48
    # 0x00-0x07: unknown
    # 0x08: action description
    while offset < len(battle_data):
        inner_offset = 0x08
        while offset < len(battle_data) and inner_offset < 0x48 and battle_data[offset+inner_offset] != 0x00:
            inner_offset = inner_offset + 1
        action_name = battle_data[offset+0x08:offset+inner_offset].decode('shift-jis')
        txts[common_util.uid('battle_comb', common_util.SCRIPT_ID_BASE, line_number)] = action_name 
        line_number = line_number + 1
        offset = offset + 0x48
    with open(OUTPUT_DIR + '/%s.csv' % 'battle_comb', 'w', encoding='utf8', newline='') as output_csv:
        csv_util.export_txts_to_csvfile(txts, output_csv)

def export_datpack_sample_1():
    # table_tablepack script processing sample
    fin = open(GAME_RESOURCE_DIR + '/map_mapdatpack.dat', 'rb')
    data = fin.read()
    fin.close()
    scripts = gamefile_util.datpack_to_scripts(data)
    for script_id, data in scripts.items():
        fout = open('output_mappack/%d.dat' % script_id, 'wb')
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

def export_ui_dds():
    # These offsets(and real filenames) are actually stored in the file named 'ui.hed'.
    # Since the offsets can be easily recognized by the dds magic number 'DDS', we don't bother loading the ui.hed file.
    offsets = [0, 0x1FE080, 0x3FC100, 0x5F6580, 0x7f0A00, 0x9EAE80, 0xbe5300, 0x4be5380, 0x8be5400,
               0x9be5480,0xabe5500,0xafe5580,0xb3e5600,
               0xd3e5680,0xf3e5700,0xf485780,0xf4dd640,0xf51d6c0,0xf525740,0xf52d7c0, 0xf92d841]
    idx = 0
    with open(GAME_RESOURCE_DIR + '/ui.dat', 'rb') as f_ui:
        while idx + 1 < len(offsets):
            dds = f_ui.read(offsets[idx+1] - offsets[idx])
            fout = open(OUTPUT_DIR + '/%d.dds' % idx, 'wb')
            fout.write(dds)
            fout.close()
            idx = idx + 1

def export_battle_txt_in_exe():
    with open(GAME_RESOURCE_DIR + '/Death Mark.exe', 'rb') as exe:
        exe_data = exe.read()
    line_number = 1
    txts = dict()
    offset = 0x314E04
    MSG_TABLE_END = 0x315E5A
    # exe battle text block data structure:
    # 0-ending strings
    while offset < MSG_TABLE_END:
        if exe_data[offset] == 0x00:
            offset = offset + 1
            continue
        inner_offset = 0x00
        while exe_data[offset+inner_offset] != 0x00:
            inner_offset = inner_offset + 1
        exe_txt = exe_data[offset:offset+inner_offset].decode('shift-jis')
        txts[common_util.uid('exe', common_util.SCRIPT_ID_BASE, line_number)] = exe_txt
        line_number = line_number + 1
        offset = offset + inner_offset

    with open(OUTPUT_DIR + '/%s.csv' % 'exe_cn', 'w', encoding='utf8', newline='') as output_csv:
        csv_util.export_txts_to_csvfile(txts, output_csv)

def gen_cn_font():
    # generate a character table for needed characters
    print('start generating character table using translation files...')
    font_util.gen_char_table(CSV_FILE_LIST)
    print('generating character table finished')

    # map characters into valid shift-jis encodings
    print('start generating character mapping...')
    font_util.gen_char_mapping()
    print('generating character mapping finished')
    
    print('start generating cn font file...')
    fin = open(GAME_RESOURCE_DIR + '/fontdata_fontdata01.exp', 'rb')
    jp_font_data = fin.read()
    cn_font_data = font_util.reimport_font_data(jp_font_data)
    with open(OUTPUT_DIR + '/fontdata_fontdata01_cn.exp', 'wb') as fout:
        fout.write(cn_font_data)
    print('generating cn font file finished.')
    print('All jobs done!')

def parse_args():
    parser = argparse.ArgumentParser(description='This file is the main script for the shiin localization \
                                     project.\n You SHOULD always execute this script and DON\'T execute \
                                     other scripts directly \
                                     unless you understand what you are doing. Make sure you have configured the \
                                     configuration variables defined in the config.py file.')
    parser.add_argument('--export_dat', dest='export_script', action='store', choices=['all', 'main', 'maze'], help='export .dat to csv files. \
                        Use "all" to export all necessary .dat files.')
    parser.add_argument('--export_ui', dest='export_ui', action='store_true', help='export ui.dat to dds files.')
    parser.add_argument('--gen_patch', dest='patch', action='store_true', help='generate patch files.')
    parser.add_argument('--reimport', dest='reimport', action='store', choices=['all', 'main', 'maze'], help='reimport localized \
                        files patch files. Use "all" to export all necessary .dat files.')
    parser.add_argument('--gen_font', dest='font', action='store_true', help='generate the main font \
                        file for Chinese characters.')
    args = parser.parse_args()
    if len(sys.argv) == 1:
        parser.print_help()
        return
    if args.export_script:
        if args.export_script == 'all':
            print('export all')
    if args.export_ui:
        export_ui_dds()
    elif args.patch:
        gen_patch()
    elif args.font:
        gen_cn_font()
    elif args.reimport:
        if args.reimport == 'all':
            print('function "reimport all" has not been implemented yet. Please use main instead.')
        elif args.reimport == 'main':
            reimport_main_script()
        elif args.reimport == 'maze':
            print('function "reimport maze" has not been implemented yet. Please use main instead.')


def main():
    pass
    # export_main_script()
    # export_maze_script()
    # parse_args()
    # export_datpack_sample()
    # export_item_txt()
    # export_battle_txt()
    # export_battle_txt_in_exe()
    # export_battle_comb_txt()

if __name__ == '__main__':
    main()