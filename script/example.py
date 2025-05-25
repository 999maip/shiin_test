import os
import zipfile
import gamefile_util
from config import *

# reimport title image
def exg_reimport_example():
    with open('texture_test/graphic_title.exg', 'rb') as old_exg_file:
        old_title_exg = old_exg_file.read()
    with open('texture_test/graphic_title_cn.png', 'rb') as png_file:
        title_png = png_file.read()
    with open('texture_test/graphic_title_cn.exg', 'wb') as exg_file:
        exg_file.write(gamefile_util.png_to_exg(title_png, old_title_exg))

# reimport images in folder
def exg_reimport_example2():
    path = 'C:\\Users\\Administrator\\Downloads\\textures_to_localize-ch\\'
    os.chdir(path)
    files = os.listdir(path)
    for file in files:
        if 'raw' in file:
            continue
        if not file.endswith('png'):
            continue
        with zipfile.ZipFile('old/' + file[:-4] + '.zip', 'r') as zip_ref:
            zip_ref.extractall('old/')
        
        exg_filename = file[:-4]
        if file == 'graphic_comtex_comtex_exg.png':
            exg_filename = 'graphic_comtex_comtex.exg'
        elif file == 'graphic_title.exg.png':
            exg_filename = 'graphic_title.exg'

        with open('old/' + exg_filename, 'rb') as old_exg_file:
            old_exg = old_exg_file.read()
        with open(file, 'rb') as png_file:
            new_png = png_file.read()
        with open(exg_filename, 'wb') as exg_file:
            exg_file.write(gamefile_util.png_to_exg(new_png, old_exg))
        with zipfile.ZipFile(file[:-4] + '.zip', 'w', zipfile.ZIP_DEFLATED) as myzip:
            myzip.write(exg_filename)
        print('file %s replace succeeded!' % file[:-4])

# table_tablepack script processing example
def export_datpack_example(filepath):
    with open(filepath, 'rb') as f:
        data = f.read()

    scripts = gamefile_util.datpack_to_decrypted_file_list(data)
    for script_id, data in enumerate(scripts):
        with open('output_tablepack_debug/%d.dat' % script_id, 'wb') as fout:
            fout.write(data)
