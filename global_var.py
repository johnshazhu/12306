def init():
    global global_dict
    global_dict = {}

def set_value(key, value):
    global_dict[key] = value

def get_value(key):
    if key in global_dict:
        return global_dict[key]
    return None


