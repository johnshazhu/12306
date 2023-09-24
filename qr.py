import base64
import datetime
import json
import os
import ssl
import time
import urllib
import threading
from urllib.parse import urlencode

import handle_sms_code
import notification_util
from api_with_cookie import init, update_cookie
from config import init_config
from global_var import get_value, set_value
from js.js_util import exec_js
from ticket.query_left_ticket import get_detail, can_buy_seat


def get_today_str():
    return datetime.date.today().strftime('%Y-%m-%d')

def is_success(response):
    if 'result_code' in response:
        return str(response['result_code']) == '0'
    if 'status' in response:
        return response['status']
    return False

def create_qr64():
    url = 'https://kyfw.12306.cn/passport/web/create-qr64'
    rsp = update_cookie(url, post_data={
        'appid': 'otn'
    }, other={
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'
    })
    if rsp['result_code'] == '0':
        # print(rsp['image'])
        # print(rsp['uuid'])
        image = base64.b64decode(rsp['image'])
        if os.path.exists("resource/qr_image.jpg"):
            os.remove("resource/qr_image.jpg")
        file = open('resource/qr_image.jpg', 'wb')
        file.write(image)
        file.close()
        return rsp['uuid']
    return None

def check_qr(uuid):
    while True:
        url = 'https://kyfw.12306.cn/passport/web/checkqr'
        rsp = update_cookie(url, post_data={
            'appid': 'otn',
            'uuid': uuid
        }, other={
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'
        })
        if rsp['result_code'] == '2':
            print(rsp['result_message'])
            uamtk = rsp['uamtk']
            break
        time.sleep(0.5)

def user_login():
    return update_cookie('https://kyfw.12306.cn/otn/login/userLogin', post_method=False)

def redirect_user_login():
    return update_cookie('https://kyfw.12306.cn/otn/passport?redirect=/otn/login/userLogin', post_method=False)

def uamtk():
    return update_cookie('https://kyfw.12306.cn/passport/web/auth/uamtk', post_data={
        'appid': 'otn'
    }, other={
        'Referer': 'https://kyfw.12306.cn/otn/passport?redirect=/otn/login/userLogin',
        'Content-Type': 'application/x-www-form-urlencoded;application/json;charset=UTF-8'
    })

def uamauthclient(new_app_tk):
    return update_cookie('https://kyfw.12306.cn/otn/uamauthclient', post_data={
        'tk': new_app_tk,
    }, other={
        'Referer': 'https://kyfw.12306.cn/otn/passport?redirect=/otn/login/userLogin',
        'Content-Type': 'application/x-www-form-urlencoded;application/json;charset=UTF-8'
    })

def web_auth_uamtk_static():
    print('查看是否已登录')
    return update_cookie('https://kyfw.12306.cn/passport/web/auth/uamtk-static', post_data={
            'appid': 'otn'
        }, other={
            'Content-Type': 'application/x-www-form-urlencoded'
        })

def conf():
    return update_cookie('https://kyfw.12306.cn/index/otn/login/conf')

def get_login_config():
    print('获取登录配置')
    rsp = update_cookie('https://kyfw.12306.cn/otn/login/conf')
    if is_success(rsp):
        data = rsp['data']
        set_value('is_uam_login', data['is_uam_login'] == 'Y')
        set_value('is_login_passCode', data['is_login_passCode'] == 'Y')
        set_value('is_login', data['is_login'] == 'Y')
        set_value('queryUrl', data['queryUrl'])
    return rsp

def check_verify():
    rsp = check_login_verify()
    if rsp['login_check_code'] == '0':
        process_start_from_login()
    elif rsp['login_check_code'] == '2':
        print('滑块方式验证暂不支持')
    elif rsp['login_check_code'] == '3':
        print('短信验证码方式验证')
        rsp = get_sms_code()
        if is_success(rsp):
            notification_util.show_notification('短信验证码', '请注意查看短信验证码并输入')
            handle_sms_code.input_sms_code(submit_sms_code_callback)
        else:
            print(rsp['result_message'])
    else:
        print(rsp)

def check_login_verify():
    return update_cookie('https://kyfw.12306.cn/passport/web/checkLoginVerify', post_data={
        'username': get_value('config_obj').username,
        'appid': 'otn'
    }, other={
        'Referer': 'https://kyfw.12306.cn/otn/resources/login.html',
        'Content-Type': 'application/x-www-form-urlencoded;application/json;charset=UTF-8',
        'Origin': 'https://kyfw.12306.cn',
        'Accept': '*/*'
    })

