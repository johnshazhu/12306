import json

from api_with_cookie import update_cookie
from global_var import get_value
from log.log import log


def get_passengers(token=None):
    url = 'https://kyfw.12306.cn/otn/confirmPassenger/getPassengerDTOs'
    if token is None:
        return update_cookie(url)

    return update_cookie(url, post_data={
        '_json_att': '',
        'REPEAT_SUBMIT_TOKEN': token
    }, other={
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'
    })

def get_order_passengers(rsp):
    if rsp['status'] and len(rsp['data']['normal_passengers']) > 0:
        order_passengers = []
        for passenger in rsp['data']['normal_passengers']:
            if get_value('config_dict')['passengers'].find(passenger['passenger_name']) != -1:
                order_passengers.append(passenger)
        return order_passengers
    else:
        log('获取乘客列表失败')
        log(json.dumps(rsp))