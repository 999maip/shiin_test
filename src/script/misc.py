# the following code snippets are only left for reference.
def old_debug_codes():
    pass
    # img = Image.open('gt.png')
    # new_img = img.crop((150, 100, img.width, img.height))
    # new_img_2 = img.crop((430, 100, img.width, img.height))
    # new_img_3 = img.crop((710, 100, img.width, img.height))
    # images = []
    # for i in range(30):
    #     final1 = Image.new("RGBA", img.size)
    #     final1.paste(new_img_2, (random.randint(-1,1), random.randint(-1,1)), new_img_2)
    #     final1.paste(new_img_3, (random.randint(-1,1), random.randint(-1,1)), new_img_3)
    #     final1.paste(new_img, (0, 0), new_img)
    #     images.append(final1)
    #     # final1.show()

    # images[0].save('title.gif',
    #            save_all=True, disposal=0,append_images=images[1:], optimize=False, duration=100, loop=0)
    # event script processing sample
    # fin = open('event_script.dat', 'rb')
    # data = fin.read()
    # fin.close()
    # scripts = dat_to_scripts(data)
    # for script_id, data in scripts.items():
    #     fout = open('output_data/%d.dat' % script_id, 'wb')
    #     fout.write(data)
    #     fout.close()
    # dir_path = "output_data"
    # files = os.listdir(dir_path)
    # files.sort()
    # scripts = dict()
    # for file in files:
    #     if not file.endswith('dat'):
    #         continue
    #     script_id = int(file.split('.')[0])
    #     fin = open(dir_path + '/' + file, 'rb')
    #     scripts[script_id] = fin.read()
    #     fin.close()
    
    # event_mazeevent script processing sample
    # fin = open('event_mazeevent.dat', 'rb')
    # data = fin.read()
    # fin.close()
    # scripts = dat_to_scripts(data)
    # for script_id, data in scripts.items():
    #     fout = open('output_csv_maze/%d.dat.txt' % script_id, 'w', encoding='utf-8')
    #     for uid, txt in script_to_txts('maze', script_id, data).items():
    #         fout.write(uid + ',' + txt + '\n')
    #     fout.close()