def get_sms_code():
    print('获取短信验证码')
    url = 'https://kyfw.12306.cn/passport/web/getMessageCode'
    check_data = {
        'username': get_value('config_obj').username,
        'appid': 'otn',
        'castNum': get_value('config_dict')['castNum'],
    }
    return update_cookie(url, post_data=check_data, other={
        'Referer': 'https://kyfw.12306.cn/otn/resources/login.html',
        'Content-Type': 'application/x-www-form-urlencoded;application/json;charset=UTF-8',
        'Origin': 'https://kyfw.12306.cn',
        'Accept': '*/*'
    })

def submit_sms_code_callback():
    sms_code = handle_sms_code.get_sms_code()
    config = get_value('config_obj')
    config.checkMode = '0'
    config.randCode = sms_code
    set_value('config_obj', config)

    handle_sms_code.destroy()
    process_start_from_login()


def to_user_auth_center():
    rsp = uamtk()
    if is_success(rsp):
        tk = rsp['newapptk']
        if tk is None:
            tk = rsp['apptk']
        rsp = uamauthclient(tk)
        if is_success(rsp):
            user_login()
            rsp = conf()
            set_value('can_go_next', is_success(rsp) and rsp['data']['is_login'] == 'Y')
            return rsp

def process_start_from_login():
    print('process_start_from_login')
    rsp = web_login()
    session = get_value('session')
    if 'isPasswordCopy' in session.headers:
        del session.headers['isPasswordCopy']
        set_value('session', session)
    if rsp['result_code'] == 0:
        print('跳转otn/login/userLogin')
        rsp = user_login()
        if rsp == 302:
            redirect_user_login()
        to_user_auth_center()
    elif rsp['result_code'] == 91 or rsp['result_code'] == 92 or rsp['result_code'] == 94 or rsp['result_code'] == 95 or rsp['result_code'] == 97:
        is_uam_login = get_value('is_uam_login')
        if is_uam_login:
            to_user_auth_center()
    elif rsp['result_code'] == 101:
        print('您的密码很久没有修改了，为降低安全风险，请您重新设置密码后再登录')
    else:
        print(rsp['result_message'])

def web_login():
    return update_cookie('https://kyfw.12306.cn/passport/web/login', post_data=get_value('config_obj').__dict__, other={
        'isPasswordCopy': 'N',
        'Referer': 'https://kyfw.12306.cn/otn/resources/login.html',
        'Content-Type': 'application/x-www-form-urlencoded;application/json;charset=UTF-8',
        'Origin': 'https://kyfw.12306.cn',
    })


def query_left_tickets():
    return update_cookie('https://kyfw.12306.cn/otn/leftTicket/queryZ', post_data={
        'leftTicketDTO.train_date': get_value('config_dict')['date'],
        'leftTicketDTO.from_station': get_value('from_station_code'),
        'leftTicketDTO.to_station': get_value('to_station_code'),
        'purpose_codes': get_value('config_dict')['purpose_codes'],
    }, other={
        'Referer': 'https://kyfw.12306.cn/otn/leftTicket/init',
        'If-Modified-Since': '0',
        'X-Requested-With': 'XMLHttpRequest',
        'Accept': '*/*',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Site': 'same-origin',
        'Cache-Control': 'no-cache',
        'Accept-Encoding': 'gzip, deflate, br',
        'Content-Type': 'application/x-www-form-urlencoded;application/json;charset=UTF-8'
    }, post_method=False)

def check_user():
    url = 'https://kyfw.12306.cn/otn/login/checkUser'
    post_data = {
        '_json_att': ''
    }
    rsp = update_cookie(url, post_data=post_data, other={
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'
    })
    if is_success(rsp) and rsp['data']['flag']:
        return True
    return False

def submit_order(train_detail, back_date):
    order_date = get_value('config_dict')['date']
    submit_order_url = 'https://kyfw.12306.cn/otn/leftTicket/submitOrderRequest'
    post_data = {
        'secretStr': urllib.parse.unquote(train_detail['secretStr'], encoding='utf-8', errors='replace'),
        'train_date': order_date,
        'back_train_date': get_today_str(),
        'purpose_codes': get_value('config_dict')['purpose_codes'],
        'tour_flag': 'dc',
        'query_from_station_name': get_value('config_dict')['from'],
        'query_to_station_name': get_value('config_dict')['to'],
        'undefined': ''
    }
    return update_cookie(submit_order_url, post_data=post_data, other={
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'
    }, post_method=True)


def get_repeat_submit_token():
    url = 'https://kyfw.12306.cn/otn/confirmPassenger/initDc'
    content = update_cookie(url, other={
        'Content-Type': 'application/x-www-form-urlencoded'
    })
    return get_token_from_content(content.decode('utf-8'))


