from PIL import Image, ImageDraw
import unicodedata

code_table = [
0xDC, 0xE6, 0x72, 0x8F, 0xF4, 0x1E, 0xC9, 0x87, 0x36, 0xD4, 0x81, 0xF2, 0x92, 0xD3, 0xCE, 0xAF,
0x52, 0xF6, 0x5C, 0xC4, 0x22, 0xBC, 0x27, 0xFB, 0x97, 0xC2, 0xED, 0xCC, 0xB8, 0x65, 0xB0, 0x79,
0x7F, 0x57, 0x07, 0x3A, 0x0E, 0x5A, 0xB7, 0x02, 0xD9, 0xD8, 0x5D, 0x9D, 0x56, 0xDF, 0x49, 0xAA,
0x2C, 0xE0, 0xDD, 0x00, 0x1A, 0x94, 0x93, 0x29, 0x59, 0xD6, 0x7A, 0x31, 0xFC, 0x3D, 0xBD, 0x41,
0x11, 0x80, 0xDE, 0x60, 0xB4, 0x3B, 0x69, 0x06, 0x6C, 0x61, 0xA1, 0x7E, 0xFA, 0x6E, 0xD1, 0xAB,
0xA2, 0x1F, 0x39, 0x83, 0xEB, 0x66, 0x2A, 0x76, 0xCD, 0xF9, 0x3F, 0x98, 0x99, 0xE5, 0xE9, 0xE7,
0x45, 0xA0, 0x85, 0x42, 0x10, 0xB6, 0x50, 0xBA, 0xFD, 0x62, 0x96, 0x14, 0x6B, 0x47, 0x15, 0xC6,
0x18, 0xA8, 0x32, 0xAD, 0x3E, 0x9C, 0x5B, 0x0D, 0x19, 0x35, 0xD7, 0xC7, 0xA9, 0x68, 0x40, 0x13,
0x75, 0x1C, 0x0F, 0x26, 0xC5, 0xDB, 0xCF, 0x53, 0x6D, 0x4E, 0xAE, 0xA7, 0x7B, 0x4B, 0x0B, 0xE3,
0x54, 0xC3, 0x3C, 0xAC, 0xB1, 0x90, 0x8E, 0xD5, 0x2E, 0x0A, 0x82, 0xB5, 0x63, 0xEF, 0xBB, 0x7D,
0x5F, 0x04, 0x73, 0xF8, 0x9B, 0xFE, 0x51, 0x21, 0xA4, 0x8D, 0x37, 0xB3, 0x17, 0x5E, 0x67, 0x77,
0xB2, 0x05, 0x7C, 0x25, 0xF0, 0x20, 0x23, 0x9A, 0x91, 0xC1, 0x9E, 0x24, 0xF5, 0xBE, 0x0C, 0xF1,
0x16, 0xA3, 0xD0, 0x4C, 0xE8, 0x28, 0xA6, 0xEE, 0x2D, 0x2B, 0x86, 0x44, 0x89, 0x2F, 0x70, 0xCA,
0x4D, 0xC8, 0x71, 0xBF, 0x46, 0xEA, 0xD2, 0x12, 0x4A, 0x88, 0x8B, 0xE4, 0x38, 0xC0, 0xF7, 0xA5,
0x58, 0x9F, 0x84, 0xEC, 0x55, 0xF3, 0x33, 0x09, 0xE2, 0x8C, 0x74, 0x6A, 0xFF, 0x08, 0x30, 0x1D,
0x78, 0x43, 0x48, 0x4F, 0x34, 0xE1, 0x95, 0xDA, 0xB9, 0x1B, 0x64, 0x8A, 0x01, 0xCB, 0x03, 0x6F]

