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
import example

# reimport localized txts to .dat file
def reimport_dat_with_cn_txts(jp_dat, cn_txts: dict):
    jp_scripts = gamefile_util.dat_to_scripts(jp_dat)
    cn_scripts = dict()

    char_mapping = font_util.load_char_mapping()

    for script_id, jp_script in jp_scripts.items():
        if script_id not in cn_txts:
            cn_script = jp_script
        else:
            cn_script = reimport_script_with_cn_txts(script_id, jp_script, cn_txts[script_id], char_mapping)
        cn_scripts[script_id] = cn_script
    return gamefile_util.scripts_to_dat(cn_scripts)

# reimport localized texts to script data
# NOTE: Do not call this function directly. Call reimport_dat_with_cn_txts() instead.
# param[in] jp_script the japanese script file binary data
def reimport_script_with_cn_txts(script_id: int, jp_script, cn_txts: dict, char_mapping) -> bytearray:
    cn_script = bytearray()
    offset = 0
    while offset < len(jp_script):
        line_id = int.from_bytes(jp_script[offset:offset+4], 'little')
        jp_size = int.from_bytes(jp_script[offset+4:offset+8], 'little')
        cn_script.extend(jp_script[offset:offset+4])

        if line_id in cn_txts:
            txt_encoded = font_util.txt_to_mapped_txt(cn_txts[line_id], char_mapping).encode('sjis')
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
    with open(os.path.join(GAME_RESOURCE_DIR, 'event_mazeevent.dat'), 'rb') as fin:
        data = fin.read()

    scripts = gamefile_util.dat_to_scripts(data)
    txts = dict()
    for script_id, script_data in scripts.items():
        txts = txts | gamefile_util.script_to_txts('maze', script_id, script_data)
    with open(os.path.join(OUTPUT_DIR, 'maze.csv'), 'w', encoding='utf8', newline='') as output_csv:
        csv_util.export_txts_to_csvfile(txts, output_csv)

def reimport_maze_script():
    csv_data = []
    try:
        with open(os.path.join(TEXT_DIR, 'maze_cn.csv',), 'r', encoding='utf8') as fin:
            # ignore header
            fin.readline()

            csv_data.extend(fin.readlines())
    except Exception as e:
        print('Warning: file maze_cn.csv not exists.')
        raise e
    cn_txts = csv_util.csvs_to_cn_txts(csv_data)
    with open(os.path.join(GAME_RESOURCE_DIR, 'event_mazeevent.dat'), 'rb') as fin:
        jp_dat = fin.read()
    cn_dat = reimport_dat_with_cn_txts(jp_dat, cn_txts)

    output_path = os.path.join(OUTPUT_DIR, 'event_mazeevent_cn.dat')
    with open(output_path, 'wb') as fout:
        fout.write(cn_dat)

    print(f'Reimporting maze script completed. The main script file is generated at {output_path}.')

def reimport_main_script():
    csv_data = []
    for csv_file in MAIN_CSV_FILE_LIST:
        try:
            print(f'Loading {csv_file}...')
            with open(os.path.join(TEXT_DIR, csv_file), 'r', encoding='utf8') as fin:
                # ignore header
                fin.readline()
                lines = fin.readlines()
                # we add an extra line separator if the last line doesn't end with one
                if not lines[-1].endswith(os.linesep):
                    lines[-1] = lines[-1] + os.linesep
                csv_data.extend(lines)
        except Exception:
            print('Warning: file %s not exists.' % csv_file)
            continue
    print('File loading Compelete.')
    cn_txts = csv_util.csvs_to_cn_txts(csv_data)
    with open(os.path.join(GAME_RESOURCE_DIR, 'event_script.dat'), 'rb') as fin:
        jp_dat = fin.read()
    cn_dat = reimport_dat_with_cn_txts(jp_dat, cn_txts)

    output_path = os.path.join(OUTPUT_DIR, 'event_script_cn.dat')
    with open(output_path, 'wb') as fout:
        fout.write(cn_dat)

    print(f'Reimporting main script completed. The main script file is generated at {output_path}.')

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
    with open(os.path.join(OUTPUT_DIR, 'item.csv'), 'w', encoding='utf8', newline='') as output_csv:
        csv_util.export_txts_to_csvfile(txts, output_csv)

def export_map_txt():
    with open(os.path.join(OUTPUT_DIR, 'map.csv'), 'w', encoding='utf8', newline='') as output_csv:
        txts = dict()
        for file_index in range(16):
            with open(os.path.join('output_mappack', f'{file_index}.dat'), 'rb') as map_file:
                map_data = map_file.read()
            line_number = 1
            offset = 0xAAA0
            # map data structure:
            # text offset: 0xAAA0
            # 0-terminated strings
            while offset < len(map_data):
                inner_offset = 0
                while offset < len(map_data) and map_data[offset+inner_offset] != 0x00:
                    inner_offset = inner_offset + 1
                if inner_offset != 0:
                    map_txt = map_data[offset:offset+inner_offset].decode('shift-jis')
                    txts[common_util.uid('map', common_util.SCRIPT_ID_BASE + file_index, line_number)] = map_txt
                    line_number = line_number + 1
                offset = offset + inner_offset + 1
        csv_util.export_txts_to_csvfile(txts, output_csv)


