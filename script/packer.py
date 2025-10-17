import argparse
import os
import subprocess
import sys
import shutil
import hashlib

MAGIC_NUMBER = '5A7A59794464'

FILE_TEMPLATE_XML = """<File>
    <Type>2</Type>
    <Name><!-- inject: fileName --></Name>
    <File><!-- inject: filePath --></File>
    <ActiveX>false</ActiveX>
    <ActiveXInstall>false</ActiveXInstall>
    <Action>0</Action>
    <OverwriteDateTime>false</OverwriteDateTime>
    <OverwriteAttributes>false</OverwriteAttributes>
    <PassCommandLine>false</PassCommandLine>
</File>"""

FOLDER_TEMPLATE_XML = """<File>
    <Type>3</Type>
    <Name><!-- inject: folderName --></Name>
    <Action>0</Action>
    <OverwriteDateTime>false</OverwriteDateTime>
    <OverwriteAttributes>false</OverwriteAttributes>
    <Files><!-- inject: files --></Files>
</File>"""

PROJECT_TEMPLATE_XML = """<?xml version="1.0" encoding="utf-8"?>
<>
    <InputFile><!-- inject: inputExe --></InputFile>
    <OutputFile><!-- inject: outputExe --></OutputFile>
    <Files>
        <Enabled>true</Enabled>
        <DeleteExtractedOnExit>True</DeleteExtractedOnExit>
        <CompressFiles>False</CompressFiles>
        <Files>
            <File>
                <Type>3</Type>
                <Name>%DEFAULT FOLDER%</Name>
                <Action>0</Action>
                <OverwriteDateTime>false</OverwriteDateTime>
                <OverwriteAttributes>false</OverwriteAttributes>
                <Files><!-- inject: files --></Files>
            </File>
        </Files>
    </Files>
    <Registries>
        <Enabled>false</Enabled>
        <Registries>
            <Registry>
                <Type>1</Type>
                <Virtual>true</Virtual>
                <Name>Classes</Name>
                <ValueType>0</ValueType>
                <Value/>
                <Registries/>
            </Registry>
            <Registry>
                <Type>1</Type>
                <Virtual>true</Virtual>
                <Name>User</Name>
                <ValueType>0</ValueType>
                <Value/>
                <Registries/>
            </Registry>
            <Registry>
                <Type>1</Type>
                <Virtual>true</Virtual>
                <Name>Machine</Name>
                <ValueType>0</ValueType>
                <Value/>
                <Registries/>
            </Registry>
            <Registry>
                <Type>1</Type>
                <Virtual>true</Virtual>
                <Name>Users</Name>
                <ValueType>0</ValueType>
                <Value/>
                <Registries/>
            </Registry>
            <Registry>
                <Type>1</Type>
                <Virtual>true</Virtual>
                <Name>Config</Name>
                <ValueType>0</ValueType>
                <Value/>
                <Registries/>
            </Registry>
        </Registries>
    </Registries>
    <Packaging>
        <Enabled>false</Enabled>
    </Packaging>
    <Options>
        <ShareVirtualSystem>False</ShareVirtualSystem>
        <MapExecutableWithTemporaryFile>True</MapExecutableWithTemporaryFile>
        <AllowRunningOfVirtualExeFiles>True</AllowRunningOfVirtualExeFiles>
    </Options>
</>"""

# param[in] filepaths game file paths
# param[in] diff_root_path output folder names
def generate_diff(file_index:int, old_filepath:str, new_filepath:str, diff_root_path:str):
    CHUNK_SIZE = 8192 * 16

    old_folder_path = os.path.join(diff_root_path, f'{file_index}_o')
    new_folder_path = os.path.join(diff_root_path, f'{file_index}_n')
    os.mkdir(old_folder_path)
    os.mkdir(new_folder_path)

    f_old = open(old_filepath, 'rb')
    f_new = open(new_filepath, 'rb')
    md5_old = hashlib.md5()
    md5_new = hashlib.md5()
    size_old = 0
    size_new = 0
    diff_cnt = 0
    addr = 0
    while True:
        old = f_old.read(CHUNK_SIZE)
        new = f_new.read(CHUNK_SIZE)
        if (not old and not new) or (len(old) == 0 and len(new) == 0):
            break
        if old:
            md5_old.update(old)
            size_old += len(old)
        if new:
            md5_new.update(new)
            size_new += len(new)

        if old != new:
            po = open(os.path.join(old_folder_path, str(addr) + '.patch'), 'wb')
            po.write(old)
            po.close()
            no = open(os.path.join(new_folder_path, str(addr) + '.patch'), 'wb')
            no.write(new)
            no.close()
            diff_cnt += 1
        addr = addr + CHUNK_SIZE
    f_old.close()
    f_new.close()

    return md5_old.hexdigest(), md5_new.hexdigest(), format(size_old, 'x'), format(size_new, 'x'), diff_cnt

