from PIL import Image, ImageFont, ImageDraw
import os
import csv
from config import *

# About the font file format:
# 0x00: 4 bytes, magic number EXF1
# 4 bytes, font size info. 1 byte: size, 1 byte: size, 1 byte: advance 1 byte: x offset?
# 2 bytes, unknown
# 2 bytes, max glyph unicode index 0xFC4B=64587 0~64587 64588 glyphs
# 2 bytes, zero padding
# 0x10 ~ 0x3f140: 4 bytes * glyph number (64587 + 1 = 64588)
# 0x3f140 ~ : glyph table. (6 bytes glyph meta info + glyph bitmap) for each glyph
# 6 bytes glyph meta: 2-byte bimap size, 1-byte wdith, 1-byte height, 1-byte xoffset, 1-byte yoffset

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

    image_width2 = data[6] # margin/padding for alphabet glyphs
    height_padding = data[7] # not used?
    width_padding = data[8]
    char_table_size = int.from_bytes(data[10:12], 'little') + 1

    # index table consists of 4-bytes offsets relative to 'glyph_table_offset'
    index_table_size = char_table_size * 4
    index_table_offset = 0x10
    glyph_table_offset = index_table_size + index_table_offset # 0x3f140 for fontdata_fontdata01.exp
    print(format(glyph_table_offset, 'x'))

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

def reimport_font_data(jp_font_data, font_size, advance):
    glyph_table = gen_cn_glyphs(font_size)
    cn_font_data = bytearray()
    cn_font_data.extend(jp_font_data[:0x3f140])
    char_table_size = int.from_bytes(jp_font_data[10:12], 'little') + 1
    cn_font_data[0x06] = advance

    # 0x3f140-0x3f1CA(0x3f140 + 0x8A) is the first visible glyph '!'(0x21) for fontdata1(main text font)
    # 0x3f140-0x3f191(0x3f140 + 0x51) is the first visible glyph '!'(0x21) for fontdata1(main text font)
    glyph_offset = 0x00
    for i in range (char_table_size):
        # the glyph offset is 0 for a non-exist glyph, and the very first visible glyph '!'(0x21)
        if i != 0x21 and int.from_bytes(cn_font_data[0x10+i*4:0x10+(i+1)*4], 'little') == 0:
            continue
        try:
            char = chr(i)
            if i >= 0x7f:
                char = i.to_bytes(2, 'big').decode('sjis')
            glyph_obj = glyph_table[char]
        except Exception:
            # use '?' to replace glyphs not found in font file
            glyph_obj = glyph_table['？']
        cn_font_data[0x10+i*4:0x10+(i+1)*4] = glyph_offset.to_bytes(4, 'little')
        cn_font_data.extend(len(glyph_obj.glyph).to_bytes(2, 'little'))
        cn_font_data.extend(glyph_obj.width.to_bytes(1, 'little'))
        cn_font_data.extend(glyph_obj.height.to_bytes(1, 'little'))
        cn_font_data.extend(glyph_obj.offsetx.to_bytes(1, 'little'))
        cn_font_data.extend(glyph_obj.offsety.to_bytes(1, 'little'))
        cn_font_data.extend(glyph_obj.glyph)
        glyph_offset = glyph_offset + 6 + len(glyph_obj.glyph)
    
    return cn_font_data

def gen_char_table(csv_file_list):
    table = dict()

    with open(os.path.join(RESOURCE_DIR, 'default_char_table.txt'), encoding='utf8') as fdefault:
        for line in fdefault:
            line = line.strip()
            for ch in line:
                table[ch] = 1

    for csv_file in csv_file_list:
        try:
            with open(os.path.join(TEXT_DIR, csv_file), encoding='utf8') as fscript:
                csv_reader = csv.reader(fscript)
                for row in csv_reader:
                    line = row[2] # cn
                    if line == '':
                        line = row[1] # untranslated jp

                    for ch in line:
                        table[ch] = 1
        except Exception:
            print('Warning: file %s not found' % csv_file)

    fdefault.close()

    fout = open(RESOURCE_DIR + '/char_table.txt', 'w', encoding='utf8')

    print('%d characters.' % len(table))

    for ch in table:
        fout.write(ch)
    fout.close()