# reimports the item data
# param[in] write_to_file: if true, the updated tablepack will be written to a new file.
#                          Otherwise the updated tablepack will be reutrned
def reimport_item_txt(write_to_file: bool=True, header_data=None, table_tablepack=None):
    # each item is represented by two lines,
    # the first for the name, and the second for the description.
    item_list_cn = csv_util.load_csv_file(os.path.join(TEXT_DIR, 'item_cn.csv'))
    ITEM_FILE_INDEX = 4

    if table_tablepack is None:
        with open(os.path.join(GAME_RESOURCE_DIR, 'table_tablepack.dat'), 'rb') as f_table_tablepack:
            table_tablepack = f_table_tablepack.read()
        with open(os.path.join(GAME_RESOURCE_DIR, 'table_tablepack.hed'), 'rb') as f_header:
            header_data = bytearray(f_header.read())
    item_data = gamefile_util.datpack_to_decrypted_file_list(table_tablepack)[ITEM_FILE_INDEX]

    char_mapping = font_util.load_char_mapping()
    offset = 0
    item_list_idx = 0
    # item entry layout:  size: 0x170, 0x00~: item_name, 0x1A~: item_description, 0x150~: meta data
    while offset < len(item_data):
        # clear the original data first(note that the meta data is kept inpact)
        item_data[offset:offset + 0x150] = b'\x00' * 0x150

        mapped_item_name = font_util.txt_to_mapped_txt(item_list_cn[item_list_idx][2], char_mapping).encode('shift-jis')
        if len(mapped_item_name) == 0:
            mapped_item_name = item_list_cn[item_list_idx][1].encode('shift-jis')
        item_data[offset:offset+len(mapped_item_name)] = mapped_item_name
        mapped_item_desc = font_util.txt_to_mapped_txt(item_list_cn[item_list_idx+1][2], char_mapping).encode('shift-jis')
        if len(mapped_item_desc) == 0:
            mapped_item_desc = item_list_cn[item_list_idx+1][1].encode('shift-jis')
        item_data[offset+0x1A:offset+0x1A+len(mapped_item_desc)] = mapped_item_desc
        offset = offset + 0x170
        item_list_idx += 2
    
    # debug code
    with open(os.path.join(OUTPUT_DIR, '4.dat'), 'wb') as f_item:
        f_item.write(item_data)
    # debug code end
    
    header_data, table_tablepack = gamefile_util.reimport_datpack(header_data, table_tablepack, [(ITEM_FILE_INDEX, item_data)])

    if write_to_file:
        output_path_content = os.path.join(OUTPUT_DIR, 'table_tablepack_cn.dat')
        with open(output_path_content, 'wb') as f_table_tablepack:
            f_table_tablepack.write(table_tablepack)

        output_path_header = os.path.join(OUTPUT_DIR, 'table_tablepack_cn.hed')
        with open(output_path_header, 'wb') as f_header:
            f_header.write(header_data)
        print(f'Reimporting item txt completed. The main script file is generated at {output_path_content} and {output_path_header}.')
    else:
        return header_data, table_tablepack

# reimports the location data
# param[in] write_to_file: if true, the updated tablepack will be written to a new file.
#                          Otherwise the updated tablepack will be reutrned
def reimport_location_txt(write_to_file: bool=True, header_data=None, table_tablepack=None):
    # each line a location name.
    loc_list_cn = csv_util.load_csv_file(os.path.join(TEXT_DIR, 'loc_cn.csv'))
    LOC_FILE_INDEX = 6

    if table_tablepack is None:
        with open(os.path.join(GAME_RESOURCE_DIR, 'table_tablepack.dat'), 'rb') as f_table_tablepack:
            table_tablepack = f_table_tablepack.read()
        with open(os.path.join(GAME_RESOURCE_DIR, 'table_tablepack.hed'), 'rb') as f_header:
            header_data = bytearray(f_header.read())

    loc_data = gamefile_util.datpack_to_decrypted_file_list(table_tablepack)[LOC_FILE_INDEX]

    char_mapping = font_util.load_char_mapping()
    offset = 0x26
    loc_list_idx = 0
    # location entry layout: size: 0x26, 0xA~: name
    while offset < len(loc_data):
        mapped_loc_name = font_util.txt_to_mapped_txt(loc_list_cn[loc_list_idx][2], char_mapping).encode('shift-jis')
        if len(mapped_loc_name) == 0:
            mapped_loc_name = loc_list_cn[loc_list_idx][1].encode('shift-jis')
        loc_data[offset+0xA:offset+0xA+len(mapped_loc_name)] = mapped_loc_name
        loc_data[offset+0xA+len(mapped_loc_name):offset+0x26] = b'\x00' * (offset+0x26 - (offset+0xA+len(mapped_loc_name)))
        loc_list_idx += 1
        offset = offset + 0x26
    
    header_data, table_tablepack = gamefile_util.reimport_datpack(header_data, table_tablepack, [(LOC_FILE_INDEX, loc_data)])

    if write_to_file:
        output_path_content = os.path.join(OUTPUT_DIR, 'table_tablepack_cn.dat')
        with open(output_path_content, 'wb') as f_table_tablepack:
            f_table_tablepack.write(table_tablepack)

        output_path_header = os.path.join(OUTPUT_DIR, 'table_tablepack_cn.hed')
        with open(output_path_header, 'wb') as f_header:
            f_header.write(header_data)
        print(f'Reimporting location txt completed. The main script file is generated at {output_path_content} and {output_path_header}.')
    else:
        return header_data, table_tablepack

