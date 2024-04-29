import json
import os
import requests
import urllib3
urllib3.disable_warnings()

from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
f_cookie = os.path.join(BASE_DIR, 'cookie.json')
f_user_info = os.path.join(BASE_DIR, 'user_info.json')

def get_cookies(url, user_name, user_pass, host):
    """
    获取cookie
    """
    payload = {
        'userName': user_name,
        'userPass': user_pass
    }

    headers = {
        'Host': host,
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'X-Requested-With': 'XMLHttpRequest'
    }

    res = requests.post(url=url, data=payload, headers=headers, verify=False)
    cookies = res.cookies.items()

    return cookies


def get_user_info(admin_cookie):
    """
    获取有效的公司
    :param admin_cookie:
    :return:
    """
    payload = {
        'search_type': 'company_code_arr',
        'cu_type': 1,
        'page': 1,
        'pageSize': 2000
    }

    headers = {
        'Host': 'gzbf-admin.goodhmy.com',
        'Cookie': admin_cookie,
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36',
    }

    res = requests.post(
        url=r'https://gzbf-admin.goodhmy.com/customer/distributor/list',
        data=payload,
        headers=headers,
        verify=False
    )

    data = res.json()

    payload_company_code = {
        'company_code[]': []
    }

    all_company = {}
    valid_company = {}

    for item in data.get('data').get('rows'):
        company_name = item.get('company_name')
        user_name = item.get('cu_code')
        user_pass = item.get('cu_password')
        all_company[item.get('cc_code')] = [company_name, user_name, user_pass]

    return all_company


def get_admin_cookie():
    admin_cookie = get_cookies(
        url=r'https://gzbf-admin.goodhmy.com/default/index/login',
        user_name='globaltradeez',
        user_pass='gzbf_aaabbb123456',
        host='gzbf-admin.goodhmy.com'
    )

    admin_cookie[0], admin_cookie[1], admin_cookie[2] = admin_cookie[1], admin_cookie[2], admin_cookie[0]
    admin_cookie = ';'.join(['='.join(i) for i in admin_cookie])

    with open(f_cookie, 'a+', encoding='utf-8') as fa:
        cookie_data = {}
        fa.seek(0)
        if os.path.getsize(f_cookie) != 0:
            cookie_data = json.load(fa)
        cookie_data['admin'] = admin_cookie
        fa.truncate(0)
        json.dump(cookie_data, fa)

    return admin_cookie


def save_user_info(company_code):
    with open(f_user_info, 'w', encoding='utf-8') as fw:
        admin_cookie = get_admin_cookie()
        all_company_info = get_user_info(admin_cookie)
        all_company_info['admin'] = ['admin', 'globaltradeez', 'gzbf_aaabbb123456']
        json.dump(all_company_info, fw)

    return all_company_info[company_code]


def login_save_cookie(company_code):
    with open(f_user_info, 'a+', encoding='utf-8') as fr, \
            open(f_cookie, 'a+', encoding='utf-8') as fw:
        try:
            fr.seek(0)
            user_data = json.load(fr)
        except:
            user_data = {}

        user_info = user_data.get(str(company_code))
        if not user_info:
            user_info = save_user_info(str(company_code))

        if user_info[0] == 'admin':
            cookie = get_admin_cookie()
        else:
            cookies = get_cookies(
                url=r'https://gzbf-shop.goodhmy.com/default/index/login',
                user_name=user_info[1],
                user_pass=user_info[-1],
                host='gzbf-shop.goodhmy.com'
            )
            cookie = '='.join(cookies[-1])
            fw.seek(0)
            cookie_data = json.load(fw)
            cookie_data[company_code] = cookie
            fw.truncate(0)
            json.dump(cookie_data, fw)

    return cookie