def init():
    global global_dict
    global_dict = {}

def set_value(key, value):
    global_dict[key] = value

def get_value(key):
    return global_dict[key]