# reimport the boss data
# param[in] write_to_file: if true, the updated tablepack will be written to a new file.
#                          Otherwise the updated tablepack will be reutrned
def reimport_boss_txt(write_to_file: bool=True, header_data=None, table_tablepack=None):
    # each boss is represented by two lines,
    # the first for the name1, and the second for name2.
    boss_list_cn = csv_util.load_csv_file(os.path.join(TEXT_DIR, 'boss_cn.csv'))
    BOSS_FILE_INDEX = 3

    if table_tablepack is None:
        with open(os.path.join(GAME_RESOURCE_DIR, 'table_tablepack.dat'), 'rb') as f_table_tablepack:
            table_tablepack = f_table_tablepack.read()
        with open(os.path.join(GAME_RESOURCE_DIR, 'table_tablepack.hed'), 'rb') as f_header:
            header_data = bytearray(f_header.read())

    boss_data = gamefile_util.datpack_to_decrypted_file_list(table_tablepack)[BOSS_FILE_INDEX]

    char_mapping = font_util.load_char_mapping()
    offset = 0x0
    boss_list_idx = 0
    # location entry layout: size: 0x68, 0x32~: name1 0x4D~ name2
    while offset < len(boss_data) and boss_list_idx < len(boss_list_cn):
        mapped_boss_name1 = font_util.txt_to_mapped_txt(boss_list_cn[boss_list_idx][2], char_mapping).encode('shift-jis')
        if len(mapped_boss_name1) == 0:
            mapped_boss_name1 = boss_list_cn[boss_list_idx][1].encode('shift-jis')
        boss_data[offset+0x32:offset+0x32+len(mapped_boss_name1)] = mapped_boss_name1
        boss_data[offset+0x32+len(mapped_boss_name1):offset+0x4D] = b'\x00' * (offset+0x4D - (offset+0x32+len(mapped_boss_name1)))
        boss_list_idx += 1

        mapped_boss_name2 = font_util.txt_to_mapped_txt(boss_list_cn[boss_list_idx][2], char_mapping).encode('shift-jis')
        if len(mapped_boss_name2) == 0:
            mapped_boss_name2 = boss_list_cn[boss_list_idx][1].encode('shift-jis')
        boss_data[offset+0x4D:offset+0x4D+len(mapped_boss_name1)] = mapped_boss_name1
        boss_data[offset+0x4D+len(mapped_boss_name1):offset+0x68] = b'\x00' * (offset+0x68 - (offset+0x4D+len(mapped_boss_name2)))
        boss_list_idx += 1

        offset = offset + 0x68
    
    header_data, table_tablepack = gamefile_util.reimport_datpack(header_data, table_tablepack, [(BOSS_FILE_INDEX, boss_data)])

    if write_to_file:
        output_path_content = os.path.join(OUTPUT_DIR, 'table_tablepack_cn.dat')
        with open(output_path_content, 'wb') as f_table_tablepack:
            f_table_tablepack.write(table_tablepack)

        output_path_header = os.path.join(OUTPUT_DIR, 'table_tablepack_cn.hed')
        with open(output_path_header, 'wb') as f_header:
            f_header.write(header_data)
        print(f'Reimporting location txt completed. The main script file is generated at {output_path_content} and {output_path_header}.')
    else:
        return header_data, table_tablepack

# reimports the character data
# param[in] write_to_file: if true, the updated tablepack will be written to a new file.
#                          Otherwise the updated tablepack will be reutrned
def reimport_character_txt(write_to_file: bool=True, header_data=None, table_tablepack=None):
    # each character is represented by three lines,
    # each line a name.
    char_list_cn = csv_util.load_csv_file(os.path.join(TEXT_DIR, 'char_cn.csv'))
    CHAR_FILE_INDEX = 8

    if table_tablepack is None:
        with open(os.path.join(GAME_RESOURCE_DIR, 'table_tablepack.dat'), 'rb') as f_table_tablepack:
            table_tablepack = f_table_tablepack.read()
        with open(os.path.join(GAME_RESOURCE_DIR, 'table_tablepack.hed'), 'rb') as f_header:
            header_data = bytearray(f_header.read())

    char_data = gamefile_util.datpack_to_decrypted_file_list(table_tablepack)[CHAR_FILE_INDEX]

    char_mapping = font_util.load_char_mapping()
    offset = 0x50
    char_list_idx = 0
    # character entry layout: size: 0x50, 0x2C~: name1, 0x38~: name2, 0x44~: name3
    while offset < len(char_data):
        mapped_char_name1 = font_util.txt_to_mapped_txt(char_list_cn[char_list_idx][2], char_mapping).encode('shift-jis')
        if len(mapped_char_name1) == 0:
            mapped_char_name1 = char_list_cn[char_list_idx][1].encode('shift-jis')
        char_data[offset+0x2C:offset+0x2C+len(mapped_char_name1)] = mapped_char_name1
        char_data[offset+0x2C+len(mapped_char_name1):offset+0x38] = b'\x00' * (offset+0x38 - (offset+0x2C+len(mapped_char_name1)))

        char_list_idx += 1
        mapped_char_name2 = font_util.txt_to_mapped_txt(char_list_cn[char_list_idx][2], char_mapping).encode('shift-jis')
        if len(mapped_char_name2) == 0:
            mapped_char_name2 = char_list_cn[char_list_idx][1].encode('shift-jis')
        char_data[offset+0x38:offset+0x38+len(mapped_char_name2)] = mapped_char_name2
        char_data[offset+0x38+len(mapped_char_name2):offset+0x44] = b'\x00' * (offset+0x44 - (offset+0x38+len(mapped_char_name2)))

        char_list_idx += 1
        mapped_char_name3 = font_util.txt_to_mapped_txt(char_list_cn[char_list_idx][2], char_mapping).encode('shift-jis')
        if len(mapped_char_name3) == 0:
            mapped_char_name3 = char_list_cn[char_list_idx][1].encode('shift-jis')
        char_data[offset+0x44:offset+0x44+len(mapped_char_name3)] = mapped_char_name3
        char_data[offset+0x44+len(mapped_char_name3):offset+0x50] = b'\x00' * (offset+0x50 - (offset+0x44+len(mapped_char_name3)))

        offset = offset + 0x50
        char_list_idx += 1
    
    # debug code
    # with open(os.path.join(OUTPUT_DIR, '4.dat'), 'wb') as f_item:
    #     f_item.write(char_data)
    # debug code end
    
    header_data, table_tablepack = gamefile_util.reimport_datpack(header_data, table_tablepack, [(CHAR_FILE_INDEX, char_data)])

    if write_to_file:
        output_path_content = os.path.join(OUTPUT_DIR, 'table_tablepack_cn.dat')
        with open(output_path_content, 'wb') as f_table_tablepack:
            f_table_tablepack.write(table_tablepack)

        output_path_header = os.path.join(OUTPUT_DIR, 'table_tablepack_cn.hed')
        with open(output_path_header, 'wb') as f_header:
            f_header.write(header_data)
        print(f'Reimporting char txt completed. The main script file is generated at {output_path_content} and {output_path_header}.')
    else:
        return header_data, table_tablepack

