import os
import queue
import threading
import openpyxl

from datetime import datetime
from pathlib import Path

from dateutil.relativedelta import relativedelta
from playwright.sync_api import sync_playwright

base_path = Path(__file__).resolve().parent
excel_path = base_path / '店铺信息 - 副本.xlsx'

now = datetime.now()
date = now.date() - relativedelta(months=1)
save_path = Path(rf'D:\我的坚果云\数据采集\订单数据\{date.strftime("%Y年%m月")}')


def start_browsers(company_name, user, pw, s_time, e_time, results, headless=False):
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch_persistent_context(
                headless=headless,
                user_data_dir=f'./playwright_user_info/{user}',
                accept_downloads=True,
                args=[
                    "--accept-insecure-certs",
                    "--ignore-https-errors",
                    "--enable-automation",
                    "--disable-blink-features=AutomationControlled",
                    # "--disable-password-manager-reauthentication",
                    "--disable-infobars"
                ],
                permissions=[],
                ignore_default_args=["--enable-automation"]
            )
            page = browser.pages[0]
            js = """
                Object.defineProperties(navigator, {webdriver:{get:()=>undefined}});
            """
            page.add_init_script(js)
            page.goto('https://csp.aliexpress.com/')
            if page.url == r'https://login.aliexpress.com/csp_login.htm?return_url=http://csp.aliexpress.com/':
                login_user(page, user, pw)
            page.keyboard.down('Escape')
            page.wait_for_timeout(1000)
            details = page.get_by_role('button', name='查看详情')
            if details.count():
                details.click()
                print(f'{company_name}, 有详情')

            x = page.query_selector('//div[@role="dialog"]/*[@aria-label="关闭"]')
            if x:x.click()
            print(f'开始操作 {company_name}')
            export_order(company_name, page, s_time, e_time, results)
            export_loan(company_name, page, s_time, e_time, results)
            export_refund(company_name, page, s_time, e_time, results)
            print('---------------------------------------')

    except Exception as e:
        results.put(e)


def get_month(start_time, end_time):
    begin = datetime.strptime(start_time, "%Y-%m-%d")
    end = datetime.strptime(end_time, "%Y-%m-%d")
    begin_year, end_year = begin.year, end.year
    begin_month, end_month = begin.month, end.month
    if begin_year == end_year:
        range_count = end_month - begin_month
    else:
        range_count = (end_year - begin_year) * 12 + end_month - begin_month

    return range_count, begin_year, end_year, begin_month


def export_refund(company_name, page, start_time, end_time, results):
    page.click('//*[@id="TabContainerValue"]//div[string()="订单退款记录"]')

    r_count, b_y, e_y, s_m = get_month(start_time, end_time)
    temp = [1, 3, 5, 7, 8, 10, 12]
    for i in range(r_count+1):
        m = s_m + i
        if m > 12:
            m -= 12
            b_y = e_y
        start_time = f'{b_y}-{m:0>2d}-01'
        end_time = f'{b_y}-{m:0>2d}-{29 if m == 2 else 31 if m in temp else 30}'
        page.click('//*[@id="orderRefundTime"]//input[@placeholder="开始时间"]')
        s_input = page.wait_for_selector("(//input[@placeholder='YYYY-MM-DD'])[1]")
        s_input.fill(start_time)
        s_input.press('Enter')
        page.wait_for_timeout(1000)
        e_input = page.wait_for_selector("(//input[@placeholder='YYYY-MM-DD'])[2]")
        e_input.fill(end_time)
        e_input.press('Enter')
        page.click('//div[@class="next-date-picker-panel-footer"]/button[text()="确定"]')
        page.wait_for_timeout(1000)
        no_data = page.query_selector('//*[@id="orderRefundTable"]//div[string()="暂无数据"]')
        if no_data:
            continue

        page.click('//*[@id="Button_l417bso7"]/button[string()="导出明细"]')

        with page.expect_download() as download_info:
            page.click(
                '//*[@id="detailTable"]//tr[@class="next-table-row first"]//a[string()="下载报表"]',
                timeout=20000
            )
        download = download_info.value
        path = save_path / company_name
        os.makedirs(path, exist_ok=True)
        download.save_as(str(path / f'退款_{b_y}{m:0>2d}.xlsx'))
        print(f'{company_name}, 退款_{b_y}{m:0>2d}，下载成功')
        page.click('//*[contains(@class, "next-dialog-footer")]//button[text()="取消"]')