def get_passengers(token):
    url = 'https://kyfw.12306.cn/otn/confirmPassenger/getPassengerDTOs'
    return update_cookie(url, post_data={
        '_json_att': '',
        'REPEAT_SUBMIT_TOKEN': token
    }, other={
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'
    })

def check_order_info(passengers, token):
    check_order_info_url = 'https://kyfw.12306.cn/otn/confirmPassenger/checkOrderInfo'
    return update_cookie(check_order_info_url, post_data={
        'cancel_flag': 2,
        'bed_level_order_num': '000000000000000000000000000000',
        'passengerTicketStr': get_passenger_tickets(passengers),
        'oldPassengerStr': get_old_passengers(passengers),
        'tour_flag': 'dc',
        'whatsSelect': str(len(passengers)),
        'sessionId': '',
        'sig': '',
        'scene': 'nc_login',
        '_json_att': '',
        'REPEAT_SUBMIT_TOKEN': token
    }, other={
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'
    })

def get_queue_count(token, train_info):
    url = 'https://kyfw.12306.cn/otn/confirmPassenger/getQueueCount'
    config_dict = get_value('config_dict')
    ticket_info_for_passenger_form = get_value('ticket_info_for_passenger_form')

    return update_cookie(url, post_data={
        'train_date': exec_js('js/date.js', 'getTrainDate', config_dict['date']),
        'train_no': train_info['train_no'],
        'stationTrainCode': train_info['station_train_code'],
        'seatType': config_dict['seatType'],
        'fromStationTelecode': train_info['from_station_telecode'],
        'toStationTelecode': train_info['to_station_telecode'],
        'leftTicket': ticket_info_for_passenger_form['queryLeftTicketRequestDTO']['ypInfoDetail'],
        'purpose_codes': ticket_info_for_passenger_form['purpose_codes'],
        'train_location': train_info['location_code'],
        'REPEAT_SUBMIT_TOKEN': token
    }, other={
        'Referer': 'https://kyfw.12306.cn/otn/confirmPassenger/initDc',
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'
    })

def confirm_single_for_queue(token, confirm_order_passengers, train_info, encrypted_data):
    cookie = get_value('cookie')
    ticket_info_for_passenger_form = get_value('ticket_info_for_passenger_form')
    config_dict = get_value('config_dict')
    url = 'https://kyfw.12306.cn/otn/confirmPassenger/confirmSingleForQueue'
    if '_passport_session' in cookie:
        del cookie['_passport_session']

    cookie['highContrastMode'] = 'defaltMode'
    cookie['cursorStatus'] = 'off'
    cookie['guidesStatus'] = 'off'
    cookie['_jc_save_wfdc_flag'] = 'dc'
    cookie['_jc_save_showIns'] = 'true'
    cookie['_jc_save_fromStation'] = get_value('_jc_save_fromStation')
    cookie['_jc_save_toStation'] = get_value('_jc_save_toStation')
    cookie['_jc_save_fromDate'] = config_dict['date']
    cookie['_jc_save_toDate'] = get_today_str()

    return update_cookie(url, post_data={
        'passengerTicketStr': get_passenger_tickets(confirm_order_passengers),
        'oldPassengerStr': get_old_passengers(confirm_order_passengers),
        'purpose_codes': ticket_info_for_passenger_form['purpose_codes'],
        'key_check_isChange': ticket_info_for_passenger_form['key_check_isChange'],
        'leftTicketStr': ticket_info_for_passenger_form['leftTicketStr'],
        'train_location': ticket_info_for_passenger_form['train_location'],
        'choose_seats': config_dict['chooseSeats'],
        # 卧铺席， 2个下铺200，两个中铺020，其他 101（上下铺）
        'seatDetailType': config_dict['seatDetailType'],
        # 静音车厢
        'is_jy': 'N',
        # 残疾人
        'is_cj': 'Y',
        # js 中...window.json_ua.toString()
        # 'encryptedData': get_encrypted_data(),
        'encryptedData': encrypted_data,
        'whatsSelect': len(confirm_order_passengers),
        # 动卧？
        'roomType': '00',
        # 单程往返全选
        'dwAll': 'N',
        '_json_att': '',
        'REPEAT_SUBMIT_TOKEN': token
    }, other={
        'Referer': 'https://kyfw.12306.cn/otn/confirmPassenger/initDc',
        'Sec-Ch-Ua': '"Chromium";v="116", "Not)A;Brand";v="24", "Google Chrome";v="116"',
        'Sec-Ch-Ua-Mobile': '?0',
        'Sec-Ch-Ua-Platform': "macOS",
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-origin',
        'Pragma': 'no-cache',
        'X-Requested-With': 'XMLHttpRequest',
        'Cache-Control': 'no-cache',
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'
    })