# reimport the tablepack data
def reimport_table_txt():
    header_data, table_tablepack = reimport_character_txt(False)
    header_data, table_tablepack = reimport_location_txt(False, header_data, table_tablepack)
    header_data, table_tablepack = reimport_boss_txt(False, header_data, table_tablepack)
    header_data, table_tablepack = reimport_item_txt(False, header_data, table_tablepack)
    header_data, table_tablepack = reimport_battle_txt(False, header_data, table_tablepack)
    header_data, table_tablepack = reimport_battle_comb_txt(False, header_data, table_tablepack)

    output_path_content = os.path.join(OUTPUT_DIR, 'table_tablepack_cn.dat')
    with open(output_path_content, 'wb') as f_table_tablepack:
        f_table_tablepack.write(table_tablepack)

    output_path_header = os.path.join(OUTPUT_DIR, 'table_tablepack_cn.hed')
    with open(output_path_header, 'wb') as f_header:
        f_header.write(header_data)

    print(f'Reimporting tablepack completed. The main script file is generated at {output_path_content} and {output_path_header}.')

# reimports the map data
def reimport_map_txt():
    map_list_cn = csv_util.load_csv_file(os.path.join(TEXT_DIR, 'map_cn.csv'))

    with open(os.path.join(GAME_RESOURCE_DIR, 'map_mapdatpack.dat'), 'rb') as f_map_mapdatpack:
        map_mapdatpack = f_map_mapdatpack.read()
    with open(os.path.join(GAME_RESOURCE_DIR, 'map_mapdatpack.hed'), 'rb') as f_header:
        header_data = bytearray(f_header.read())

    char_mapping = font_util.load_char_mapping()
    reimport_list = []
    map_data_list = gamefile_util.datpack_to_decrypted_file_list(map_mapdatpack)
    for file_index in range(16):
        map_data = map_data_list[file_index]

        offset = 0xAAA0
        map_list_idx = 0
        # clear the original data first
        map_data[offset:] = b'\x00' * (len(map_data) - offset)
        while map_list_idx < len(map_list_cn):
            prefix, script_id, line_id = common_util.split_uid(map_list_cn[map_list_idx][5])
            script_id = script_id - common_util.SCRIPT_ID_BASE
            if script_id == file_index:
                mapped_map_txt = font_util.txt_to_mapped_txt(map_list_cn[map_list_idx][2], char_mapping).encode('shift-jis')
                if len(mapped_map_txt) == 0:
                    mapped_map_txt = map_list_cn[map_list_idx][1].encode('shift-jis')
                if offset+len(mapped_map_txt) >= len(map_data):
                    extra_space_required = offset + len(mapped_map_txt) - len(map_data) + 1
                    map_data = map_data + b'\x00' * (extra_space_required)
                map_data[offset:offset+len(mapped_map_txt)] = mapped_map_txt
                offset = offset + len(mapped_map_txt) + 1
            map_list_idx += 1
        if len(map_data) % 2 == 1:
            map_data = map_data + b'\x00' # 2-byte alignment
        if file_index == 0:
            with open(os.path.join(OUTPUT_DIR, 'f_test.data'), 'wb') as f_test:
                f_test.write(map_data)

        reimport_list.append((file_index, map_data))

    header_data, map_mapdatpack = gamefile_util.reimport_datpack(header_data, map_mapdatpack, reimport_list)
    
    output_path_content = os.path.join(OUTPUT_DIR, 'map_mapdatpack_cn.dat')
    with open(output_path_content, 'wb') as f_map_mapdatpack:
        f_map_mapdatpack.write(map_mapdatpack)

    output_path_header = os.path.join(OUTPUT_DIR, 'map_mapdatpack_cn.hed')
    with open(output_path_header, 'wb') as f_header:
        f_header.write(header_data)

    print(f'Reimporting map txt completed. The main script file is generated at {output_path_content} and {output_path_header}.')

