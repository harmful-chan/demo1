import json
import os
import re
import time

import requests
import urllib3

from datetime import datetime
from pathlib import Path

from save import Save
from wlog import setup_logging

urllib3.disable_warnings()
BASE_DIR = './'

save = Save()
f_cookie = os.path.join(BASE_DIR, 'cookie.json')


def view_order(cookie='', order_status=1, platform_account_id='',
               order_code='', start_time='', end_time=''):
    """
    获取订单信息
    :param company_name:
    :param order_status:
    :param platform_account_id:
    :param order_code:
    :param start_time:
    :param end_time:
    :return:
    """

    status_temp = {
        '待发货审核': 1,
        '待发货': 2,
        '已发货': 3,
        '问题件': 6,
        '已作废': 7,
        '已放款': 9
    }

    payload = {
        'data[0][name]': 'search_type',
        'data[0][value]': '1',
        'data[4][name]': 'time_type',
        'data[3][name]': 'order_code',
        'data[3][value]': order_code,
        'data[4][value]': '1',
        'data[5][name]': 'time_start',
        'data[5][value]': start_time,
        'data[6][name]': 'time_end',
        'data[6][value]': end_time,
        'data[8][name]':' platform_account_id',
        'data[8][value]': platform_account_id,
        'data[19][name]': 'page',
        'data[19][value]': '1',
        'data[20][name]': 'page_size',
        'data[20][value]': '2000',
        'data[21][name]': 'status',
        'data[21][value]': order_status,
        'data[25][name]': 'is_sub',
        'data[25][value]': '0',
    }

    headers = {
        'Cookie': cookie,
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36',
    }

    res = requests.post(
        url=r'https://gzbf-shop.goodhmy.com/auth/order/manage',
        data=payload, headers=headers, verify=False
    )
    try:
        json_data = res.json()
        if json_data.get('state') == 0:
            return '重新登录'
    except:
        text = res.text
        r = re.findall(r"<body style=.*'>\n(.*?)</br>", text)
        if len(r) > 0:
            return r

    order_info = json_data.get('data')

    return order_info


# 分销成本
def get_distribution_costs(cookie, order_code):
    order_code_str = re.sub(r'(\r\n|\s\n)', ' ', order_code)

    order_info = view_order(cookie, order_code=order_code_str)
    if order_info == '重新登录':
        return '重新登录'

    if type(order_info) is list:
        return '搜不到订单'

    status_temp = {
        '1': '待发货审核',
        '2': '待发货',
        '3': '已发货',
        '4': '缺货',
        '5': '缺货采购中',
        '6': '问题件',
        '7': '已作废',
        '8': '未付款',
        '9': '已放款'
    }

    counts = order_info.get("counts")

    for key, value in counts.items():
        # 如果没有订单就跳过
        if value.get('count') == 0:
            continue

        status = status_temp[key]
        if key not in ['1', '2', '3', '6', '7']:
            return status

        order = view_order(
            cookie=cookie,
            order_status=int(key),
            order_code=order_code_str
        )

        data = order.get('rows')

        for item in data:
            if key in ['6', '7']:
                exception_msg = item.get('exception_msg')
                if exception_msg != '订单已发货' or '取消' in exception_msg:
                    return exception_msg

            order_id = item.get('id')  # 订单ID
            # country = item['orderShipsFrom']  # 物流国家
            distribution_cost = item.get('distribution_costs')  # 分销成本
            # if eval(distribution_cost) == 0:
            #     return 'erp中成本为零无法扣除'

            return {
                'status': status,
                'order_id': order_id,
                'cost': distribution_cost
            }

    return '搜不到订单'


def is_exists(company_code):
    if not os.path.exists(f_cookie):
        save.save_user_info(company_code)
    with open(f_cookie, 'r', encoding='utf-8') as f:
        data = json.load(f)
        cookie = data.get(str(company_code))
        if not cookie:
            cookie = save.login_save_cookie(str(company_code))

    return cookie


