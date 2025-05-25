import os
import hashlib
from config import *

def md5sum(file_path, block_size=65536):
    """计算文件的 MD5 值"""
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(block_size), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def compare_dirs(dir1, dir2):
    """比较两个目录中同名文件的 MD5"""
    files1 = set(os.listdir(dir1))
    files2 = set(os.listdir(dir2))

    common_files = files1 & files2  # 取交集，得到同名文件

    for filename in sorted(common_files):
        path1 = os.path.join(dir1, filename)
        path2 = os.path.join(dir2, filename)

        # 只对文件进行比较
        if os.path.isfile(path1) and os.path.isfile(path2):
            md5_1 = md5sum(path1)
            md5_2 = md5sum(path2)

            if md5_1 != md5_2:
                print(f"Different: {filename}")

def compare_files_bytewise(file1, file2):
    """比较两个文件，返回第一个不同字节的偏移位置"""
    with open(file1, 'rb') as f1, open(file2, 'rb') as f2:
        offset = 0
        while True:
            b1 = f1.read(1)
            b2 = f2.read(1)

            if not b1 and not b2:
                print("Files are identical.")
                return None

            if b1 != b2:
                print(f"Difference found at byte offset {offset}, {b1}, {b2}")
                return offset

            offset += 1

if __name__ == "__main__":
    dir1 = "output_tablepack"  # ← 替换成你的第一个目录
    dir2 = "output_tablepack_debug"  # ← 替换成你的第二个目录
    compare_dirs(dir1, dir2)
    # compare_files_bytewise('output_tablepack/4.dat', 'output_tablepack_debug/4.dat')