# data为压缩数据,code_size为压缩后的数据处理次数,size_raw为解压后数据大小
# optimized version
def decompress_new(data, code_size, size_raw: int):
    result = bytearray(size_raw)
    result_cursor = 0
    if code_size <= 0:
        for i in range(size_raw):
            result[i] = data[i]
        return result
    else:
        flag_cursor = 0
        data_cursor = 2
        flag = 0
        for count in range(code_size):
            # 从前两个字节中的flag位判断从result里复制数据还是从码表赋值
            if ((1 << flag) & int.from_bytes(data[flag_cursor:flag_cursor + 2], 'little')) != 0:

                # 如果为1，读取数据second_cursor位置的两个字节，前9位存储偏移量
                copy_start_cursor = (-2 * (int.from_bytes(data[data_cursor:data_cursor + 2], 'little') >> 7) +
                                     result_cursor)

                # second_cursor位置后7位存储重复的长度
                length = int.from_bytes(data[data_cursor:data_cursor + 2], 'little') & 0x7F
                for _ in range(length):
                    first_byte = result[copy_start_cursor]
                    second_byte = result[copy_start_cursor + 1]
                    copy_start_cursor += 2
                    result[result_cursor] = first_byte
                    result[result_cursor + 1] = second_byte
                    # 更新result_cursor
                    result_cursor += 2
            # flag为0，从码表获取数据
            else:
                # 读取second_cursor位置的数据作为索引找到码表，换句话说second_cursor位置存储了对应码表的索引
                result[result_cursor] = code_table[data[data_cursor]]
                result[result_cursor + 1] = code_table[data[data_cursor + 1]]
                # 更新result_cursor
                result_cursor += 2
            data_cursor += 2
            # 更新flag
            flag = (count + 1) & 0xF
            if flag == 0:
                # 更新标记指针flag_cursor
                flag_cursor = data_cursor
                data_cursor = data_cursor + 2
    return result

def decompress(data, code_size, size_raw: int):
    a1 = -8
    result = bytearray(size_raw)
    result_offset = 0
    v10 = code_size

    if v10 <= 0:
        for i in range(size_raw):
            result[i] = data[i]
    else:
        v3 = 0
        v4 = a1 + 8
        v5 = a1 + 10
        # v11 = 0
        # v12 = a1 + 8
        v6 = 0
        while True:
            if ((1 << v6) & int.from_bytes(data[v4:v4+2], 'little')) != 0:
                v7 = -2 * (int.from_bytes(data[v5:v5+2], 'little') >> 7) + result_offset
                v8 = int.from_bytes(data[v5:v5+2], 'little') & 0x7F
                while v8 != 0:
                    v91 = result[v7]
                    v92 = result[v7 + 1]
                    v7 += 2
                    result[result_offset] = v91
                    result[result_offset+1] = v92
                    result_offset += 2
                    v8 = v8 - 1
                # v4 = v12
            else:
                # v3 = v11
                result[result_offset] = code_table[data[v5]]
                result[result_offset+1] = code_table[data[v5+1]]
                result_offset += 2
            v3 += 1
            v5 += 2
            # v11 = v3
            v6 = v3 & 0xF
            if (v3 & 0xF) == 0:
                v4 = v5
                v5 = v5 + 2
                # v12 = v4
            if v3 >= v10:
                break
    return result

def uid(prefix, script_id, line_id):
    script_id_base = 0x1000000
    return prefix + '_' + format(script_id - script_id_base, '05x') + '_' + format(line_id, '08x')

def dat_to_scripts(data):
    offset = 0
    scripts = dict()
    while offset < len(data):
        script_id = int.from_bytes(data[offset:offset+4], 'little')
        script_size_compressed = int.from_bytes(data[offset+4:offset+8], 'little', signed=True)
        script_data = data[offset+16:offset+8+script_size_compressed]
        script_size_compressed = (script_size_compressed + 3) & 0xFFFFFFFC # 4-byte alignment
        script_size_raw = int.from_bytes(data[offset+8:offset+12], 'little', signed=True)
        script_code_size = int.from_bytes(data[offset+12:offset+16], 'little', signed=True)

        if script_size_raw != 0:
            scripts[script_id] = decompress(script_data, script_code_size, script_size_raw)
        offset += 8 + script_size_compressed

    return scripts