# reimports the battle data
# param[in] write_to_file: if true, the updated tablepack will be written to a new file.
#                          Otherwise the updated tablepack will be reutrned
def reimport_battle_txt(write_to_file: bool=True, header_data=None, table_tablepack=None):
    battle_list_cn = csv_util.load_csv_file(os.path.join(TEXT_DIR, 'battle_cn.csv'))
    BATTLE_FILE_INDEX = 11

    if table_tablepack is None:
        with open(os.path.join(GAME_RESOURCE_DIR, 'table_tablepack.dat'), 'rb') as f_table_tablepack:
            table_tablepack = f_table_tablepack.read()
        with open(os.path.join(GAME_RESOURCE_DIR, 'table_tablepack.hed'), 'rb') as f_header:
            header_data = bytearray(f_header.read())

    battle_data = gamefile_util.datpack_to_decrypted_file_list(table_tablepack)[BATTLE_FILE_INDEX]

    char_mapping = font_util.load_char_mapping()
    offset = 0
    battle_list_idx = 0
    # battle action block layout:
    # total size: 0x64
    # 0x00-0x03: unknown
    # 0x04-0x07: action id
    # 0x08-0x0b: unknown
    # 0x0c: action name
    # 0x24: action description
    while offset < len(battle_data):
        mapped_action_name = font_util.txt_to_mapped_txt(battle_list_cn[battle_list_idx][2], char_mapping).encode('shift-jis')
        if len(mapped_action_name) == 0:
            mapped_action_name = battle_list_cn[battle_list_idx][1].encode('shift-jis')
        battle_data[offset+0xC:offset+0xC+len(mapped_action_name)] = mapped_action_name
        battle_data[offset+0xC+len(mapped_action_name):offset+0x24] = b'\x00' * (offset+0x24 - (offset+0xC+len(mapped_action_name)))
        battle_list_idx += 1

        mapped_action_desc = font_util.txt_to_mapped_txt(battle_list_cn[battle_list_idx][2], char_mapping).encode('shift-jis')
        if len(mapped_action_desc) == 0:
            mapped_action_desc = battle_list_cn[battle_list_idx][1].encode('shift-jis')
        battle_data[offset+0x24:offset+0x24+len(mapped_action_desc)] = mapped_action_desc
        battle_data[offset+0x24+len(mapped_action_desc):offset+0x64] = b'\x00' * (offset+0x64 - (offset+0x24+len(mapped_action_desc)))
        battle_list_idx += 1
        offset = offset + 0x64
    
    header_data, table_tablepack = gamefile_util.reimport_datpack(header_data, table_tablepack, [(BATTLE_FILE_INDEX, battle_data)])

    if write_to_file:
        output_path_content = os.path.join(OUTPUT_DIR, 'table_tablepack_cn.dat')
        with open(output_path_content, 'wb') as f_table_tablepack:
            f_table_tablepack.write(table_tablepack)

        output_path_header = os.path.join(OUTPUT_DIR, 'table_tablepack_cn.hed')
        with open(output_path_header, 'wb') as f_header:
            f_header.write(header_data)
        print(f'Reimporting battle txt completed. The main script file is generated at {output_path_content} and {output_path_header}.')
    else:
        return header_data, table_tablepack

# reimports the battle-comb data
# param[in] write_to_file: if true, the updated tablepack will be written to a new file.
#                          Otherwise the updated tablepack will be reutrned
def reimport_battle_comb_txt(write_to_file: bool=True, header_data=None, table_tablepack=None):
    battle_list_cn = csv_util.load_csv_file(os.path.join(TEXT_DIR, 'battle-comb_cn.csv'))
    BATTLE_COMB_FILE_INDEX = 12

    if table_tablepack is None:
        with open(os.path.join(GAME_RESOURCE_DIR, 'table_tablepack.dat'), 'rb') as f_table_tablepack:
            table_tablepack = f_table_tablepack.read()
        with open(os.path.join(GAME_RESOURCE_DIR, 'table_tablepack.hed'), 'rb') as f_header:
            header_data = bytearray(f_header.read())

    battle_data = gamefile_util.datpack_to_decrypted_file_list(table_tablepack)[BATTLE_COMB_FILE_INDEX]

    char_mapping = font_util.load_char_mapping()
    offset = 0x48
    battle_list_idx = 0
    # battle comb-action block layout:
    # total size: 0x48
    # 0x00~0x07: unknown
    # 0x08~: action description
    while offset < len(battle_data):
        mapped_action_name = font_util.txt_to_mapped_txt(battle_list_cn[battle_list_idx][2], char_mapping).encode('shift-jis')
        if len(mapped_action_name) == 0:
            mapped_action_name = battle_list_cn[battle_list_idx][1].encode('shift-jis')
        battle_data[offset+0x8:offset+0x8+len(mapped_action_name)] = mapped_action_name
        battle_data[offset+0x8+len(mapped_action_name):offset+0x48] = b'\x00' * (offset+0x48 - (offset+0x8+len(mapped_action_name)))
        battle_list_idx += 1

        offset = offset + 0x48
    
    header_data, table_tablepack = gamefile_util.reimport_datpack(header_data, table_tablepack, [(BATTLE_COMB_FILE_INDEX, battle_data)])

    if write_to_file:
        output_path_content = os.path.join(OUTPUT_DIR, 'table_tablepack_cn.dat')
        with open(output_path_content, 'wb') as f_table_tablepack:
            f_table_tablepack.write(table_tablepack)

        output_path_header = os.path.join(OUTPUT_DIR, 'table_tablepack_cn.hed')
        with open(output_path_header, 'wb') as f_header:
            f_header.write(header_data)
        print(f'Reimporting battle-comb txt completed. The main script file is generated at {output_path_content} and {output_path_header}.')
    else:
        return header_data, table_tablepack