# inspired by https://github.com/etiktin/generate-evb
def generate_evb(input_path_abs:str, output_path_abs:str):
    global MAGIC_NUMBER
    project_name = f'project_{MAGIC_NUMBER}.evb'
    project_template = PROJECT_TEMPLATE_XML
    folder_template = FOLDER_TEMPLATE_XML
    file_template = FILE_TEMPLATE_XML

    file_ignore_list = [patch_exe_name, patch_exe_name[:-4] + '_boxed.exe']
    file_needed_list = [f'diff_folder_{MAGIC_NUMBER}']


    INPUT_RE = '<!-- inject: inputExe -->'
    OUTPUT_RE = '<!-- inject: outputExe -->'
    FOLDER_NAME_RE = '<!-- inject: folderName -->'
    FILES_RE = '<!-- inject: files -->'
    FILENAME_RE = '<!-- inject: fileName -->' 
    FILEPATH_RE = '<!-- inject: filePath -->'

    def generate_file_tree_xml(depth, root_path, file_ignore_list, file_needed_list):
        parts = []
        for entry in os.listdir(root_path):
            full_path = os.path.join(root_path, entry)

            if (len(file_ignore_list) > 0) and (entry in file_ignore_list):
                continue
            if (len(file_needed_list) > 0) and (entry not in file_needed_list) and depth == 0:
                continue

            if os.path.isdir(full_path):
                part = folder_template.replace(FOLDER_NAME_RE, entry)
                file_xml = generate_file_tree_xml(depth + 1, full_path, file_ignore_list, file_needed_list)
                part = part.replace(FILES_RE, file_xml)
            else:
                part = file_template.replace(FILENAME_RE, entry)
                part = part.replace(FILEPATH_RE, full_path)
            parts.append(part)
        return ''.join(parts)

    input_folder_path_abs = os.path.dirname(input_path_abs)
    output_folder_path_abs = os.path.dirname(output_path_abs)

    project_xml = project_template.replace(INPUT_RE, input_path_abs)
    project_xml = project_xml.replace(OUTPUT_RE, output_path_abs)

    file_tree_xml = generate_file_tree_xml(0, input_folder_path_abs, file_ignore_list, [])

    # if the output folder path is not the same as the input folder path, the diff files in the output folder should
    # also be included.
    if input_folder_path_abs != output_folder_path_abs:
        file_tree_xml += generate_file_tree_xml(0, output_folder_path_abs, [], file_needed_list)
    project_xml = project_xml.replace(FILES_RE, file_tree_xml)

    evb_path = os.path.join(output_folder_path_abs, project_name)
    with open(evb_path, 'w', encoding='utf-8') as f_evb:
        f_evb.write(project_xml)
    
    return evb_path


