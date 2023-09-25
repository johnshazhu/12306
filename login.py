from api_login import get_login_config, web_auth_uamtk_static, check_verify
from config import init_config
from global_var import get_value, set_value
from log.log import log
from query_and_order import start
from util import is_success

if __name__ == '__main__':
    if init_config():
        rsp = get_login_config()
        if is_success(rsp):
            rsp = web_auth_uamtk_static()
            is_login = False
            if is_success(rsp):
                is_login = True
                log('已登录')
            else:
                log('未登录')
                check_verify()

            while not is_login:
                can_go_next = get_value('can_go_next')
                if can_go_next:
                    log('登录成功')
                    is_login = True
                    break

            set_value('login', 'psw')
            start()

    log('exit')