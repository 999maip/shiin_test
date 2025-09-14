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
        'Death Mark_cn.exe',
    ]
    file_paths = [
        'resource',
        'resource',
        'resource',
        'resource',
        'resource',
        'resource',
        'resource',
        'resource',
        '.',
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