from log.log import log


class TicketResultData:
    def __init__(self, result, flag, map):
        self.result = result
        self.flag = flag
        self.map = map

    @staticmethod
    def object_hook(dict_data):
        return TicketResultData(
            dict_data['result'],
            dict_data['flag'],
            dict_data['map']
        )


class TicketResult:
    def __init__(self, httpstatus, data, messages, status):
        self.httpstatus = httpstatus
        self.data = data
        self.messages = messages
        self.status = status

    @staticmethod
    def object_hook(dict_data):
        print(type(dict_data))
        print(dict_data)
        return TicketResult(
            dict_data['httpstatus'],
            dict_data['data'],
            # json.loads(dict_data['data'], cls=TicketResultData.object_hook),
            dict_data['messages'],
            dict_data['status']
        )


def get_dj_by_seat(seat_type):
    seat_type_map = {
        '9': 'SWZ',
        'M': 'ZY',
        'O': 'ZE',

        '6': 'GR',
        'I': 'RW',
        'F': 'SRRB',
        'J': 'YW',

        '1': 'YZ',
        '2': 'RZ',
        '3': 'YW',
        '4': 'RW',
        'A': 'YYRW',
        'P': 'TZ'
    }
    return seat_type_map[seat_type]

def get_detail(result, data_map):
    keys = [
        'train_no',
        # 车次号
        'station_train_code',
        'start_station_telecode',
        'end_station_telecode',
        'from_station_telecode',
        'to_station_telecode',
        # 发车时间
        'start_time',
        # 到达时间
        'arrive_time',
        # 历时
        'lishi',
        # 是否可预订
        'canWebBuy',

        'yp_info',
        'start_train_date',
        'train_seat_feature',
        'location_code',
        'from_station_no',
        'to_station_no',
        'is_support_card',
        'controlled_train_flag',
        'gg_num',
        # 高级软卧
        'gr_num',

        # 其他
        'qt_num',
        # 软卧
        'rw_num',
        # 软座
        'rz_num',
        # 特等座?
        'tz_num',
        # 无座
        'wz_num',
        'yb_num',
        # 硬卧
        'yw_num',
        # 硬座
        'yz_num',
        # 二等座数
        'ze_num',
        # 一等座数
        'zy_num',

        # 商务座数
        'swz_num',
        # 动卧
        'srrb_num',
        'yp_ex',
        'seat_types',
        'exchange_train_flag',
        'houbu_train_flag',
        'houbu_seat_limit',
        # yp_info_new index 39
        'yp_info_new',
    ]
    left_keys = [
        # dw_flag index 46
        'dw_flag',
        # stopcheckTime index 48
        'stopcheckTime',

        'country_flag',
        'local_arrive_time',
        'local_start_time',
    ]
    result_list = []
    for item in result:
        contents = item.split('|')
        start = 0
        secret_str = contents[start]
        start += 1
        button_text_info = contents[start]
        start += 1
        child = {
            'secretStr': secret_str,
            'buttonTextInfo': button_text_info,
            'queryLeftNewDTO': {

            }
        }
        i = 0
        num_start = keys.index('gg_num')
        num_end = keys.index('srrb_num')
        while i < len(keys):
            if num_end >= i >= num_start:
                child['queryLeftNewDTO'][keys[i]] = contents[start + i]
            else:
                child['queryLeftNewDTO'][keys[i]] = contents[start + i]
            i = i + 1

        i = 0
        start = 46
        offset = 0
        while i < len(left_keys):
            if i > 0:
                offset = 1
            child['queryLeftNewDTO'][left_keys[i]] = contents[start + i + offset]
            i = i + 1

        child['queryLeftNewDTO']['from_station_name'] = data_map[contents[6]],
        child['queryLeftNewDTO']['to_station_name'] = data_map[contents[7]],

        result_list.append(child)

    return result_list


def can_buy_seat(detail, seat_type):
    seat_type_filed_map = {
        '9': 'swz_num',
        'M': 'zy_num',
        'O': 'ze_num',
        'P': 'tz_num',

        '6': 'gr_num',
        'I': 'rw_num',
        # 动车的高级软卧下单确认页面就是高级动卧
        'A': 'gr_num',
        'F': 'srrb_num',
        'J': 'yw_num',

        '1': 'yz_num',
        '2': 'rz_num',
        '3': 'yw_num',
        '4': 'rw_num',
    }
    num = detail[seat_type_filed_map[seat_type]]
    log(f'can_buy_seat num = {num}')
    return num == '有' or (len(num) > 0 and num.isdigit())
