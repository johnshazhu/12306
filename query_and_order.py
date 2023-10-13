import json
import threading
import time
import urllib

from after_nate import candidate_process
from api_with_cookie import update_cookie
from global_var import get_value, set_value
from js.js_util import exec_js
from log.log import log
from passenger import get_passengers, get_order_passengers
from ticket.query_left_ticket import get_detail, can_buy_seat
from util import get_today_str, is_candidate_config, is_success


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

    dw_flag = train_info['dw_flag']
    split_info = dw_flag.split('#')
    is_jy = 'N'
    if len(split_info) > 2 and split_info[2][0:1] == 'Q':
        log('本次列车有静音车厢，默认将优先选择静音车厢')
        is_jy = 'Y'

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
        'is_jy': is_jy,
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
        # 'random': exec_js('js/date.js', 'getDatetime'),
        'random': int(time.time() * 1000),
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
            log(f'token = {token}')
            set_value('token', token)
            return token


def update_cookie_without_uamtk():
    cookie = get_value('cookie')
    if 'uamtk' in cookie:
        del cookie['uamtk']
        set_value('cookie', cookie)

def get_selected_train_detail(rsp):
    detail_list = get_detail(rsp['data']['result'], rsp['data']['map'])

    # 是否只看设置的车次
    train_code = get_value('config_dict')['trainCode']
    check_train_code = False
    train_set = None
    if train_code is not None and len(str(train_code)) > 0:
        check_train_code = True
        train_list = train_code.split(',')
        train_set = set(train_list)

    # 是否只看几点以后的车次
    after_time = get_value('config_dict')['aftertime']
    check_start_time = False
    if train_code is not None and len(str(after_time)) > 0:
        check_start_time = True

    # 只看有对应坐席的车次
    seat_type = get_value('config_dict')['seatType']

    candidate = is_candidate_config()
    candidate_train = None
    for detail in detail_list:
        train_info = detail['queryLeftNewDTO']
        # 若设置了车次，当前车次不在预定车次列表里
        if check_train_code and train_info['station_train_code'] not in train_set:
            continue

        # 非候补下单，不能预订 或 对应坐席不能预订
        if not candidate and (train_info['canWebBuy'] != 'Y' or not can_buy_seat(train_info, get_value('config_dict')['seatType'])):
            continue

        # 车次未设置，过滤设置时间以前的车次
        if not check_train_code and check_start_time and str(train_info['start_time']) < after_time:
            continue

        # 过滤掉不支持坐席的车次
        if str(train_info['seat_types']).find(seat_type) == -1:
            continue

        # 可候补车次
        if candidate and train_info['houbu_train_flag'] == '1' and train_info['houbu_seat_limit'] == '':
            log('车次' + train_info['station_train_code'] + '可候补，发车时间为 ' + train_info['start_time'] + ', 历时 ' + train_info['lishi'] + '小时')
            candidate_train = detail
            update_cookie_without_uamtk()
            break

        log('车次' + train_info['station_train_code'] + '可购票，发车时间为 ' + train_info['start_time'] + ', 历时 ' +
            train_info['lishi'] + '小时')
        log(json.dumps(train_info))
        update_cookie_without_uamtk()
        return detail

    if candidate_train is not None:
        candidate_process(candidate_train)

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
        seat_type = get_value('config_dict')['seatType']
        if rsp['data']['choose_Seats'].find(seat_type) > -1:
            # 是否可选座位或铺位
            if rsp['data']['canChooseSeats'] == 'Y' or rsp['data']['canChooseBeds'] == 'Y':
                return True
        else:
            return True
    else:
        set_value('ordering', False)
        log('checkOrderInfo失败')
        log(json.dumps(rsp))
    return False

def check_can_confirm_order(rsp):
    if rsp['status']:
        log('余票 : ' + rsp['data']['ticket'] + ', 排队人数 : ' + rsp['data']['count'])
        if rsp['data']['op_2'] != 'false':
            log('目前排队人数已经超过余票张数，请您选择其他席别或车次')
            return False
        return True
    else:
        set_value('ordering', False)
        log('getQueueCount失败')
        log(json.dumps(rsp))
    return False

