from PIL import Image

img = Image.open("02.png")
# 转换为合适模式（例如有 alpha 的 RGBA）
img = img.convert("RGBA")
# 保存为 DDS，使用 pixel_format="DXT5"
img.save("02.dds", format="DDS", pixel_format="DXT5")