def export_battle_txt():
    with open(os.path.join('output_tablepack', '11.dat'), 'rb') as battle_file:
        battle_data = battle_file.read()
    line_number = 1
    txts = dict()
    offset = 0
    # battle action block layout:
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
    with open(os.path.join(OUTPUT_DIR, + 'battle.csv'), 'w', encoding='utf8', newline='') as output_csv:
        csv_util.export_txts_to_csvfile(txts, output_csv)

def export_battle_comb_txt():
    with open(os.path.join('output_tablepack', '12.dat'), 'rb') as battle_file:
        battle_data = battle_file.read()
    line_number = 1
    txts = dict()
    # battle comb-action block layout:
    # total size: 0x48
    # 0x00~0x07: unknown
    # 0x08~: action description

    # skip the empty first one
    offset = 0x48
    while offset < len(battle_data):
        inner_offset = 0x08
        while offset < len(battle_data) and inner_offset < 0x48 and battle_data[offset+inner_offset] != 0x00:
            inner_offset = inner_offset + 1
        action_name = battle_data[offset+0x08:offset+inner_offset].decode('shift-jis')
        txts[common_util.uid('battle_comb', common_util.SCRIPT_ID_BASE, line_number)] = action_name 
        line_number = line_number + 1
        offset = offset + 0x48
    with open(os.path.join(OUTPUT_DIR, 'battle_comb.csv'), 'w', encoding='utf8', newline='') as output_csv:
        csv_util.export_txts_to_csvfile(txts, output_csv)

def export_datpack_sample_1():
    # table_tablepack script processing sample
    fin = open(GAME_RESOURCE_DIR + '/map_mapdatpack.dat', 'rb')
    data = fin.read()
    fin.close()
    scripts = gamefile_util.datpack_to_decrypted_file_list(data)
    for script_id, data in enumerate(scripts):
        fout = open('output_mappack_en/%d.dat' % script_id, 'wb')
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

def reimport_exe_txt():
    with open(os.path.join(TEXT_DIR, 'exe_cn.csv'), 'r', encoding='utf-8') as exe_csv:
        # ignore header line
        exe_csv.readline()
        cn_txts = csv_util.exe_csv_to_cn_txts(exe_csv.readlines())
    
    with open(os.path.join(GAME_RESOURCE_DIR, 'Death Mark.exe'), 'rb') as exe:
        exe_data = bytearray(exe.read())

    char_mapping = font_util.load_char_mapping()

    # We need to adjust the relative positions of some text strings
    # because their translated versions are longer than the originals.
    # Since it's difficult to implement a general solution and there are only two longer strings,
    # we just manually adjust the offsets for these cases.

    # the first one:
    # 0x2EC5CC: the original offset value of the string "%s を同行者にしますか？"
    #           716C70 ~ 716C87 -> 716C70 ~ 716C89
    # 0x2EC5E0: the original offset value of the string "眼鏡"
    #           716C88 ~ -> 716C8A ~
    exe_data[0x2EC5E0:0x2EC5E4] = 0x716C8A.to_bytes(4, 'little')
    # 0x315A88: the actual position that "716C88" points to in the executable file.
    exe_data[0x315A88] = 0
    exe_data[0x315A89] = 0
    # the second one:
    # 0x2EC5DC: the original offset value of the string "髭"
    #           716C40 ~ 716C43 -> 716C40 ~ 716C45
    # 0x2EC5F4: the original offset value of the string "画面の解像度を設定します（現在設定できません）"
    #           716C44 ~ -> 716C46 ~
    exe_data[0x2EC5F4:0x2EC5F8] = 0x716C46.to_bytes(4, 'little')
    # 0x315AC4: the actual position that "716C44" points to in the executable file.
    exe_data[0x315AC4] = 0
    exe_data[0x315AC5] = 0


    line_number = 1
    jp_txts = dict()
    offset = 0x314E04
    MSG_TABLE_END = 0x315EC4
    # exe text block data structure:
    # 0-terminated strings
    while offset < MSG_TABLE_END:
        inner_offset = 0
        while exe_data[offset+inner_offset] != 0x00:
            inner_offset = inner_offset + 1
        exe_txt = exe_data[offset:offset+inner_offset].decode('shift-jis')
        txt_id = common_util.uid('exe', common_util.SCRIPT_ID_BASE, line_number)
        jp_txts[txt_id] = exe_txt
        line_number = line_number + 1
        padding_zeroes = 0
        while exe_data[offset+inner_offset] == 0x00 and offset+inner_offset < MSG_TABLE_END:
            padding_zeroes = padding_zeroes + 1
            inner_offset = inner_offset + 1

        # minus 1 because we need 1 zero for a 0-terminated string
        padding_zeroes = padding_zeroes - 1

        cn_len = 0
        for ch in cn_txts[txt_id]:
            if ord(ch) >= 0x7f:
                cn_len = cn_len + 2
            else:
                cn_len = cn_len + 1

        if cn_len - len(exe_txt.encode('shift-jis')) - padding_zeroes > 0:
            print('Error: original txt:%s is shorter than new txt:%s. new/(old+padding) = %d/%d'
                % (exe_txt, cn_txts[txt_id], cn_len, len(exe_txt.encode('shift-jis')) + padding_zeroes))
            return

        mapped_cn_txt = font_util.txt_to_mapped_txt(cn_txts[txt_id], char_mapping).encode('shift-jis')
        exe_data[offset:offset+len(mapped_cn_txt)] = mapped_cn_txt

        cur_pos = offset+len(mapped_cn_txt)
        while cur_pos < offset + inner_offset:
            exe_data[cur_pos] = 0
            cur_pos += 1
        offset = offset + inner_offset
    
    # The string "新規作成" is placed in the English text section (binary file offset: 0x314454).
    # We only need to replace this string manually; other texts in the English section do not need translation.
    cn_str_new_data = '新建存档'
    mapped_cn_new_data = font_util.txt_to_mapped_txt(cn_str_new_data, char_mapping).encode('shift-jis')
    exe_data[0x314454:0x314454 + len(mapped_cn_new_data)] = mapped_cn_new_data
    exe_data[0x314454 + len(mapped_cn_new_data)] = 0
    
    output_path = os.path.join(OUTPUT_DIR, 'Death Mark_cn.exe')
    with open(output_path, 'wb') as fout:
        fout.write(exe_data)
    
    print('Reimporting exe txt completed.')

