SCRIPT_ID_BASE = 0x1000000

def uid(prefix, script_id, line_id):
    return prefix + '_' + format(script_id - SCRIPT_ID_BASE, '05x') + '_' + format(line_id, '08x')

def split_uid(uid: str):
    try:
        if uid[0] == '"':
            uid = uid[1:]
        if uid[-1] == '"':
            uid = uid[:-1]
        prefix, script_id, line_id = uid.split('_')
        script_id = int(script_id, 16) + SCRIPT_ID_BASE
    except Exception:
        print(uid)
        raise Exception()

    return prefix, script_id, int(line_id, 16)