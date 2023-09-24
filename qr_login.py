import base64
import os
import time

from api_login import user_login, redirect_user_login, to_user_auth_center
from api_with_cookie import update_cookie


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
        if rsp == 302:
            time.sleep(1)
            continue
        elif rsp['result_code'] == '2':
            print(rsp['result_message'])
            uamtk = rsp['uamtk']
            break
        time.sleep(1)

def qr_login():
    uuid = create_qr64()
    if uuid is not None:
        check_qr(uuid)

        rsp = user_login()

        if rsp == 302:
            redirect_user_login()

        return to_user_auth_center()
    return None