def export_loan(company_name, page, start_time, end_time, results):
    page.click('//*[@class="aside-menu"]//li//span[text()="资金"]')
    page.click('//*[@class="aside-menu"]//li[@title="资金管理"]')
    page.wait_for_load_state()
    page.click('//*[@id="newOverviewTabContent"]//div[string()="订单记录"]')
    page.click('//*[@id="TabContainerValue"]//div[string()="订单放款记录"]')

    r_count, b_y, e_y, s_m = get_month(start_time, end_time)
    temp = [1, 3, 5, 7, 8, 10, 12]
    for i in range(r_count+1):
        m = s_m + i
        if m > 12:
            m -= 12
            b_y = e_y
        start_time = f'{b_y}-{m:0>2d}-01'
        end_time = f'{b_y}-{m:0>2d}-{29 if m == 2 else 31 if m in temp else 30}'
        page.click('//*[@id="orderLoanTime"]//input[@placeholder="开始时间"]')
        s_input = page.wait_for_selector("(//input[@placeholder='YYYY-MM-DD'])[1]")
        s_input.fill(start_time)
        s_input.press('Enter')
        page.wait_for_timeout(1000)
        e_input = page.wait_for_selector("(//input[@placeholder='YYYY-MM-DD'])[2]")
        e_input.fill(end_time)
        e_input.press('Enter')
        page.click('//div[@class="next-date-picker-panel-footer"]/button[text()="确定"]')
        page.wait_for_timeout(1000)
        no_data = page.query_selector('//*[@id="orderLoanTable"]//div[string()="暂无数据"]')
        if no_data:
            continue

        page.click('//*[@id="Button_l417bsnn"]/button[string()="导出明细"]')

        with page.expect_download() as download_info:
            page.click(
                '//*[@id="detailTable"]//tr[@class="next-table-row first"]//a[string()="下载报表"]',
                timeout=20000
            )
        download = download_info.value
        path = save_path / company_name
        os.makedirs(path, exist_ok=True)
        download.save_as(str(path / f'放款_{b_y}{m:0>2d}.xlsx'))
        print(f'{company_name}, 放款_{b_y}{m:0>2d}，下载成功')
        page.click('//*[contains(@class, "next-dialog-footer")]//button[text()="取消"]')


def export_order(company_name, page, start_time, end_time, results):
    page.click('//*[@class="aside-menu"]//li//span[text()="交易"]')
    page.click('//*[@class="aside-menu"]//li[@title="订单批量导出"]')
    page.locator("//input[@placeholder='开始时间']").click()
    s_input = page.wait_for_selector("(//input[@placeholder='YYYY-MM-DD'])[1]")
    s_input.fill(start_time)
    s_input.press('Enter')
    page.wait_for_timeout(1000)
    e_input = page.wait_for_selector("(//input[@placeholder='YYYY-MM-DD'])[2]")
    e_input.fill(end_time)
    e_input.press('Enter')
    page.wait_for_timeout(1000)
    hms_input = page.wait_for_selector("(//input[@placeholder='HH:mm:ss'])[2]")
    hms_input.fill('23:59:59')
    hms_input.press('Enter')
    page.click("//span[string()='导出订单']")
    page.wait_for_timeout(1000)

    while True:
        msg = page.query_selector("//div[@class='next-overlay-wrapper opened']")
        if not msg:
            page.wait_for_timeout(1000)
            break

    with page.expect_download() as download_info:
        page.click(
            '//tr[@class="next-table-row first"]/td[@data-next-table-row="0"]//a[string()="下载"]',
            timeout=50000
        )
    download = download_info.value
    path = save_path / company_name
    os.makedirs(path, exist_ok=True)
    download.save_as(str(path / '订单.xlsx'))
    print(f'{company_name}, 订单 - {start_time} - {end_time}，下载成功')


