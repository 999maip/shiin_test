def reflow_text(text: str, width: int) -> str:
    """
        Remove all line breaks, then insert a line break every `width` characters.
        If the new line would start with a disallowed Chinese punctuation mark,
        move the last character of the previous line to the next line.
    """
        # Define Chinese punctuation marks that cannot appear at the beginning of a line
    bad_start_punct = "，。！？；：、)]】』〉》"

    # Remove original line breaks
    text = text.replace("\r\n", "")
    text = text.replace("\n", "")

    result_lines = []
    i = 0
    while i < len(text):
        # Take `width` characters
        line = text[i:i+width]

        # If the next line would start with a disallowed punctuation mark
        if i + width < len(text) and text[i+width] in bad_start_punct:
            # Move the last character of the current line to the next line
            line = line[:-1]
            i += width - 1
        else:
            i += width

        result_lines.append(line)

    result = "\n".join(result_lines)
    print(result)
    return result


# Example
s = '''从九条馆的大厅内拿出来的
纯银制的裁纸刀。
刀柄上雕刻着美丽女性的面孔。
虽然没有经过锋利的打磨，
但还是可以切开柔软的纸张。'''
s = '''在防空洞发现的锤子。
铁制的锤头上有疑似血迹的红黑色
污痕，可见其用于原本的用途之外。'''
s='''在防空洞内发现的笔记本。
笔记本上到处都是散发出异样气味的污痕，
难以辨认上面的内容。
在没有污痕的页面上，
写满了异常细小的文字。'''
reflow_text(s, 12)