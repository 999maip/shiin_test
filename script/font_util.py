from PIL import Image, ImageFont, ImageDraw
import unicodedata

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
    height_padding = data[7] # not used? almost useless, can be ignored
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

def reimport_font_data(jp_font_data):
    # test
    glyph_table = generate_cn_glyphs()
    cn_font_data = bytearray()
    cn_font_data.extend(jp_font_data[:0x3f1CA])
    char_table_size = int.from_bytes(jp_font_data[10:12], 'little') + 1

    # 0x3f140-0x3f1CA(0x3f140 + 0x8A) is space glyph?
    glyph_offset = 0x8A
    for i in range (char_table_size):

        if int.from_bytes(cn_font_data[0x10+i*4:0x10+(i+1)*4], 'little') == 0:
            continue
        try:
            char = chr(i)
            if i >= 0x7f:
                char = i.to_bytes(2, 'big').decode('sjis')
            glyph_obj = glyph_table[char]
        except Exception:
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

def font_test():
    img = Image.new("RGB", (500, 70))
    draw = ImageDraw.Draw(img)

    # use a truetype font
    font = ImageFont.truetype("arshanghaisonggbpro_lt.otf", 35)
    bitmap = font.getmask('，')
    bitmap_image = Image.frombytes(bitmap.mode, bitmap.size, bytes(bitmap))


    # draw.text((10, 25), "文字测试文字测试", font=font)
    draw.text((0, 0), "，", font=font)
    bbox = draw.textbbox((0, 0), "，", font=font)
    draw.rectangle(bbox, outline="red")
    img.save('output_font/test_glpyh_huiwen.png')

def gen_char_table():
    table = dict()

    fdefault = open('resource/default_char_table.txt', encoding='utf8')
    for line in fdefault:
        line = line.strip()
        for ch in line:
            table[ch] = 1

    fdefault.close()

    fscript = open('translation_files/chapter4.csv', encoding='utf8')
    for line in fscript:
        line = line.strip()
        for ch in line:
            table[ch] = 1

    fdefault.close()

    fout = open('resource/char_table.txt', 'w', encoding='utf8')

    print('%d characters.' % len(table))

    for ch in table:
        fout.write(ch)

    fout.close()

def generate_char_mapping():
    cn_char_table = dict()
    mapping = dict()
    jp_char_table = dict()

    ftable = open('resource/char_table.txt', 'r', encoding='utf8')
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
        for jp_char, v in jp_char_table.items():
            # used
            if v == 2:
                continue
            mapping[cn_char] = jp_char
            jp_char_table[jp_char] = 2
            break
        cn_char_table[cn_char] = 2

    fmapping = open('resource/char_mapping.txt', 'w', encoding='utf-8')
    for chr, mapped in mapping.items():
        fmapping.write(chr)
        fmapping.write(' ')
        fmapping.write(mapped)
        fmapping.write('\n')
    fmapping.close()

def generate_cn_glyphs():
    font = ImageFont.truetype("arshanghaisonggbpro_lt.otf", 40)
    glyph_table = dict()
    ftable = open('resource/char_mapping.txt', 'r', encoding='utf8')

    for line in ftable:
        line = line.strip()
        if len(line) == 0:
            continue
        cn_char = line[0]
        jp_char = line[2]
        # if cn_char != '，' and cn_char != '我':
        bitmap = font.getmask(cn_char)
        bbox = font.getbbox(cn_char)
        glyph_obj = Glyph()
        glyph_obj.glyph = bytes(bitmap)
        glyph_obj.width = bitmap.size[0]
        glyph_obj.height = bitmap.size[1]
        glyph_obj.offsetx = max(bbox[0], 0)
        glyph_obj.offsety = bbox[1]

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

def txt_to_mapped_txt(text):
    mapping = dict()
    ftable = open('resource/char_mapping.txt', 'r', encoding='utf8')
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
    
    out_text = ''
    for i in range(len(text)):
        out_text = out_text + mapping[text[i]]
    
    # debug log
    # print(out_text)

    return out_text
    


def main():
    # generate_character_mapping()
    # generate_glyphs()
    txt_to_mapped_txt('我们回家前要不要先去唱个歌啊？')

if __name__ == '__main__':
    main()