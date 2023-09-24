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

    seats = ['1', '2', '3', '4', '6', '9', 'F', 'I', 'J', 'M', 'O', 'P']
    can_choose_seats_type = ['9', 'M', 'O', 'P']
    can_choose_seat_detail_type = ['3', '4', 'F']
    other_seats_type = ['1', '2', '6', 'I', 'J']
    keys_check_ignore = 'timesBetweenTwoQuery, chooseSeats, seatDetailType, trainCode, candidate'
    config_check_pass = True
    with open('config.properties', 'r') as f:
        for line in f.readlines():
            line = line.strip()
            if not len(line):
                continue
            key = line.split('=')[0]
            config_dict[key] = str(line)[(len(key) + 1):]
            if len(config_dict[key]) == 0:
                if keys_check_ignore.find(key) == -1:
                    config_check_pass = False
                    print(f'请在config.properties中配置{key}的值=xxx')

    # 检查坐席设置是否正常
    if config_check_pass and not is_value_exist(config_dict['seatType'], seats):
        config_check_pass = False
        print(f'seatType的值应该在{seats}中')

    # 是否是不可选座类型
    if config_check_pass and is_value_exist(config_dict['seatType'], other_seats_type):
        config_dict['seatDetailType'] = '000'
        config_dict['chooseSeats'] = ''

    # 检查是动车/高铁坐席
    if config_check_pass and is_value_exist(config_dict['seatType'], can_choose_seats_type):
        # 动车或高铁时，seatDetailType设置无效，默认为'000'
        config_dict['seatDetailType'] = '000'
        if len(config_dict['chooseSeats']) == 0:
            config_check_pass = False
            print('请在config.properties中配置chooseSeats的值')

    # 检查是否是卧铺类坐席
    if config_check_pass and is_value_exist(config_dict['seatType'], can_choose_seat_detail_type):
        # 卧铺类时，chooseSeats设置无效，默认为''
        config_dict['chooseSeats'] = ''
        if len(config_dict['seatDetailType']) == 0:
            config_check_pass = False
            print('请在config.properties中配置seatDetailType的值')

    if config_check_pass:
        set_value('config_dict', config_dict)
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


def is_value_exist(value, value_list):
    try:
        index = value_list.index(value)
        return index >= 0
    except Exception as err:
        print(f'ignore this err...{err}')
    return False

def get_station_code(name, station_name_list):
    for station in station_name_list:
        if station[1] == name:
            print(station)
            return station[2]


def get_encrypt_content(plain_text):
    encrypt_result = exec_js('js/SM4.js', "encrypt_ecb", plain_text, SM4_key)
    return f'@{encrypt_result}'