def compress(data):
    if len(data) <= 2:
        return data
    window = 1 << 10
    lookahead = 1 << 8
    data_cursor = 0
    count = 0
    flag_index = 0
    flag = 0
    result = bytearray()
    while data_cursor < len(data):
        # flag存储判断信息,每16次添加2个占位字节,并更新该占位字节的索引
        if count & 0xF == 0:
            result.append(0)
            result.append(0)
            flag_index = len(result) - 2
            flag = 0
        # 小于窗口长度,从数据头开始匹配字节串,否则从数据窗口起点开始匹配
        start_index = 0 if data_cursor <= window else data_cursor - window
        match_result = match(data[start_index: data_cursor], data[data_cursor: data_cursor + lookahead])
        # 若匹配字节串为0,没有匹配到,获取索引
        if match_result[1] <= 0 or match_result[0] <= 0:
            result.append(code_table.index(data[data_cursor]))
            result.append(code_table.index(data[data_cursor + 1]))
            data_cursor += 2
        # 若匹配到了,直接存储复制信息
        else:
            # 计算出偏移量,数据指针绝对位置减去开始复制时的绝对位置
            offset = (data_cursor - match_result[0] - start_index) << 6
            # 计算出长度
            length = match_result[1] >> 1
            message = offset | length
            result.append(message & 0xFF)
            result.append((message >> 8) & 0xFF)
            # 移动指针到匹配好的位置
            data_cursor += match_result[1]
            # 标记位为1
            flag = (1 << (count & 0xF)) | flag
        count += 1
        # 更新flag
        result[flag_index] = flag & 0xFF
        result[flag_index + 1] = (flag >> 8) & 0xFF
    return result


def match(window_data, lookahead_data):
    index = 0
    max_length = 0
    window_cursor = 0
    lookahead_cursor = 0
    if len(window_data) < 2 or len(lookahead_data) < 2:
        # 数组第一位为索引，第二为长度
        return [0, 0]
    while window_cursor < len(window_data):
        # print(window_data[0])
        # 判断当前先行缓存区的字节串是否与滑动窗口的字节串匹配,搜索距离最近的最大子串
        if window_data[window_cursor: window_cursor + 2] == lookahead_data[lookahead_cursor: lookahead_cursor + 2]:
            lookahead_cursor += 2
            if lookahead_cursor >= max_length:
                max_length = lookahead_cursor
                index = window_cursor - max_length + 2
        else:
            lookahead_cursor = 0
        window_cursor += 2
    return [index, max_length]