# 扣款
def deduct_money(company_code, cookie, cost):
    headers = {
        'Cookie': cookie,
        'Host': 'www.globaltradeez.com',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'X-Requested-With': 'XMLHttpRequest'
    }
    resp = {}
    # 余额
    value_time = requests.post(
        url=r'https://www.globaltradeez.com/customer/customer/get-customer-balance',
        headers=headers, verify=False).json()['data']

    cb_value = value_time['cb_value']

    if eval(cb_value) < eval(cost):
        resp['error'] = f'余额不足, {cb_value}'
        return resp

    # 银行账号   cuba_sub_name   cuba_account   cuba_username
    cuba_account_info = requests.post(
        url=r'https://www.globaltradeez.com/fee/user-bank/list?page=1&limit=2',
        headers=headers, verify=False).json()['data'][0]

    payload_bth_submit = {
        'payment_method': 'BANK',
        'payment_date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'payment_amount': cost,
        'beneficiary_name': cuba_account_info['cuba_username'],
        'beneficiary_sub_bank': cuba_account_info['cuba_sub_name'],
        'beneficiary_account_number': cuba_account_info['cuba_account'],
        'payment_currency': 'RMB'
    }

    headers['Cookie'] = headers['Cookie'] + f'; LANGUAGE=zh_CN; CURRENCY=USD; {company_code}_purchaseStatus=true'

    # 预防提现超时
    max_retries = 3
    click_submit = {}
    for attempt in range(max_retries):
        try:
            click_submit = requests.post(
                url=r'https://www.globaltradeez.com/fee/account-refund-note/save',
                data=payload_bth_submit, headers=headers, verify=False).json()

            if click_submit.get('message'):
                break

        except Exception as e:
            if 'HTTPSConnectionPool' in str(e) and attempt < max_retries - 1:
                time.sleep(1)
                continue
            else:
                break

    if click_submit.get('error'):
        resp['error'] = click_submit['error'][0]
        return resp

    # 找到需要扣款的记录
    while True:
        try:
            record = requests.get(
                url=r'https://www.globaltradeez.com/fee/account-refund-note/list?page=1&limit=2',
                headers=headers, verify=False).json()['data']
            status_name = record[0]['status_name']
            if status_name == '待审核':
                break
        except Exception as e:
            if 'HTTPSConnectionPool' in str(e):
                time.sleep(1)
                continue

    resp['transaction_no_tx'] = record[0]['transaction_no']

    return resp


# 转已发货
def shipped(cookie, o_id):
    headers = {
        'Cookie': cookie,
        'Host': 'gzbf-shop.goodhmy.com',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'X-Requested-With': 'XMLHttpRequest'
    }

    max_retries = 3
    for attempt in range(max_retries):
        try:
            shipped = requests.post(
                url=r'https://gzbf-shop.goodhmy.com/auth/order/manual-shipped', data={'send_data[ids][]': o_id},
                headers=headers, verify=False).json()['data']

            if shipped['success_num'] != 1:
                return '转已发货失败'
            else:
                return '转已发货'

        except Exception as e:
            if 'HTTPSConnectionPool' in str(e) and attempt < max_retries - 1:
                time.sleep(1)
                continue
            else:
                break