def export_exe_txt():
    with open(os.path.join(GAME_RESOURCE_DIR, 'Death Mark.exe'), 'rb') as exe:
        exe_data = exe.read()
    line_number = 1
    txts = dict()
    offset = 0x314E04
    MSG_TABLE_END = 0x315EC4
    # exe battle text block data structure:
    # 0-terminated strings
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

    with open(os.path.join(OUTPUT_DIR, 'exe_cn.csv'), 'w', encoding='utf8', newline='') as output_csv:
        csv_util.export_txts_to_csvfile(txts, output_csv)

def export_location_txt():
    with open(os.path.join('output_tablepack', '6.dat'), 'rb') as loc_file:
        loc_data = loc_file.read()
    # location block layout:
    # total size: 0x26
    # 0xA: name 

    # skip the first block which is a zero-filled block
    line_number = 1
    txts = dict()
    offset = 0x26
    while offset < len(loc_data):
        inner_offset = 0xA
        while offset < len(loc_data) and loc_data[offset+inner_offset] != 0x00:
            inner_offset = inner_offset + 1
        name1 = loc_data[offset+0xA:offset+inner_offset].decode('shift-jis')
        txts[common_util.uid('loc', common_util.SCRIPT_ID_BASE, line_number)] = name1
        line_number = line_number + 1
        offset = offset + 0x26

    with open(os.path.join(OUTPUT_DIR, 'loc.csv'), 'w', encoding='utf8', newline='') as output_csv:
        csv_util.export_txts_to_csvfile(txts, output_csv)

def export_boss_txt():
    with open(os.path.join('output_tablepack', '3.dat'), 'rb') as boss_file:
        boss_data = boss_file.read()
    # boss block layout:
    # total size: 0x68
    # 0x32: name1
    # 0x4D: name2

    line_number = 1
    txts = dict()
    offset = 0x0
    while offset < len(boss_data):
        inner_offset = 0x32
        while offset < len(boss_data) and boss_data[offset+inner_offset] != 0x00:
            inner_offset = inner_offset + 1
        name1 = boss_data[offset+0x32:offset+inner_offset].decode('shift-jis')
        txts[common_util.uid('boss', common_util.SCRIPT_ID_BASE, line_number)] = name1
        line_number = line_number + 1

        inner_offset = 0x4D
        while offset < len(boss_data) and boss_data[offset+inner_offset] != 0x00:
            inner_offset = inner_offset + 1
        name2 = boss_data[offset+0x4D:offset+inner_offset].decode('shift-jis')
        txts[common_util.uid('boss', common_util.SCRIPT_ID_BASE, line_number)] = name2
        line_number = line_number + 1

        offset = offset + 0x68

    with open(os.path.join(OUTPUT_DIR, 'boss.csv'), 'w', encoding='utf8', newline='') as output_csv:
        csv_util.export_txts_to_csvfile(txts, output_csv)

def export_character_txt():
    with open(os.path.join('output_tablepack', '8.dat'), 'rb') as char_file:
        char_data = char_file.read()
    # character block layout:
    # total size: 0x50
    # 0x2c: name1 
    # 0x38: name2
    # 0x44: name3

    # skip the first block which is a zero-filled block
    line_number = 1
    txts = dict()
    offset = 0x50
    while offset < len(char_data):
        inner_offset = 0x2C
        while offset < len(char_data) and char_data[offset+inner_offset] != 0x00:
            inner_offset = inner_offset + 1
        name1 = char_data[offset+0x2C:offset+inner_offset].decode('shift-jis')
        txts[common_util.uid('char', common_util.SCRIPT_ID_BASE, line_number)] = name1
        line_number = line_number + 1

        inner_offset = 0x38
        while offset < len(char_data) and char_data[offset+inner_offset] != 0x00:
            inner_offset = inner_offset + 1
        name2 = char_data[offset+0x38:offset+inner_offset].decode('shift-jis')
        txts[common_util.uid('char', common_util.SCRIPT_ID_BASE, line_number)] = name2
        line_number = line_number + 1

        inner_offset = 0x44
        while offset < len(char_data) and char_data[offset+inner_offset] != 0x00:
            inner_offset = inner_offset + 1
        name3 = char_data[offset+0x44:offset+inner_offset].decode('shift-jis')
        txts[common_util.uid('char', common_util.SCRIPT_ID_BASE, line_number)] = name3
        line_number = line_number + 1
        offset = offset + 0x50

    with open(os.path.join(OUTPUT_DIR, 'char.csv'), 'w', encoding='utf8', newline='') as output_csv:
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
    
    print('start generating main cn font file...')
    with open(os.path.join(GAME_RESOURCE_DIR, 'fontdata_fontdata01.exp'), 'rb') as fin:
        jp_font_data = fin.read()
    cn_font_data = font_util.reimport_font_data(jp_font_data, 40, 0x1e)
    font_file_path = os.path.join(OUTPUT_DIR, 'fontdata_fontdata01_cn.exp')
    with open(font_file_path, 'wb') as fout:
        fout.write(cn_font_data)

    print('start generating second cn font file...')
    with open(os.path.join(GAME_RESOURCE_DIR, 'fontdata_fontdata02.exp'), 'rb') as fin:
        jp_font_data = fin.read()
    cn_font_data = font_util.reimport_font_data(jp_font_data, 30, 0x16)
    font_file_path = os.path.join(OUTPUT_DIR, 'fontdata_fontdata02_cn.exp')
    with open(font_file_path, 'wb') as fout:
        fout.write(cn_font_data)

    print(f'generating cn font file finished. The font file is generated at {font_file_path}.')
    print('All jobs done!')