# 获取压缩数据解压时需要的迭代次数code_size
def get_code_size(data):
    return (len(data) // 34) * 16 + (len(data) % 34 - 2) // 2


# 只映射code_table,不进行压缩,可以保证解压后数据不会出错,但会导致文件变大,备选方案
def compress_dummy(data):
    if len(data) <= 2:
        return data
    count = 0
    data_cursor = 0
    result = bytearray()
    while data_cursor < len(data):
        if count & 0xF == 0:
            result.append(0)
            result.append(0)
        result.append(code_table.index(data[data_cursor]))
        result.append(code_table.index(data[data_cursor + 1]))
        data_cursor += 2
        count += 1
    return result


# 打包成dat文件,包含压缩过程,将字典里的数据压缩成可输出的字节串
# 传入scripts字典,key为script_id,value为txt_to_script的返回值
def scripts_to_dat(scripts: dict):
    result = bytearray()
    for script_id, data in scripts.items():
        # 压缩
        compress_data = compress(data)
        length = len(compress_data)
        if len(compress_data) % 4 != 0:
            compress_data.extend([0, 0])
        # 文件id
        result.extend(script_id.to_bytes(4, 'little'))
        # 压缩后文件大小
        result.extend((length + 8).to_bytes(4, 'little'))
        # 原数据大小
        result.extend(len(data).to_bytes(4, 'little'))
        # 迭代次数
        result.extend(get_code_size(compress_data).to_bytes(4, 'little'))
        result.extend(compress_data)

    return result


def script_to_txts(prefix, script_id, data):
    offset = 0
    txts = dict()
    while offset < len(data):
        line_id = int.from_bytes(data[offset:offset+4], 'little')
        size = int.from_bytes(data[offset+4:offset+8], 'little')
        text_str = '<binary data>'
        if size > 0:
            try:
                # remove trailing 0x00s
                idx = offset+8+size-1
                while data[idx] == 0 and idx >= offset + 8:
                    idx = idx - 1

                text_str = data[offset+8:idx+1].decode(encoding='sjis')

                if len(data[offset+8:idx+1]) == 1:
                    text_str = '<binary data>'
                elif any(unicodedata.category(char) == 'Cc' for char in text_str):
                    text_str = '<binary data>'
                elif all(ord(char) <= 0xff for char in text_str):
                    text_str = '<binary data>'

            except Exception:
                pass
        if text_str != '<binary data>':
            # extra filter:

            txts[uid(prefix, script_id, line_id)] = text_str

        offset = offset + 8 + size
    return txts

class Glyph:
    glyph = bytearray()
    width = 0
    height = 0
    offsetx = 0
    offsety = 0

# @param char_sjis shift-jis encoding of character(2 bytes)
def exp_to_glyph(data, char_sjis):
    canvas = bytearray()
    # 4-byte EXF1
    if data[:4].decode('ascii') != 'EXF1':
        print('Invalid font data')
        return canvas
    image_height = data[4]
    image_width = data[5]

    canvas = bytearray(image_width * image_height)

    image_width2 = data[6] # for alphabet glyphs maybe; almost useless, can be ignored
    height_padding = data[7] # no working? almost useless, can be ignored
    width_padding = data[8]
    char_table_size = int.from_bytes(data[10:12], 'little') + 1

    # index table consists of 4-bytes offsets relative to 'glyph_table_offset'
    index_table_size = char_table_size * 4
    index_table_offset = 0x10
    glyph_table_offset = index_table_size + index_table_offset # 0x3f140 for fontdata_fontdata01.exp

    index = int.from_bytes(data[char_sjis * 4 + index_table_offset:char_sjis * 4 + index_table_offset + 4], 'little')
    glyph_offset = glyph_table_offset + index
    glyph_size = int.from_bytes(data[glyph_offset:glyph_offset+2], 'little')
    glyph_width = data[glyph_offset + 2]
    glyph_height = data[glyph_offset + 3]
    # glyph_size == glyph_width * glyph_height
    glyph_bearingx = data[glyph_offset + 4] # bearing or just offset?
    glyph_bearingy = data[glyph_offset + 5] # bearing or just offset?

    glyph = data[glyph_offset+6:glyph_offset+6+glyph_size]

    glyph_obj = Glyph()
    glyph_obj.glyph = glyph
    glyph_obj.width = glyph_width
    glyph_obj.height = glyph_height
    glyph_obj.offsetx = glyph_bearingx
    glyph_obj.offsety = glyph_bearingy

    return glyph_obj

# used for test only
def glyph_to_img(glyph_obj: Glyph):
    # a 60*60 canvas
    print(glyph_obj.height, glyph_obj.width)
    img = Image.new("RGB", (60, 60))
    for i in range(glyph_obj.height):
        for j in range(glyph_obj.width):
            gray_scale = glyph_obj.glyph[i*glyph_obj.width + j]
            img.putpixel((j+glyph_obj.offsetx, i+glyph_obj.offsety), (gray_scale, gray_scale, gray_scale))
    
    return img
    


def main():
    # script processing sample
    fin = open('event_script.dat', 'rb')
    data = fin.read()
    fin.close()
    scripts = dat_to_scripts(data)
    for script_id, data in scripts.items():
        fout = open('output_data/%d.dat' % script_id, 'wb')
        fout.write(data)
        fout.close()

    # font processing sample
    # fin = open('fontdata_fontdata01.exp', 'rb')
    # data = fin.read()
    # glyph_obj = exp_to_glyph(data, 0x82a6) # ぇ
    # img = glyph_to_img(glyph_obj)
    # img.save('output_font/test_glpyh.png')
    # fin.close()

if __name__ == '__main__':
    main()