# 审核出纳
def audit_teller(admin_cookie, transaction_no_tx):
    resp = {}
    headers = {
        'Cookie': admin_cookie,
        'Host': 'gzbf-admin.goodhmy.com',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'X-Requested-With': 'XMLHttpRequest'
    }

    while True:
        # 找到扣款订单
        data = {'page': 1, 'limit': 20, 'transaction_no': transaction_no_tx}
        deduct_order = requests.post(
            url=r'https://gzbf-admin.goodhmy.com/payment/present/list', data=data,
            headers=headers, verify=False).json()

        if deduct_order['state'] == 0:
            resp['error'] = deduct_order['message']
            return resp

        arn_id = deduct_order['data'][0]['arn_id']
        arn_amount = deduct_order['data'][0]['arn_amount']  # 金额
        arn_currency_code = deduct_order['data'][0]['arn_currency_code']  # 单位

        rp_list = []
        for arn in deduct_order['data']:
            t_no = arn['transaction_no']
            if t_no not in rp_list:
                rp_list.append(t_no)
            else:
                abnormal = requests.post(
                    url=r'https://gzbf-admin.goodhmy.com/payment/present/abnormal?status=1',
                    data={'checkId': arn_id, 'remark_info': '搞错了'},
                    headers=headers, verify=False).json()

                if abnormal['state'] == 0:
                    resp['error'] = '拒绝审核失败'
                else:
                    resp['error'] = '拒绝审核成功'

                return resp

        status_name = deduct_order['data'][0]['status_name']
        if status_name in ['待审核', '待打款']:
            break

    max_retries = 3
    for attempt in range(max_retries):
        try:
            # 确认审核
            if status_name == '待审核':
                audit_status = requests.post(
                    url=r'https://gzbf-admin.goodhmy.com/payment/present/yes?status=1', data={'checkId': arn_id},
                    headers=headers, verify=False).json()

                if audit_status['state'] == 0:
                    resp['error'] = '审核失败'
                    return resp

            time.sleep(1)

            # 出纳
            teller_status = requests.post(
                url=r'https://gzbf-admin.goodhmy.com/payment/present/passed', data={'checkId': arn_id},
                headers=headers, verify=False).json()

            if teller_status['state'] == 0:
                resp['error'] = '出纳失败'
                return resp

            if teller_status['state'] == 1:
                break

        except Exception as e:
            if 'HTTPSConnectionPool' in str(e) and attempt < max_retries - 1:
                time.sleep(1)
                continue
            else:
                resp['error'] = str(e)
                return resp

    result = transaction_no_tx + '\t' + arn_amount + arn_currency_code
    resp['result'] = result

    return resp


