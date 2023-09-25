import datetime

from global_var import get_value


def is_candidate_config():
    candidate = False
    candidate_config = get_value('config_dict')['candidate']
    if candidate_config is not None and candidate_config == '1':
        candidate = True
    return candidate

def get_today_str():
    return datetime.date.today().strftime('%Y-%m-%d')

def is_success(response):
    if response is None:
        return False
    if 'result_code' in response:
        return str(response['result_code']) == '0'
    if 'status' in response:
        return response['status']
    return False

