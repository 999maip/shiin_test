import os
import hashlib
from config import *

# param[in] filepaths game file paths
# param[in] out output folder names
def generate_patch(filepaths, out):
    CHUNK_SIZE = 8192 * 16
    filenames = [os.path.split(filepath)[1] for filepath in filepaths]

    f_meta = open(PATCH_DIR + '/file_metas.txt', 'w', encoding='utf8')
    f_meta.write('filename filename_short md5_origin md5_cnlized size_origin size_cnlized\n')

    for i in range(len(out)):
        dir = PATCH_DIR + '/' + out[i] + '_o/'
        if not os.path.exists(dir):
            os.makedirs(dir)
        for f in os.listdir(dir):
            os.remove(os.path.join(dir, f))

        dir = PATCH_DIR + '/' + out[i] + '_n/'
        if not os.path.exists(dir):
            os.makedirs(dir)
        for f in os.listdir(dir):
            os.remove(os.path.join(dir, f))

        f_ori = open(PATCH_DIR + '/' + filenames[i] + '.old', 'rb')
        f_new = open(PATCH_DIR + '/' + filenames[i] + '.new', 'rb')

        md5_ori = hashlib.md5()
        md5_new = hashlib.md5()
        size_ori = 0
        size_new = 0

        diff_cnt = 0
        addr = 0
        while True:
            old = f_ori.read(CHUNK_SIZE)
            new = f_new.read(CHUNK_SIZE)
            if (not old and not new) or (len(old) == 0 and len(new) == 0):
                break
            if old:
                md5_ori.update(old)
                size_ori = size_ori + len(old)
            if new:
                md5_new.update(new)
                size_new = size_new + len(new)
            if old != new:
                diff_cnt = diff_cnt + 1
                po = open(PATCH_DIR + '/' + out[i] + '_o/' + str(addr) + '.patch', 'wb')
                po.write(old)
                po.close()
                no = open(PATCH_DIR + '/' + out[i] + '_n/' + str(addr) + '.patch', 'wb')
                no.write(new)
                no.close()
            addr = addr + CHUNK_SIZE

        meta = [filepaths[i], out[i], md5_ori.hexdigest(), md5_new.hexdigest(), format(size_ori, 'x'), format(size_new, 'x')]
        f_meta.write(' '.join(meta) + '\n')
        print(diff_cnt)

        f_ori.close()
        f_new.close()

    f_meta.close()