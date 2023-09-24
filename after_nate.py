import datetime
import time

from api_login import check_user, check_verify
from api_with_cookie import update_cookie
from global_var import get_value
from passenger import get_passengers, get_order_passengers
from qr_login import qr_login
from util import is_success


def candidate_process(train_detail):
    check_pass = False
    submit_after_login = False
    login_with_psw = get_value('login') == 'psw'
    while not check_pass:
        check_pass = check_face(train_detail)
        if not check_pass:
            if login_with_psw:
                is_login = False
                check_verify()
                while not is_login:
                    can_go_next = get_value('can_go_next')
                    if can_go_next:
                        break
                    time.sleep(0.3)
                submit_after_login = True
            else:
                rsp = qr_login()
                if is_success(rsp) and rsp['data']['is_login'] == 'Y':
                    submit_after_login = True
                    break
        else:
            check_pass = check_user()
            if check_pass:
                submit_after_login = True
            break

    if submit_after_login:
        seat_type = get_value('config_dict')['seatType']
        secret_list = train_detail['secretStr'] + '#' + seat_type + '|'
        rsp = submit_candidate_order(secret_list)
        if is_success(rsp) and rsp['data']['flag']:
            rsp = after_nate_passenger_init()
            if is_success(rsp):
                rsp = get_passengers()
                passenger_list = get_order_passengers(rsp)
            else:
                passenger_list = None
            if passenger_list is not None and len(passenger_list) > 0:
                passenger_info = ''
                for passenger in passenger_list:
                    born_date = int(passenger['born_date'].split('-')[0])
                    age = datetime.date.today().year - born_date
                    is_old_than_60 = age >= 60
                    passenger_info += (passenger['passenger_type'] + '#' + passenger['passenger_name'] + '#' +
                                       passenger['passenger_id_type_code'] + '#' + passenger['passenger_id_no'] + '#' + passenger['allEncStr'] + '#')
                    if is_old_than_60:
                        passenger_info += '1;'
                    else:
                        passenger_info += '0;'
                if len(passenger_info) > 0 and check_candidate_queue_can_goto_next():
                    rsp = confirm_candidate_order(passenger_info, train_detail)
                    if is_success(rsp) and rsp['data']['flag']:
                        if rsp['data']['isAsync']:
                            while True:
                                next_request_time = query_candidate_queue()
                                if next_request_time > 0:
                                    time.sleep(next_request_time)
                                else:
                                    break

def confirm_candidate_order(passenger_info, train_detail):
    url = 'https://kyfw.12306.cn/otn/afterNate/confirmHB'
    seat_type = get_value('config_dict')['seatType']
    rsp = update_cookie(url, post_data={
        'passengerInfo': passenger_info,
        'jzParam': '',
        # 候补车次信息
        'hbTrain': train_detail['queryLeftNewDTO']['train_no'] + ',' + seat_type + '#',
        'lkParam': '',
        'sessionId': '',
        'sig': '',
        'scene': 'nc_login',
        'encryptedData': '',
        # 是否接受无座，默认接受
        'if_receive_wseat': 'Y',
        # 截止兑换时间，默认开车前6小时
        'realize_limit_time_diff': 360
    }, other={
        'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8'
    })
    return rsp

def after_nate_passenger_init():
    url = 'https://kyfw.12306.cn/otn/afterNate/passengerInitApi'
    return update_cookie(url)

# 候补队列查询
def check_candidate_queue_can_goto_next():
    url = 'https://kyfw.12306.cn/otn/afterNate/getQueueNum'
    rsp = update_cookie(url)
    if is_success(rsp) and rsp['data']['flag']:
        return True
    return False

def query_candidate_queue():
    url = 'https://kyfw.12306.cn/otn/afterNate/queryQueue'
    rsp = update_cookie(url)
    if is_success(rsp) and rsp['data']['flag'] and rsp['data']['isAsync']:
        status = rsp['data']['status']
        if status == 1:
            print('候补排队成功，待支付')
            return 0
        elif status == -1:
            print('候补排队失败')
        else:
            wait_time = rsp['data']['waitTime']
            n = int(wait_time / 3)
            if n < 1:
                n = 1
            return n
    return -1


def check_face(train_detail):
    seat_type = get_value('config_dict')['seatType']
    secret_list = train_detail['secretStr'] + '#' + seat_type + '|'
    success_secret = train_detail['secretStr'] + '#' + seat_type
    url = 'https://kyfw.12306.cn/otn/afterNate/chechFace'
    rsp = update_cookie(url, post_data={
        'secretList': secret_list,
        '_json_attr': '',
    }, other={
        'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8'
    })
    if is_success(rsp) and rsp['data']['login_flag'] and rsp['data']['face_flag']:
        return get_success_rate(success_secret)
    return False

def get_success_rate(success_secret):
    url = 'https://kyfw.12306.cn/otn/afterNate/getSuccessRate'
    rsp = update_cookie(url, post_data={
        'successSecret': success_secret,
        '_json_attr': '',
    }, other={
        'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8'
    })
    if is_success(rsp) and rsp['data']['flag'][0] is not None:
        level = int(rsp['data']['flag'][0]['level'])
        print(rsp['data']['flag'][0]['info'])
        # 候补人数少时可以尝试候补
        if level <= 2:
            return True
    return False


def submit_candidate_order(secret_list):
    url = 'https://kyfw.12306.cn/otn/afterNate/submitOrderRequest'
    return update_cookie(url, post_data={
        'secretList': secret_list,
        '_json_attr': '',
    }, other={
        'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8'
    })