import qr
from config import init_config
from global_var import get_value

if __name__ == '__main__':
    if init_config():
        rsp = qr.get_login_config()
        if qr.is_success(rsp):
            rsp = qr.web_auth_uamtk_static()
            is_login = False
            if qr.is_success(rsp):
                is_login = True
                print('已登录')
            else:
                print('未登录')
                qr.check_verify()

            while not is_login:
                can_go_next = get_value('can_go_next')
                if can_go_next:
                    print('登录成功')
                    is_login = True
                    break

            qr.process_from_query_start()