def main(in_o):
    in_o_list = [' '.join(item.split()[::2]) for item in in_o.strip().split('\n')]
    temp, cookie = '', ''
    admin_cookie = is_exists('admin')
    res_list = [''] * len(in_o_list)
    now = datetime.now().strftime('%Y-%m-%d')
    f_tx_path = os.path.join(BASE_DIR, f'日志\\{now}\\提现总的.txt')
    log_path = os.path.join(BASE_DIR, f'日志\\{now}\\日志总的.txt')
    logger = setup_logging(log_path)
    logger_tx = setup_logging(f_tx_path, print_=False)
    log_dir_last = os.path.join(BASE_DIR, '日志', '上次')
    os.makedirs(log_dir_last, exist_ok=True)

    index = 0
    gap = None
    o_status = ''
    text_last = ''
    pass_company_code = None
    while index < len(in_o_list):
        try:
            item = in_o_list[index]
            company_code, order_code = item.split()

            if pass_company_code == company_code:
                logger.info(f'此 {company_code} 有出纳报错无法处理，跳过')
                res_list[index] = f'此 {company_code} 有出纳报错无法处理，跳过'
                continue

            template = company_code + ' ' + order_code
            f_last_path = os.path.join(log_dir_last, f'{company_code}.txt')
            if temp != company_code:
                cookie = is_exists(company_code)

            # 分销成本
            costs_info = get_distribution_costs(cookie, order_code)
            if costs_info == '重新登录':
                cookie = save.login_save_cookie(company_code)
                costs_info = get_distribution_costs(cookie, order_code)

            if type(costs_info) is not dict:
                res_list[index] = costs_info
                logger.info(template + ' ' + costs_info)
                # in_o_list.pop(0)
                continue

            o_status, order_id, cost = costs_info.values()
            # 提现
            deduct_info = deduct_money(company_code, cookie, cost)
            time.sleep(1)
            deduct_info_err = deduct_info.get('error')
            transaction_no_tx = deduct_info.get('transaction_no_tx')
            if transaction_no_tx:
                with open(f_last_path, 'a+', encoding='utf-8') as f:
                    f.seek(0)
                    txt = f.readline().split()
                    if txt:
                        transaction_no_tx_last = txt[-1]
                        if transaction_no_tx != transaction_no_tx_last:
                            f.truncate(0)
                            logger_tx.info(template + ' ' + o_status + ' ' + transaction_no_tx + ' ' + cost)
                            f.write(str(index) + ' ' + template + ' ' + o_status + ' ' + transaction_no_tx)
                    else:
                        logger_tx.info(template + ' ' + o_status + ' ' + transaction_no_tx + ' ' + cost)
                        f.write(str(index) + ' ' + template + ' ' + o_status + ' ' + transaction_no_tx)

            if deduct_info_err:
                if '还在审核中' in deduct_info_err:
                    logger.info(f'有未审核的，当前订单 [{index} {template} {o_status}]')
                    # if not os.path.exists(f_last_path):
                    #     dir_last = copy_txt()
                    #     source_file = os.path.join(dir_last, '上次', f'{company_code}.txt')
                    #     shutil.copy(source_file, f_last_path)
                    with open(f_last_path, 'r', encoding='utf-8') as f:
                        text = f.readline().split()
                        index_last = text[0]
                        company_code_last = text[1]
                        order_code_last = text[2]
                        o_status = text[3]
                        transaction_no_tx = text[-1]
                        company_code = company_code_last
                        template = company_code_last + ' ' + order_code_last

                        if text == text_last or index < int(index_last):
                            if order_code_last != order_code:
                                pass_company_code = company_code_last
                                res_list[index] = f'此 {company_code} 有出纳报错无法处理，跳过'
                                logger.info(f'此 {text} 无法处理，跳过。')
                                continue
                            else:
                                index_last = index

                        logger.info(f'优先处理上次还在审核中的 {text}')
                        gap = index - int(index_last)
                        index = int(index_last)
                        text_last = text
                else:
                    res_list[index] = deduct_info_err
                    logger.error(template + ' ' + o_status + ' ' + deduct_info_err)
                    # in_o_list.pop(0)
                    continue

            # 审核出纳
            audit_teller_info = audit_teller(admin_cookie, transaction_no_tx)
            e_message = audit_teller_info.get('error')
            if e_message:
                if e_message == '不存在该用户':
                    admin_cookie = save.login_save_cookie('admin')
                    audit_teller_info = audit_teller(admin_cookie, transaction_no_tx)
                elif e_message == '拒绝审核成功':
                    logger.info(template + ' ' + o_status + ' ' + e_message + ' ' + '再次扣款')
                    index -= 1
                    continue
                else:
                    res_list[index] = e_message
                    logger.error(template + ' ' + o_status + ' ' + e_message)
                    # in_o_list.pop(0)
                    continue

            result = audit_teller_info['result.txt']
            shipped_res = ''
            if o_status == '待发货审核':
                shipped_res = shipped(cookie, order_id)

            res_list[index] = result
            logger.info(template + ' ' + o_status + ' ' + result + ' ' + shipped_res)
            # in_o_list.pop(0)

        except Exception as e:
            res_list[index] = template + ' ' + o_status + ' ' + str(e)
            logger.error(template + ' ' + o_status + ' ' + str(e))
            # in_o_list.pop(0)
            continue

        finally:
            temp = company_code
            if gap:
                index += gap
            else:
                index += 1

            with open(os.path.join(BASE_DIR, '日志/result.txt'), 'w', encoding='utf-8') as f:
                f.write('\n'.join(res_list))

    return res_list


if __name__ == '__main__':
    in_o = '''
    '''
    res = main(in_o)
    print('\n'.join(res))
    print(f'{"结束":-^40}')