def order_day(page, results):
    page.get_by_text('交易').click()
    page.get_by_text('所有订单').click()
    page.wait_for_load_state()
    o_number_el = page.wait_for_selector(
        "//div[@class='ui-board-wrap PageCard reload-none']//*[text()='今日新订单']/preceding-sibling::span"
    )
    o_number = o_number_el.text_content()
    if int(o_number) > 0:
        o_number_el.click()
        if int(o_number) > 10:
            page.locator(
                "//div[@data-spm='pagination']//span[@class='next-input next-medium next-select-inner']"
            ).click()
            page.locator(
                "//div[@class='next-overlay-wrapper opened']//li[@title='100']"
            ).click()

    results.append(o_number)
    print(o_number)

    return results


def slider_verification(page, iframe):
    iframe.wait_for_selector('#nc_1__scale_text')
    box = iframe.locator('#nc_1__scale_text').bounding_box()
    print(box)
    x = box["x"] + 10
    y = box["y"] + box["height"] / 2
    target_x = x + box["width"]
    page.mouse.move(x, y)
    page.mouse.down()
    page.mouse.move(target_x, y)
    page.mouse.up()


def login_user(page, user, pw):
    page.locator('#fm-login-id').fill(user)
    page.locator('#fm-login-password').fill(pw)
    page.locator('button[type="submit"]').click()
    login_check = page.query_selector("#baxia-login-check-code")
    if not login_check:
        return
    page.wait_for_selector('iframe')
    iframe = page.frames[-1]
    slider_verification(page, iframe)
    page.wait_for_timeout(1000)
    refresh = iframe.query_selector("//div[@id='`nc_1_refresh1`']")
    if refresh:
        refresh.click()
        slider_verification(page, iframe)
    page.wait_for_load_state()


def start_threading(batch_list, threads, s_time, e_time, results, headless):
    for user_info in batch_list:
        company_name = user_info[0]
        user, pw = user_info[-2], user_info[-1]
        thread = threading.Thread(
            target=start_browsers,
            args=(company_name, user, pw, s_time, e_time, results, headless)
        )
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

    batch_list = []

    if not results.empty():
        print(f'{company_name}-------未完成')
        with open(os.path.join(base_path, '未完成店铺.txt'), 'a+', encoding='utf-8') as f:
            f.writelines(' '.join(user_info))
            f.write('\n')


def main(batch_size, s_time, e_time, headless):
    workbook = openpyxl.load_workbook(excel_path)
    sheet = workbook.active
    user_list = []
    results = queue.Queue()
    threads = []

    with open(os.path.join(base_path, '未完成店铺.txt'), 'r+', encoding='utf-8') as f:
        lines = f.readlines()
        if lines:
            for user_info in lines:
                company_name, user, pw = user_info.strip('\n').split()
                user_list.append([company_name, user, pw])

            for i in range(0, len(user_list), batch_size):
                batch_list = user_list[i: i + batch_size]
                start_threading(batch_list, threads, s_time, e_time, results, headless)

            f.seek(0)
            f.truncate()
        else:
            for cell in sheet.iter_rows(min_row=2, min_col=1, max_col=10, values_only=True):
                if cell[7] != '关店':
                    company_name = cell[0] + cell[2] + cell[3] + '_' + cell[4]
                    user, pw = cell[8], cell[9]
                    user_list.append([company_name, user, pw])

            for i in range(0, len(user_list), batch_size):
                batch_list = user_list[i: i + batch_size]
                start_threading(batch_list, threads, s_time, e_time, results, headless)


if __name__ == '__main__':
    start_time = '2023-06-01'
    end_time = '2024-03-31'
    batch_size = 2  # 并行个数
    headless = False  # 是否显示浏览器
    main(batch_size, start_time, end_time, headless)
    print(f'{"完成":-^20}')