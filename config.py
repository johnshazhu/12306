import json

import api_with_cookie
import global_var
from js.js_util import exec_js
from station import init_station_names

from global_var import set_value
from unescape import escape

SM4_key = 'tiekeyuankp12306'

class Config:
    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.appid = 'otn'
        self.sessionId = ''
        self.sig = ''
        self.if_check_slide_passcode_token = ''
        self.scene = ''
        # 0
        self.checkMode = ''
        # SMS验证码
        self.randCode = ''
        self._json_att = ''

    @staticmethod
    def object_hook(dict_data):
        return Config(dict_data['username'], dict_data['password'])


def init_config():
    global_var.init()

    api_with_cookie.init()

    config_dict = {}
    with open('config.properties', 'r') as f:
        for line in f.readlines():
            line = line.strip()
            if not len(line):
                continue
            key = line.split('=')[0]
            if len(str(line)[(len(key) + 1):]) > 0:
                config_dict[key] = str(line)[(len(key) + 1):]

    set_value('config_dict', config_dict)
    config_check_pass = True
    if 'username' not in config_dict:
        config_check_pass = False
        print('请在config.properties中配置用户名username=xxx')

    if 'password' not in config_dict:
        config_check_pass = False
        print('请在config.properties中配置用户名password=xxx')

    if 'trainCode' not in config_dict:
        config_check_pass = False
        print('需要在config.properties中设置预订的车次trainCode=xxx')

    if 'from' not in config_dict:
        config_check_pass = False
        print('需要在config.properties中设置出发站from=xxx')

    if 'to' not in config_dict:
        config_check_pass = False
        print('需要在config.properties中设置到达站to=xxx')

    if 'date' not in config_dict:
        config_check_pass = False
        print('需要在config.properties中设置预订车次的日期date=xxx')

    if 'seatType' not in config_dict:
        config_check_pass = False
        print('需要在config.properties中设置预订车次坐席类别seatType=xxx')

    if 'castNum' not in config_dict:
        config_check_pass = False
        print('需要在config.properties中设置预订登录账号对应人的身份证的后四位castNum=xxx')

    if config_check_pass:
        station_name_list = init_station_names()

        if station_name_list is not None:
            from_station_code = get_station_code(config_dict['from'], station_name_list)
            to_station_code = get_station_code(config_dict['to'], station_name_list)
            set_value('from_station_code', from_station_code)
            set_value('to_station_code', to_station_code)
            set_value('_jc_save_fromStation', escape(config_dict['from'] + ',' + from_station_code))
            set_value('_jc_save_toStation', escape(config_dict['to'] + ',' + to_station_code))
        config_content = json.dumps(config_dict)
        config_obj = json.loads(config_content, object_hook=Config.object_hook)
        config_obj.password = get_encrypt_content(config_obj.password)
        print('username = ' + config_obj.username)
        set_value('config_obj', config_obj)
    return config_check_pass


def get_station_code(name, station_name_list):
    for station in station_name_list:
        if station[1] == name:
            print(station)
            return station[2]


def get_encrypt_content(plain_text):
    encrypt_result = exec_js('js/SM4.js', "encrypt_ecb", plain_text, SM4_key)
    return f'@{encrypt_result}'