def query_order_wait_time(token):
    url = 'https://kyfw.12306.cn/otn/confirmPassenger/queryOrderWaitTime'
    return update_cookie(url, post_data={
        'random': exec_js('js/date.js', 'getDatetime'),
        'tourFlag': 'dc',
        '_json_att': '',
        'REPEAT_SUBMIT_TOKEN': token
    }, other={
        'Referer': 'https://kyfw.12306.cn/otn/confirmPassenger/initDc'
    }, post_method=False)

def result_order_for_dc_queue(order_id, token):
    url = 'https://kyfw.12306.cn/otn/confirmPassenger/resultOrderForDcQueue'
    return update_cookie(url, post_data={
        'orderSequence_no': order_id,
        '_json_att': '',
        'REPEAT_SUBMIT_TOKEN': token
    }, other={
        'Referer': 'https://kyfw.12306.cn/otn/confirmPassenger/initDc'
    })

def get_old_passengers(passenger_list):
    old_passengers_str = ''
    for passenger_info in passenger_list:
        name = passenger_info['passenger_name']
        id_number = passenger_info['passenger_id_no']
        id_type_code = passenger_info['passenger_id_type_code']
        passenger_type = passenger_info['passenger_type']
        old_passengers_str += f'{name},{id_type_code},{id_number},{passenger_type}_'
    return old_passengers_str

def get_token_from_content(html_content):
    start = html_content.find('var ticketInfoForPassengerForm=')
    if start > -1:
        content = html_content[start:]
        start_index = content.find('=')
        end_index = content.find(';')
        if start_index > -1 and end_index > -1:
            content = content[start_index + 1:end_index]
            content = content.replace('\'', '\"')
            set_value('ticket_info_for_passenger_form', json.loads(content))

    start = html_content.find('var globalRepeatSubmitToken = ')
    if start > -1:
        content = html_content[start:]
        start_index = content.find('\'')
        end_index = content.find(';')
        if start_index > -1 and end_index > -1:
            token = content[(start_index + 1):(end_index - 1)]
            print(f'token = {token}')
            set_value('token', token)
            return token

def get_selected_train_detail(rsp):
    detail_list = get_detail(rsp['data']['result'], rsp['data']['map'])
    train_code = get_value('config_dict')['trainCode']
    check_train_code = False
    if train_code is not None and len(str(train_code)) > 0:
        check_train_code = True
    for detail in detail_list:
        train_info = detail['queryLeftNewDTO']
        if train_info['canWebBuy'] != 'Y' or \
                (check_train_code and train_code.find(
                    train_info['station_train_code']) == -1) or \
                not can_buy_seat(train_info, get_value('config_dict')['seatType']):
            continue

        print('---get_selected_train_info---')
        print(train_info)
        cookie = get_value('cookie')
        if 'uamtk' in cookie:
            del cookie['uamtk']
            set_value('cookie', cookie)

        return detail

def get_order_passengers(rsp):
    if rsp['status'] and len(rsp['data']['normal_passengers']) > 0:
        order_passengers = []
        for passenger in rsp['data']['normal_passengers']:
            if get_value('config_dict')['passengers'].find(passenger['passenger_name']) != -1:
                order_passengers.append(passenger)
        return order_passengers

def get_passenger_tickets(passenger_list):
    passengers_tickets = ''
    for passenger_info in passenger_list:
        name = passenger_info['passenger_name']
        id_number = passenger_info['passenger_id_no']
        mobile = passenger_info['mobile_no']
        id_type_code = passenger_info['passenger_id_type_code']
        all_enc_str = passenger_info['allEncStr']
        passenger_type = passenger_info['passenger_type']
        seat_type = get_value('config_dict')['seatType']
        passengers_tickets += f'{seat_type},0,{passenger_type},{name},{id_type_code},{id_number},{mobile},N,{all_enc_str}_'
    return passengers_tickets[0:(len(passengers_tickets) - 1)]

def check_is_can_select_seat_or_bed(rsp):
    if rsp['status'] and rsp['data']['submitStatus']:
        # 是否可选座位或铺位
        if rsp['data']['canChooseSeats'] == 'Y' or rsp['data']['canChooseBeds'] == 'Y':
            return True
    return False