def parse_args():
    parser = argparse.ArgumentParser(description='This file is the main script for the shiin localization \
                                     project.\n You SHOULD always execute this script and DON\'T execute \
                                     other scripts directly \
                                     unless you understand what you are doing. Make sure you have configured the \
                                     configuration variables defined in the config.py file.')
    parser.add_argument('--export_dat', dest='export_dat', action='store', choices=['main','maze','exe'], help='export data file to csv files.')
    parser.add_argument('--export_pack', dest='export_pack', action='store', choices=['map','item','loc','char','boss'], help='export .tablepack to csv files.')
    parser.add_argument('--export_ui', dest='export_ui', action='store_true', help='export ui.dat to dds files.')
    parser.add_argument('--gen_patch', dest='patch', action='store_true', help='generate patch files.')
    parser.add_argument('--reimport', dest='reimport', action='store', choices=['all','main','maze','map','exe','table'], help='reimport localized \
                        files patch files. Use "all" to export all necessary .dat files.')
    parser.add_argument('--gen_font', dest='font', action='store_true', help='generate the main font \
                        file for Chinese characters.')
    args = parser.parse_args()
    if len(sys.argv) == 1:
        parser.print_help()
        return
    if args.export_dat:
        if args.export_dat == 'exe':
            print('Start exporting exe txt')
            export_exe_txt()
    if args.export_pack:
        if args.export_pack == 'all':
            print('Start exporting map txt')
            export_map_txt()
            print('Start exporting item txt')
            export_item_txt()
        elif args.export_pack == 'map':
            export_map_txt()
        elif args.export_pack == 'item':
            export_item_txt()
        elif args.export_pack == 'char':
            print('Start exporting character txt')
            export_character_txt()
        elif args.export_pack == 'loc':
            print('Start exporting location txt')
            export_location_txt()
        elif args.export_pack == 'boss':
            print('Start exporting boss txt')
            export_boss_txt()
    if args.export_ui:
        export_ui_dds()
    elif args.patch:
        gen_patch()
    elif args.font:
        gen_cn_font()
    elif args.reimport:
        if args.reimport == 'main':
            print('Start reimorting main script...')
            reimport_main_script()
        elif args.reimport == 'maze':
            print('Start reimorting maze script...')
            reimport_maze_script()
        elif args.reimport == 'exe':
            print('Start reimorting exe txt...')
            reimport_exe_txt()
        elif args.reimport == 'table':
            print('Start reimorting tablepack dat...')
            reimport_table_txt()
        elif args.reimport == 'map':
            print('Start reimorting map txt...')
            reimport_map_txt()
        elif args.reimport == 'all':
            print('Start reimorting main script...')
            reimport_main_script()
            print('Start reimorting maze script...')
            reimport_maze_script()
            print('Start reimorting exe txt...')
            reimport_exe_txt()
            print('Start reimorting tablepack dat...')
            reimport_table_txt()
            print('Start reimorting map txt...')
            reimport_map_txt()
            print('Everything done!')


def main():
    parse_args()

def debug():
    # table_tablepack script processing sample
    fin = open(GAME_RESOURCE_DIR + '/map_mapdatpack_en.dat', 'rb')
    data = fin.read()
    fin.close()
    scripts = gamefile_util.datpack_to_decrypted_file_list(data)
    for script_id, data in enumerate(scripts):
        fout = open('output_mappack_en/%d.dat' % script_id, 'wb')
        # for uid, txt in script_to_txts('tablepack', script_id, data).items():
            #fout.write(uid + ',' + txt + '\n')
        fout.write(data)
        fout.close()
    pass
    # export_main_script()
    # export_maze_script()
    # example.export_datpack_example(os.path.join(OUTPUT_DIR, 'table_tablepack.dat'))
    # export_item_txt()
    # export_battle_txt()
    # export_txt_in_exe()
    # reimport_txt_in_exe()
    # export_battle_comb_txt()

    # with open('output_tablepack/4.dat', 'rb') as f:
    #     data = gamefile_util.compress(f.read())

    # with open('output_tablepack_debug/debug_item', 'rb') as f:
    #     raw_size = int.from_bytes(f.read(4), 'little')
    #     code_size = int.from_bytes(f.read(4), 'little')
    #     data = gamefile_util.decompress_new(f.read(), code_size, raw_size, False)
    #     with open('output_tablepack_debug/debug_item_decrpyted', 'wb') as fd:
    #         fd.write(data)

if __name__ == '__main__':
    main()
    # debug()