def gen_char_mapping():
    cn_char_table = dict()
    mapping = dict()
    jp_char_table = dict()

    ftable = open(RESOURCE_DIR + '/char_table.txt', 'r', encoding='utf8')
    for line in ftable:
        line = line.strip()
        for ch in line:
            cn_char_table[ch] = 1
    ftable.close()

    for first_byte in range(0x81, 0x9f + 1):
        for second_byte in range(0x40, 0xfc + 1):
            char = bytearray([first_byte, second_byte])
            try:
                jp_char_table[char.decode('sjis')] = 1
            except Exception:
                continue

    print('total cn charaters', len(cn_char_table))
    print('total jp charaters', len(jp_char_table))

    if len(cn_char_table) > len(jp_char_table):
        raise Exception('number of characters not enough')

    for cn_char, v in cn_char_table.items():
        if v == 2:
            continue
        if ord(cn_char) <= 0x7f:
            mapping[cn_char] = cn_char
            cn_char_table[cn_char] = 2

    for cn_char, v in cn_char_table.items():
        if v == 2:
            continue
        if cn_char in jp_char_table:
            mapping[cn_char] = cn_char
            jp_char_table[cn_char] = 2
            cn_char_table[cn_char] = 2

    for cn_char, v in cn_char_table.items():
        # already mapped
        if v == 2:
            continue
        for jp_char, vj in jp_char_table.items():
            # used
            if vj == 2:
                continue
            mapping[cn_char] = jp_char
            jp_char_table[jp_char] = 2
            break
        cn_char_table[cn_char] = 2

    fmapping = open(RESOURCE_DIR + '/char_mapping.txt', 'w', encoding='utf-8')
    for chr, mapped in mapping.items():
        fmapping.write(chr)
        fmapping.write(' ')
        fmapping.write(mapped)
        fmapping.write('\n')
    fmapping.close()

def gen_cn_glyphs(font_size: int):
    font_file_path = os.path.join(RESOURCE_DIR, 'LXGWNeoZhiSong.ttf')
    font = ImageFont.truetype(font_file_path, font_size)
    glyph_table = dict()
    ftable = open(RESOURCE_DIR + '/char_mapping.txt', 'r', encoding='utf8')

    for line in ftable:
        line = line.strip()
        if len(line) == 0:
            continue
        cn_char = line[0]
        jp_char = line[2]
        bitmap = font.getmask(cn_char)

        bbox = font.getbbox(cn_char)
        glyph_obj = Glyph()

        # the game's font glyph is a 4-bit grayscale bitmap
        # and all it's 16 grayscale values are encoded to a 1-byte number.
        gray_scale_mapping = [0x00, 0x86, 0x8d, 0x94, 0x9a, 0xa1, 0xa8, 0xae,
                              0xb5, 0xbc, 0xc2, 0xc9, 0xd0, 0xd6, 0xdd, 0xe4]
        ba_bitmap = bytearray(bytes(bitmap))
        for i in range(len(ba_bitmap)):
            ba_bitmap[i] = gray_scale_mapping[int(ba_bitmap[i] / 16)]

        glyph_obj.glyph = ba_bitmap
        glyph_obj.width = bitmap.size[0]
        glyph_obj.height = bitmap.size[1]
        glyph_obj.offsetx = max(bbox[0], 0)
        glyph_obj.offsety = bbox[1]

        if cn_char == '“':
            glyph_obj.offsetx = 20
        elif cn_char == '‘':
            glyph_obj.offsetx = 30

        glyph_table[jp_char] = glyph_obj
        # print(glyph_obj.height, glyph_obj.width)
        # print(font.getbbox(cn_char))
        # print(font.getlength(cn_char))
        # for i in range(glyph_obj.height):
        #     for j in range(glyph_obj.width):
        #         gray_scale = glyph_obj.glyph[i*glyph_obj.width + j]
        #         img.putpixel((j+glyph_obj.offsetx + int(offset), i+glyph_obj.offsety), (gray_scale, gray_scale, gray_scale))
        # img.save('output_font/test_glpyh_huiwen.png')
    # ftable.close()
    return glyph_table