if __name__ == '__main__':
    original_cwd = os.getcwd()

    parser = argparse.ArgumentParser()
    parser.add_argument('--evb', required=True, help='path to the folder containing enigmavbconsole.exe')
    parser.add_argument('-i', '--input', required=True, help='path to the patch executable (note that it\'s not the path to the folder. The name of the patch executable should also be specified), e.g., /a/b/c/patch.exe')
    parser.add_argument('--old', required=True, help='path to the folder containing the original (pre-patch) files')
    parser.add_argument('--new', required=True, help='path to the folder containing the updated (post-patch) files')
    parser.add_argument('-o', '--output', help='output folder for the patch executable. If not specified, the packaged executable will be generated in the same folder where the original patch executable is located (as specified by the parameter -i/--input)')
    parser.add_argument('--info', help='path to the information file for this patch. The file must be UTF-8 encoded and contain only two lines: the version number on the first line, and the patch notes on the second.')
    try:
        args = parser.parse_args()
    except BaseException as e:
        sys.exit(0)
    
    input_path = args.input
    if args.output is None:
        output_folder_path = os.path.dirname(input_path)
    else:
        output_folder_path = args.output
    
    patch_version = ''
    patch_notes = ''
    # load infomation file if specified
    try:
        if args.info is not None:
            with open(args.info, 'r', encoding='utf8') as f_info:
                patch_version = f_info.readline().strip()
                patch_notes = f_info.readline().strip()
    except:
        print(f'patch infomation file specified but not found. File path is {args.info}')
        sys.exit(0)
    
    # Step 1: generate diff files into diff folder
    # 1.1 create diff folder 
    diff_root_folder_name = f'diff_folder_{MAGIC_NUMBER}'
    diff_root_folder_path = os.path.join(output_folder_path, diff_root_folder_name)
    try:
        os.mkdir(diff_root_folder_path)
    except FileExistsError:
        print(f'temporary folder "{diff_root_folder_name}" creation failed: folder already exists. Remove the folder and try again.')
        sys.exit(0)
    except PermissionError:
        print(f'temporary folder "{diff_root_folder_name}" creation failed: permission denied. Try running this program using administrator priviledge.')
        sys.exit(0)
    except Exception as e:
        print(f'temporary folder "{diff_root_folder_name}" creation failed: error {e}.')
        sys.exit(0)

    try:
        # 1.2 generate patch target file list
        os.chdir(args.old)
        patch_target_list = []
        for root, dirs, files in os.walk('.'):
            clean_root = os.path.relpath(root, '.')
            for file in files:
                patch_target_list.append(os.path.join(clean_root, file))
        os.chdir(original_cwd)

        print(f'Start geneating diff files {len(patch_target_list)} in total.')
        patch_target_list.sort()

        # 1.3 the actual diff-generating procedure
        file_index = 0
        with open(os.path.join(diff_root_folder_path, 'file_metas.txt'), 'w', encoding='utf8') as f_meta:
            f_meta.write(f'{patch_version}\n') # Version number
            f_meta.write(f'{patch_notes}\n') # Patch notes
            f_meta.write('file_index filepath md5_original md5_cnlized size_original size_cnlized\n')
            for target in patch_target_list:
                old_filepath = os.path.join(args.old, target)
                new_filepath = os.path.join(args.new, target)
                if not os.path.exists(new_filepath):
                    print(f'patch target file {target} not found in the post-patch directory')
                    raise FileExistsError()
                old_md5, new_md5, old_size, new_size, diff_cnt = generate_diff(file_index, old_filepath, new_filepath, diff_root_folder_path)
                f_meta.write(f'{file_index}|{target}|{old_md5}|{new_md5}|{old_size}|{new_size}\n')
                print(f'{diff_cnt} diff shard(s) generated for file {file_index} ("{target}").')
                file_index += 1
    
        # Step 2: package the patch executable
        # 2.1 generate the evb file
        print('Start generating evb file.')

        patch_exe_name = os.path.basename(input_path)
        output_exe_name = patch_exe_name[:-4] + '_boxed.exe' #[:-4]: remove the .exe part
        output_path = os.path.join(output_folder_path, output_exe_name)

        input_path_abs = os.path.abspath(input_path)
        output_path_abs = os.path.abspath(output_path)
        evb_path = generate_evb(input_path_abs, output_path_abs)
        print('evb file generated.')

        # execute packaging
        print('Start packaging.')
        evb_exec_path = os.path.join(args.evb, 'enigmavbconsole.exe')
        error_code = subprocess.run([
            evb_exec_path,
            evb_path,
            '-input', input_path_abs,
            '-output', output_path_abs,
        ], check=True)
        print('Packaging complete!')
        print('Everything done!')
    except subprocess.CalledProcessError as e:
        print('Packaging failed. Check output of enigmavbconsole.exe for details.')
    finally:
        # delete diff folder
        shutil.rmtree(diff_root_folder_path)
        # delete evb
        os.remove(evb_path)