import json
from urllib.parse import urlencode

import requests

from global_var import set_value, get_value

def init():
    set_value('session', requests.session())
    set_value('cookie', {})

def get_cookie():
    temp_cookies_list = ''
    for k in get_value('cookie').keys():
        temp_cookies_list += (k + '=' + get_value('cookie').get(k) + ';')
    temp_cookies_list = temp_cookies_list[:(len(temp_cookies_list) - 1)]
    return temp_cookies_list

def update_cookie(url, post_data=None, other=None, post_method=True):
    session = get_value('session')
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36',
        'Host': 'kyfw.12306.cn',
    }
    for k in headers.keys():
        session.headers[k] = headers[k]

    if other is not None:
        for k in other.keys():
            session.headers[k] = other[k]

    cookie_str = get_cookie()
    if len(cookie_str) > 0:
        session.headers['Cookie'] = cookie_str

    if post_method:
        if post_data is not None and 'Content-Type' in session.headers and session.headers['Content-Type'].find('application/x-www-form-urlencoded') > -1:
            post_data = urlencode(post_data, safe='/*').encode()
        session_rsp = session.post(url, data=post_data, verify=False)
    else:
        if post_data is not None:
            param = urlencode(post_data)
            finally_url = url + '?%s' % param
        else:
            finally_url = url
        session_rsp = session.get(finally_url, verify=False)
    if session_rsp.status_code == 200:
        session_set_cookie = session_rsp.headers.get('Set-Cookie')
        cookie = get_value('cookie')
        if session_set_cookie is not None:
            # Path=,; route=/cfg
            # Path=/abc, route=/cfg; cmd=test
            # Expire=Thu, 1970
            cookie_items = session_set_cookie.split('; ')
            for cookie_item in cookie_items:
                equals_count = cookie_item.count('=')
                if equals_count > 1:
                    sub_items = cookie_item.split(', ')
                    for child in sub_items:
                        item_key = child.split('=')[0]
                        item_value = child.split('=')[1]
                        if item_key.lower() == 'path':
                            continue
                        else:
                            cookie[item_key] = item_value
                else:
                    item_key = cookie_item.split('=')[0]
                    if item_key.lower() != 'path':
                        item_value = cookie_item.split('=')[1]
                        cookie[item_key] = item_value
        set_value('cookie', cookie)
        # if (post_method or session.headers['Content-Type'].find('application/json') > -1) and is_not_html_content(session_rsp):
        if is_not_html_content(session_rsp):
            return json.loads(session_rsp.content)
        else:
            return session_rsp.content
    else:
        return session_rsp.status_code


def is_not_html_content(rsp):
    return rsp.headers['Content-Type'].find('text/html') == -1