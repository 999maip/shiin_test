import shutil
import sys
import os
from config import OUTPUT_DIR
from pathlib import Path

def main():
    if len(sys.argv) != 2:
        print(f'Usage: {sys.argv[0]} <destination_path>')
        sys.exit(1)

    dest_path = Path(sys.argv[1])
    if not dest_path.exists():
        print(f'Destination path does not exist: {dest_path}')
        sys.exit(1)

    source_files = [
        'event_script_cn.dat',
        'event_mazeevent_cn.dat',
        'fontdata_fontdata01_cn.exp',
        'fontdata_fontdata02_cn.exp',
        'table_tablepack_cn.dat',
        'table_tablepack_cn.hed',
        'map_mapdatpack_cn.dat',
        'map_mapdatpack_cn.hed',
        'graphic_comtex_comtex_exg_cn.zip',
        'graphic_title_exg_cn.zip',
        'graphic_ev_ev_230_dat_cn.zip',
        'graphic_ev_ev_240_dat_cn.zip',
        'graphic_ev_ev_250_dat_cn.zip',
        'graphic_ev_ev_260_dat_cn.zip',
        'graphic_ev_ev_270_dat_cn.zip',
        'graphic_ev_ev_510_dat_cn.zip',
        'graphic_ev_ev_520_dat_cn.zip',
        'graphic_ev_ev_530_dat_cn.zip',
        'graphic_ev_ev_540_dat_cn.zip',
        'graphic_ev_ev_550_dat_cn.zip',
        'graphic_ev_ev_650_dat_cn.zip',
        'graphic_ev_ev_660_dat_cn.zip',
        'graphic_th_thumbnail_0510_exg_cn.zip',
        'graphic_th_thumbnail_0520_exg_cn.zip',
        'graphic_th_thumbnail_0530_exg_cn.zip',
        'graphic_th_thumbnail_0540_exg_cn.zip',
        'graphic_th_thumbnail_0550_exg_cn.zip',
        'graphic_th_thumbnail_0660_exg_cn.zip',
        'ui_cn.dat',
        'Death Mark_cn.exe',
    ]
    file_paths = [
        'resource', 'resource', 'resource', 'resource', 'resource',
        'resource', 'resource', 'resource', 'resource', 'resource',
        'resource', 'resource', 'resource', 'resource', 'resource',
        'resource', 'resource', 'resource', 'resource', 'resource',
        'resource', 'resource', 'resource', 'resource', 'resource',
        'resource', 'resource', 'resource', 'resource', '.',
    ]

    for index, src in enumerate(source_files):
        src_path = Path(OUTPUT_DIR)/src
        if not src_path.exists():
            print(f'Source file not found: {src_path}')
            continue

        new_name = src_path.name.replace('_cn', '')
        dst_path = dest_path/file_paths[index]/new_name

        shutil.copy2(src_path, dst_path)
        print(f'Copied {src_path} -> {dst_path}')

if __name__ == '__main__':
    main()