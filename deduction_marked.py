import os
import time
from datetime import datetime

import requests

from script_deduct_money import is_exists, BASE_DIR, get_distribution_costs, deduct_money, audit_teller, shipped
from user_info.scripts import save
from wlog import setup_logging


def send_out(cookie, order_id, logistics, tracking_number):
    send_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    shipping_url = 'https://t.17track.net/en#nums=' + tracking_number

    # logistics = {
    #     'spain': 'CORREOS',
    #     'brazil': 'CORREIOS_L_BR',
    #     'United States': ['FEDEX_US', 'USPS', 'UPS']
    # }
    #
    # pattern_ups = r'\b1Z[a-zA-Z0-9]{16}\b'
    # pattern_usps = r'\b(?:M\d{9}|M\d{10}|\d{10}|\d{20}|\d{22}|\d{26}|\d{28}|\d{30}|\d{34}|[A-Za-z]{2}\d{9}US)\b'
    #
    # if country == 'United States':
    #     if len(tracking_number) != 12:
    #         ups = re.findall(pattern_ups, tracking_number)
    #         usps = re.findall(pattern_usps, tracking_number)
    #         if ups:
    #             platform_carrier_code = 'UPS'
    #         if usps:
    #             platform_carrier_code = 'USPS'
    #     else:
    #         platform_carrier_code = 'FEDEX_US'
    # else:
    #     # 承运商
    #     platform_carrier_code = logistics[country]

    data, headers = {}, {}
    data['data[orders][0][id]'] = order_id
    data['data[orders][0][platform_carrier_code]'] = logistics
    data['data[orders][0][send_date]'] = send_date
    data['data[orders][0][shipping_url]'] = shipping_url
    data['data[orders][0][tracking_number]'] = tracking_number

    headers['Cookie'] = cookie
    headers['Host'] = 'gzbf-shop.goodhmy.com'
    headers['User-Agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36'
    headers['X-Requested-With'] = 'XMLHttpRequest'

    res = requests.post(
        url=r'https://gzbf-shop.goodhmy.com/auth/shipping/save-service',
        data=data, headers=headers, verify=False
    )

    out_status = res.json()
    if out_status['success_num'] == 1:
        return '标发成功'
    else:
        message = out_status['message']
        if '订单处理失败' in message[0]:
            res_again = requests.post(
                url=r'https://gzbf-shop.goodhmy.com/auth/shipping/save-service',
                data=data, headers=headers, verify=False
            )
            out_status_again = res_again.json()
            if out_status_again['success_num'] == 1:
                return '标发成功'
            else:
                return '标发失败！！！！！'
        else:
            return '标发失败！！！！！'


def main(in_o):
    now = datetime.now().strftime('%Y年%m月%d日')
    log_path = os.path.join(BASE_DIR, f'日志\\日志总的.txt')
    logger = setup_logging(log_path)

    leaflet = False
    o_split = in_o.strip().split('\n')
    is_leaflet = len(o_split[0].split()[1])
    if is_leaflet > 10:
        in_o_list = o_split
        leaflet = True
        logger.info(f'正在处理的是，促销单')
    else:
        in_o_list = [' '.join(item.split()[::2]) for item in o_split]

    temp, cookie = '', ''
    admin_cookie = is_exists('admin')
    res_list = [''] * len(in_o_list)
    record_path = os.path.join('D:\\我的坚果云\\数据采集\\扣款记录', now)
    f_tx_path = os.path.join(BASE_DIR, f'日志\\提现总的.txt')
    logger_tx = setup_logging(f_tx_path, print_=False)
    log_dir_last = os.path.join(BASE_DIR, '日志', '上次')
    os.makedirs(log_dir_last, exist_ok=True)
    os.makedirs(record_path, exist_ok=True)

    index = 0
    gap = None
    o_status = ''
    text_last = ''
    pass_company_code = None
    while index < len(in_o_list):
        try:
            item = in_o_list[index]
            if leaflet:
                company_code, order_code, tracking_number, logistics = item.split()
            else:
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
                continue

            o_status, order_id, cost = costs_info.values()

            if eval(cost) == 0:
                if not manual_cost:
                    res_list[index] = 'erp中成本为零无法扣除'
                    logger.info(template + ' erp中成本为零无法扣除')
                    continue
                else:
                    cost = str(manual_cost)
                    logger.info(template + f' 手动扣款金额 {cost}')

            if e_cost:
                cost = str(manual_cost)
                logger.info(template + f' 手动扣款金额 {cost}')

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

                    with open(f_last_path, 'r', encoding='utf-8') as f:
                        text = f.readline().split()
                        index_last = text[0]
                        company_code_last = text[1]
                        order_code_last = text[2]
                        o_status = text[3]
                        transaction_no_tx = text[-1]
                        company_code = company_code_last
                        template = company_code_last + ' ' + order_code_last

                        if text == text_last or index < int(index_last) or int(index_last) == 0:
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
                    continue

            result = audit_teller_info['result']
            shipped_res = ''
            if o_status == '待发货审核':
                shipped_res = shipped(cookie, order_id)

            if leaflet:
                res_list[index] = result.split()[0]
                send_res = send_out(cookie, order_id, logistics, tracking_number)
                logger.info(template + ' ' + o_status + ' ' + result + ' ' + shipped_res + ' ' + send_res)
            else:
                res_list[index] = result
                logger.info(template + ' ' + o_status + ' ' + result + ' ' + shipped_res)

            with open(os.path.join(record_path, f'{order_code}.txt', ), 'a+', encoding='utf-8') as w_record:
                t = datetime.now().strftime('%Y-%m-%d %H:%M')
                w_record.write(t + ' - ' + template + ' ' + result + '\n')

        except Exception as e:
            res_list[index] = template + ' ' + o_status + ' ' + str(e)
            logger.error(template + ' ' + o_status + ' ' + str(e))
            continue

        finally:
            temp = company_code
            if gap:
                index += gap
            else:
                index += 1

            with open(os.path.join(BASE_DIR, '日志/result.txt'), 'w') as f:
                f.write('\n'.join(res_list))

    return res_list


if __name__ == '__main__':
    in_o = '''  
5377235	1	8187116030025620
5377235	1	8187510788601401
5377235	1	8187622135583412
5377235	1	8187628778729138
5377150	1	8187839671535613
5377096	1	8187409801059131
5377096	1	8187633652007725
5377235	1	8187029867849138
5377235	1	8187493986599372
5377235	1	8187817997041498
5377235	1	8187015929182354
5377235	0	8187649252867904
5377003	1	8187506785753175
5377003	1	8186950496073594
5377003	1	8187429401835328
5376745	1	8187027201824917
5376798	2	8187383167791036
5376798	1	8187495663485442
5376798	2	8186958002571965
5376798	0	8186956412324645
5376798	0	8187652294177511
5376745	7	8186800823828531
    '''
    # 每一次手动填写金额扣款完成后，记得恢复 默认值
    e_cost = False  # 成本扣错了，例如 只扣了 0.071 时 改为 e_cost = True，epr中成本为零时不用管，默认值为 e_cost = False
    manual_cost = ''   # 手动扣款金额, 需要手动扣款时，才填，默认值为 manual_cost = ''

    res = main(in_o)
    print('\n'.join(res))
    print(f'{"结束":-^40}')