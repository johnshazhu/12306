import base64
import os
import time

from api_login import user_login, redirect_user_login, to_user_auth_center
from api_with_cookie import update_cookie
from log.log import log


def create_qr64():
    url = 'https://kyfw.12306.cn/passport/web/create-qr64'
    rsp = update_cookie(url, post_data={
        'appid': 'otn'
    }, other={
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'
    })
    if rsp['result_code'] == '0':
        image = base64.b64decode(rsp['image'])
        if os.path.exists("resource/qr_image.jpg"):
            os.remove("resource/qr_image.jpg")
        file = open('resource/qr_image.jpg', 'wb')
        file.write(image)
        file.close()
        log(rsp['result_message'])
        return rsp['uuid']
    else:
        log('登录二维码生成失败，code = ' + rsp['result_code'] + ', result_message = ' + rsp['result_message'])
    return None

def check_qr(uuid):
    log('二维码扫描检测中...')
    scan_success = False
    while True:
        url = 'https://kyfw.12306.cn/passport/web/checkqr'
        rsp = update_cookie(url, post_data={
            'appid': 'otn',
            'uuid': uuid
        }, other={
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'
        })
        if rsp == 302:
            time.sleep(1)
            continue
        elif rsp['result_code'] == '0' or rsp['result_code'] == '1':
            time.sleep(1)
            continue
        else:
            log(rsp['result_message'] + ', result_code = ' + rsp['result_code'])
            scan_success = rsp['result_code'] == '2'
            break

    return scan_success

def qr_login():
    uuid = create_qr64()
    if uuid is not None:
        if check_qr(uuid):
            rsp = user_login()

            if rsp == 302:
                redirect_user_login()
                log('redirect_user_login --- 登录成功后更新cookie中的JSESSIONID')

            return to_user_auth_center()
    return None