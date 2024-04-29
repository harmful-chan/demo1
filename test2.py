# import os
# from deduct_money import BASE_DIR
#
#
# path = os.path.join(BASE_DIR, '日志2')
# path2 = os.path.join(BASE_DIR, '扣款记录')
#
# aa = os.listdir(path)
# for i in aa:
#     d = os.path.join(path, i)
#     for j in os.listdir(d):
#         if j == '提现总的.txt':
#             t = os.path.join(d, j)
#             with open(t, 'r', encoding='utf-8') as f:
#                 lt = f.readlines()
#                 for k in lt:
#                     sp = k.split()
#                     if len(sp) <= 7:
#                         jiaoyihao = sp[-1]
#                     else:
#                         jiaoyihao = sp[-2]
#
#                     with open(os.path.join(d, '日志总的.txt'), 'r', encoding='utf-8') as fff:
#                         ll = fff.readlines()
#                         for s in ll:
#                             ss = s.split()
#                             if jiaoyihao in ss:
#                                 index = ss.index(jiaoyihao) + 1
#                                 jiner = ss[index]
#                                 pppp = os.path.join(path2, i)
#                                 os.makedirs(pppp, exist_ok=True)
#                                 with open(os.path.join(pppp, f'{sp[4]}.txt'), 'a+', encoding='utf-8') as ff:
#                                     ccc = ss[0:index]
#                                     if '待发货审核' in ccc:
#                                         ccc.remove('待发货审核')
#                                     if '已发货' in ccc:
#                                         ccc.remove('已发货')
#                                     ff.write(' '.join(ccc) + ' ' + jiner + '\n')
# import os
# from datetime import datetime
#
# import openpyxl
# from dateutil.relativedelta import relativedelta
#
# from export_order import base_path
#
# excel_path = base_path / '店铺信息.xlsx'
# workbook = openpyxl.load_workbook(excel_path)
# sheet = workbook.active
#
# c = r'D:\我的坚果云\数据采集\订单数据\2024年03月'
# aa = os.listdir(c)
#
#
#
# for cell in sheet.iter_rows(min_row=2, min_col=1, max_col=10, values_only=True):
#     if cell[5] != '关店':
#         company_name = cell[0] + cell[2] + cell[3] + '_' + cell[4]
#         for i in aa:
#             d = os.path.join(c, i)
#             if cell[4] in i:
#                 os.rename(d, os.path.join(c, company_name))


import sys


#
# def aaa(fun_list):
#     def start_browsers(*args, **kwargs):
#         try:
#             with sync_playwright() as p:
#                 browser = p.chromium.launch_persistent_context(
#                     headless=headless,
#                     user_data_dir=f'./playwright_user_info/{user}',
#                     accept_downloads=True,
#                     args=[
#                         "--accept-insecure-certs",
#                         "--ignore-https-errors",
#                         "--enable-automation",
#                         "--disable-blink-features=AutomationControlled",
#                         "--disable-password-manager-reauthentication",
#                         "--disable-infobars"
#                     ],
#                     permissions=[],
#                     ignore_default_args=["--enable-automation"]
#                 )
#                 page = browser.pages[0]
#                 js = """
#                     Object.defineProperties(navigator, {webdriver:{get:()=>undefined}});
#                 """
#                 page.add_init_script(js)
#                 page.goto('https://csp.aliexpress.com/')
#                 if page.url == r'https://login.aliexpress.com/csp_login.htm?return_url=http://csp.aliexpress.com/':
#                     login_user(page, user, pw)
#                 page.keyboard.down('Escape')
#                 page.wait_for_timeout(1000)
#                 details = page.get_by_role('button', name='查看详情')
#                 if details.count():
#                     details.click()
#                     print(f'{company_name}, 有详情')
#
#                 x = page.query_selector('//div[@role="dialog"]/*[@aria-label="关闭"]')
#                 if x:x.click()
#                 print(f'开始操作 {company_name}')
#                 export_order(company_name, page, s_time, e_time, results)
#                 export_loan(company_name, page, s_time, e_time, results)
#                 export_refund(company_name, page, s_time, e_time, results)
#                 for fun in fun_list:
#                     fun(*args, *kwargs)
#                 print('---------------------------------------')
#
#         except Exception as e:
#             results.put(e)
#
#         return start_browsers


from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent

print(BASE_DIR)