def load_char_mapping() -> dict:
    mapping = dict()
    with open(os.path.join(RESOURCE_DIR, 'char_mapping.txt'), 'r', encoding='utf8') as ftable:
        mapping['\n'] = '\n'
        mapping[' '] = ' '
        mapping['　'] = '　'
        for line in ftable:
            line = line.strip()
            if len(line) == 0:
                continue
            if line[0] == ' ' or line[0] == '　':
                continue
            cn_char = line[0]
            jp_char = line[2]
            mapping[cn_char] = jp_char
    return mapping

def txt_to_mapped_txt(text, mapping=None):
    if mapping is None:
        mapping = load_char_mapping()
    
    out_text = ''
    for i in range(len(text)):
        out_text = out_text + mapping[text[i]]
    
    return out_text

def main():
    gen_char_table(CSV_FILE_LIST)

    # gen char mapping sample
    gen_char_mapping()

    # txt to mapped txt sample
    # txt_to_mapped_txt('我们回家前要不要先去唱个歌啊？')

    # font processing sample
    # fin = open('fontdata_fontdata01.exp', 'rb')
    # data = fin.read()
    # # glyph_obj = exp_to_glyph(data, 0x82a6) # ぇ
    # # glyph_obj = exp_to_glyph(data, 0x4F) # ぇ
    # img = glyph_to_img(glyph_obj)
    # img.save('output_font/test_glpyh.png')
    # fin.close()

    # font file generation sample
    gen_cn_font()

if __name__ == '__main__':
    # main()
    os.system('copy "generated\\fontdata_fontdata01_cn.exp" "D:\\SteamLibrary\\steamapps\\common\\Death Mark\\resource\\fontdata_fontdata01.exp"')
    # image = Image.new("RGB", (300, 300))
    # font = ImageFont.truetype("resource/LXGWNeoZhiSong.ttf", 40)
    # draw = ImageDraw.Draw(image)
    # draw.text((0, 0), "埃", font=font)

    # image = ImageOps.grayscale(image)

    # image.show()

    # font processing sample
    # fin = open('fontdata_fontdata01_cn.exp', 'rb')
    # data = fin.read()
    # glyph_obj = exp_to_glyph(data, 0x978e) # ぇ
    # # glyph_obj = exp_to_glyph(data, 0x4F) # ぇ
    # img = glyph_to_img(glyph_obj)
    # img.save('test_glpyh2.png')
    # fin.close()

# debug functions
# used for debug only
def glyph_to_img(glyph_obj: Glyph):
    maxv = 0
    # a 60*60 canvas
    print(glyph_obj.height, glyph_obj.width)
    img = Image.new("RGB", (60, 60))
    for i in range(glyph_obj.height):
        for j in range(glyph_obj.width):
            gray_scale = glyph_obj.glyph[i*glyph_obj.width + j]
            if gray_scale > maxv:
                maxv = gray_scale
            img.putpixel((j+glyph_obj.offsetx, i+glyph_obj.offsety), (gray_scale, gray_scale, gray_scale))
    
    print(maxv)
    return img

def font_test():
    img = Image.new("RGB", (500, 70))
    draw = ImageDraw.Draw(img)

    # use a truetype font
    font = ImageFont.truetype(RESOURCE_DIR + '/arshanghaisonggbpro_lt.otf', 35)
    bitmap = font.getmask('，')
    bitmap_image = Image.frombytes(bitmap.mode, bitmap.size, bytes(bitmap))


    # draw.text((10, 25), "文字测试文字测试", font=font)
    draw.text((0, 0), "，", font=font)
    bbox = draw.textbbox((0, 0), "，", font=font)
    draw.rectangle(bbox, outline="red")
    img.save('output_font/test_glpyh_huiwen.png')