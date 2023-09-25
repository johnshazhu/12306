import ssl

from config import init_config
from global_var import set_value
from log.log import log
from qr_login import qr_login
from query_and_order import start
from util import is_success


if __name__ == '__main__':
    ssl._create_default_https_context = ssl._create_unverified_context
    if init_config():
        rsp = qr_login()
        set_value('login', 'qr')
        if is_success(rsp) and rsp['data']['is_login'] == 'Y':
            start()
    log('exit')