def check_can_confirm_order(rsp):
    if rsp['status']:
        print('余票 : ' + rsp['data']['ticket'] + ', 排队人数 : ' + rsp['data']['count'])
        if rsp['data']['op_2'] != 'false':
            print('目前排队人数已经超过余票张数，请您选择其他席别或车次')
            return False
        print('---confirm_single_for_queue---')
        return True
    return False

def check_wait_time(rsp):
    if rsp['status'] and rsp['data']['submitStatus']:
        if rsp['data']['isAsync']:
            return True
    return False

def need_check_order(rsp):
    return rsp['status'] and rsp['data']['orderId'] is not None

def need_resend_wait_time_req(rsp):
    return rsp['status'] and rsp['data']['orderId'] is None

def check_order_success(rsp):
    return rsp['status'] and rsp['data']['submitStatus']

def start_timer_job(token):
    t1 = threading.Thread(target=timer_job, args=(token, 0))
    t2 = threading.Thread(target=delay_timer_job, args=(token,))
    print("{}".format(int(time.time())) + ' : start_timer_job')
    t1.start()
    t2.start()
    t1.join()
    t2.join()

def delay_timer_job(token):
    print("{}".format(int(time.time())) + ' : delay_timer_job')
    timer = threading.Timer(1.0, function=timer_job, args=(token, 1))
    timer.start()

def timer_job(token, index):
    disp_time = get_value('disp_time')
    next_request_time = get_value('next_request_time')
    print("{}".format(int(time.time())) + ' : execute timer_job index = ' + str(index) + ', disp_time = ' + str(disp_time) + ', next_request_time = ' + str(next_request_time))

    if disp_time <= 0:
        rsp = result_order_for_dc_queue(get_value('orderId'), token)
        if check_order_success(rsp):
            set_value('order_success', True)
            print('order success, orderId = ' + get_value('orderId'))
            return True
        else:
            print('order confirm fail')
            return False

    if disp_time == next_request_time:
        rsp = query_order_wait_time(token)
        if rsp['status'] and rsp['data']['queryOrderWaitTimeStatus']:
            wait_time = rsp['data']['waitTime']
            if wait_time != -100:
                set_value('disp_time', wait_time)
                set_value('orderId', rsp['data']['orderId'])
                d = int(wait_time / 1.5)
                if d > 60:
                    d = 60
                b = wait_time - d
                if b <= 0:
                    b = 1
                set_value('next_request_time', b)

    if disp_time > 1:
        disp_time -= 1
        set_value('disp_time', disp_time)
    if index > 0:
        time.sleep(1)
        timer_job(token, index + 1)

def process_from_query_start():
    rsp = query_left_tickets()
    if is_success(rsp):
        detail = get_selected_train_detail(rsp)
        # 可能需要调用checkUser接口
        # rsp = check_user()
        # if is_success(rsp) and rsp['data']['flag']:
        if detail is None:
            return False
        rsp = submit_order(detail, '')
        if is_success(rsp):
            token = get_repeat_submit_token()
            rsp = get_passengers(token)
            passenger_list = get_order_passengers(rsp)
            if passenger_list is not None and len(passenger_list) > 0:
                rsp = check_order_info(passenger_list, token)
                if check_is_can_select_seat_or_bed(rsp):
                    selected_train_info = detail['queryLeftNewDTO']
                    rsp = get_queue_count(token, selected_train_info)
                    if check_can_confirm_order(rsp):
                        # encrypted_data = exec_js('js/suit.js', 'init', get_cookie())
                        rsp = confirm_single_for_queue(token, passenger_list, selected_train_info, '')
                        if check_wait_time(rsp):
                            set_value('disp_time', 1)
                            set_value('next_request_time', 1)
                            start_timer_job(token)
                            return True
                        else:
                            print('check_wait_time failed')
                            print(rsp['data'])

    return False


if __name__ == '__main__':
    ssl._create_default_https_context = ssl._create_unverified_context
    if init_config():
        uuid = create_qr64()
        if uuid is not None:
            check_qr(uuid)

            rsp = user_login()

            if rsp == 302:
                rsp = redirect_user_login()

            rsp = to_user_auth_center()
            if is_success(rsp) and rsp['data']['is_login'] == 'Y':
                config_dict = get_value('config_dict')
                delay_time = 0
                if 'timesBetweenTwoQuery' in config_dict:
                    delay_time = float(config_dict['timesBetweenTwoQuery'])

                if delay_time > 0.3:
                    set_value('order_success', False)
                    while not get_value('order_success'):
                        success = process_from_query_start()
                        if not success:
                            time.sleep(delay_time)
                else:
                    process_from_query_start()
