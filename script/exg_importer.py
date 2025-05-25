import sys
import zipfile
from PIL import Image, ImageFont, ImageDraw
from zipfile import ZipFile
import io

# convert png data to .exg data
def png_to_exg(png, old_exg):
    exg = bytearray()
    exg.extend(old_exg[:0x28])

    png = Image.open(io.BytesIO(png))
    png_pixel_data = list(png.getdata())
    for i in range(0, len(png_pixel_data)):
            r, g, b, a = png_pixel_data[i]
            exg.append(b)
            exg.append(g)
            exg.append(r)
            exg.append(a)
    if len(exg) < len(old_exg):
        exg.extend(old_exg[len(exg):])
    return exg

def main():
    png_filename = 'graphic_comtex_comtex_exg.png'
    zip_filename =  'graphic_comtex_comtex_exg.zip'
    if len(sys.argv) >= 3:
        zip_filename = sys.argv[1]
        png_filename = sys.argv[2]

    with ZipFile(zip_filename, 'r') as zip_file:
        exg_filename = zip_file.namelist()[0]
        old_exg = zip_file.open(exg_filename).read()

    with open(png_filename, 'rb') as png_file:
        new_png = png_file.read()
    
    with ZipFile(zip_filename[:-4] + '.new.zip', 'w', zipfile.ZIP_DEFLATED) as new_zip_file:
        new_zip_file.writestr(exg_filename, png_to_exg(new_png, old_exg))

if __name__ == '__main__':
    main()