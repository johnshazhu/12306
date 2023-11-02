import json

import handle_sms_code
import notification_util
from api_with_cookie import update_cookie
from global_var import set_value, get_value
from log.log import log
from util import is_success

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
    log('查看是否已登录')
    return update_cookie('https://kyfw.12306.cn/passport/web/auth/uamtk-static', post_data={
            'appid': 'otn'
        }, other={
            'Content-Type': 'application/x-www-form-urlencoded'
        })

def conf():
    return update_cookie('https://kyfw.12306.cn/index/otn/login/conf')

def get_login_config():
    log('获取登录配置')
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
        log('滑块方式验证暂不支持')
    elif rsp['login_check_code'] == '3':
        log('短信验证码方式验证')
        rsp = get_sms_code()
        if is_success(rsp):
            notification_util.show_notification('短信验证码', '请注意查看短信验证码并输入')
            handle_sms_code.input_sms_code(submit_sms_code_callback)
        else:
            log(rsp['result_message'])
    else:
        log(json.dumps(rsp))

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
    log('获取短信验证码')
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
    log('to_user_auth_center --- 用户中心统一认证')
    rsp = uamtk()
    if is_success(rsp):
        tk = rsp['newapptk']
        if tk is None:
            tk = rsp['apptk']
        rsp = uamauthclient(tk)
        if is_success(rsp):
            user_login()
            log('user_login --- 更新cookie uKey')
            rsp = conf()
            log('conf --- 获取配置信息，is_login = ' + rsp['data']['is_login'])
            if is_success(rsp):
                set_value('queryUrl', rsp['data']['queryUrl'])
            set_value('can_go_next', is_success(rsp) and rsp['data']['is_login'] == 'Y')
            return rsp
        else:
            log('uamauthclient : ' +  rsp['result_message'] + ', result_code = ' + str(rsp['result_code']))
    else:
        log('uamtk : ' + rsp['result_message'] + ', result_code = ' + str(rsp['result_code']))


def process_start_from_login():
    log('开始调用web/login接口登录')
    rsp = web_login()
    session = get_value('session')
    if 'isPasswordCopy' in session.headers:
        del session.headers['isPasswordCopy']
        set_value('session', session)
    if rsp['result_code'] == 0:
        log('跳转otn/login/userLogin')
        rsp = user_login()
        if rsp == 302:
            redirect_user_login()
        to_user_auth_center()
    elif rsp['result_code'] == 91 or rsp['result_code'] == 92 or rsp['result_code'] == 94 or rsp['result_code'] == 95 or rsp['result_code'] == 97:
        is_uam_login = get_value('is_uam_login')
        if is_uam_login:
            to_user_auth_center()
    elif rsp['result_code'] == 101:
        log('您的密码很久没有修改了，为降低安全风险，请您重新设置密码后再登录')
    else:
        log(rsp['result_message'])

def web_login():
    return update_cookie('https://kyfw.12306.cn/passport/web/login', post_data=get_value('config_obj').__dict__, other={
        'isPasswordCopy': 'N',
        'Referer': 'https://kyfw.12306.cn/otn/resources/login.html',
        'Content-Type': 'application/x-www-form-urlencoded;application/json;charset=UTF-8',
        'Origin': 'https://kyfw.12306.cn',
    })

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