def check_wait_time(rsp):
    if rsp['status'] and rsp['data']['submitStatus']:
        if rsp['data']['isAsync'] or rsp['data']['isAsync'] == '1':
            return True
    else:
        set_value('ordering', False)
        log('confirmSingleForQueue失败')
        log(json.dumps(rsp))
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
    log('start_timer_job')
    t1.start()
    t2.start()
    t1.join()
    t2.join()

def delay_timer_job(token):
    log('delay_timer_job')
    timer = threading.Timer(1.0, function=timer_job, args=(token, 1))
    timer.start()

def timer_job(token, index):
    disp_time = get_value('disp_time')
    next_request_time = get_value('next_request_time')
    log('execute timer_job index = ' + str(index) + ', disp_time = ' + str(disp_time) + ', next_request_time = ' + str(next_request_time))

    if disp_time <= 0:
        rsp = result_order_for_dc_queue(get_value('orderId'), token)
        if check_order_success(rsp):
            set_value('order_success', True)
            log('订单确认成功, 订单号 = ' + get_value('orderId') + ', 可到待支付订单中确认支付')
            return True
        else:
            set_value('ordering', False)
            log('订单确认失败')
            return False

    if disp_time == next_request_time:
        rsp = query_order_wait_time(token)
        if rsp['status'] and rsp['data']['queryOrderWaitTimeStatus']:
            wait_time = rsp['data']['waitTime']
            if wait_time != -100:
                log(f'等待时长 = {wait_time} 秒')
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
    log('---开始查询---')
    rsp = query_left_tickets()
    if is_success(rsp):
        detail = get_selected_train_detail(rsp)
        # 可能需要调用checkUser接口
        # rsp = check_user()
        # if is_success(rsp) and rsp['data']['flag']:
        if detail is None:
            return False
        log('开始准备提交订单')
        set_value('ordering', True)
        rsp = submit_order(detail, '')
        if is_success(rsp):
            log('获取token')
            token = get_repeat_submit_token()
            log('获取乘客信息列表')
            rsp = get_passengers(token)
            passenger_list = get_order_passengers(rsp)
            if passenger_list is not None and len(passenger_list) > 0:
                log('检查订单信息')
                rsp = check_order_info(passenger_list, token)
                if check_is_can_select_seat_or_bed(rsp):
                    log('开始查看排队数')
                    selected_train_info = detail['queryLeftNewDTO']
                    rsp = get_queue_count(token, selected_train_info)
                    if check_can_confirm_order(rsp):
                        # encrypted_data = exec_js('js/suit.js', 'init', get_cookie())
                        log('确定加入排队队列')
                        rsp = confirm_single_for_queue(token, passenger_list, selected_train_info, '')
                        if check_wait_time(rsp):
                            set_value('disp_time', 1)
                            set_value('next_request_time', 1)
                            log('等待中...')
                            start_timer_job(token)
                            return True
            else:
                set_value('ordering', False)
                log('乘客列表信息获取失败')
                log(json.dumps(rsp))
        else:
            set_value('ordering', False)
            log('submitOrderRequest失败')
            log(json.dumps(rsp))
    else:
        log('余票查询失败 : ' + rsp['messages'])

    return False

def start():
    config_dict = get_value('config_dict')
    delay_time = 0
    # 配置候补下单时，自动查询无效
    if not is_candidate_config():
        if 'timesBetweenTwoQuery' in config_dict:
            delay_time = float(config_dict['timesBetweenTwoQuery'])
            log(f'余票自动查询，间隔为 {delay_time} 秒')

    if delay_time > 0.3:
        set_value('order_success', False)
        set_value('ordering', False)
        while not get_value('order_success'):
            # 仅未提交订单时开始自动查询
            if not get_value('ordering'):
                success = process_from_query_start()
                if not success:
                    time.sleep(delay_time)
            else:
                # 提交订单中，等待时间延长点
                time.sleep(2 * delay_time)
    else:
        log('单次查询开始')
        process_from_query_start()