import asyncio

import aiohttp
import json
import subprocess

from threading import Thread
from playwright.async_api import async_playwright

base_url = 'http://127.0.0.1:6873'
app_id = '202305181108814973326454784'

app_secret = 'MIIEvAIBADANBgkqhkiG9w0BAQEFAASCBKYwggSiAgEAAoIBAQCZ65Zs3aFwhR5dcpVApohsNgZgKBKj6l' \
             'k7Lkt+E/+YtLLAIX3l34uN4IVTGsHJTlVvwOAZCd3zl/FjGD/zDJzw5Kuu+FYafdlta3UOO1HsD+N1S0nloZpg' \
             'H451DtgrOFogJSe9Wq33Q65LFcPw60pv0oYOzWGGmxz5fnNefIRQNcbu5EnAsm+s89LmSDj6vmvmgzZQDVT2L/6yu' \
             'SY/bO8o4Le/jpBCvYX6ZrYFd4J6LfxrhwodMCp79GjRAjA9hCjKGtHu+F9o6y/4rZSmg9O2sB5QOqBQ4t57doEoEDvEf' \
             '82Z9rxDzsRipHAzlk+gcT7g7zE/MZzxOAO0VknU4sh7AgMBAAECggEAPBnHdN7diMgR4T86lDHylv5JYwaCsMpy6S7cf3' \
             'Bjn0b/fRIWzMmK/m0q4hZSkL4rkiVn258EsXck5CK15buJFG7Vss55IIL/gUAyRspW5KwXjtdFFYsScnIf+AlB0y5/0olvi' \
             'Pp9b01YIy1ugwX83MkBW4pKiHrMx4bemYhZSc/6VTKodu0+3GmjqerQQ2d64WblFyMtZb+Kpfu+r+RyUo9iISjIdZL3F+CTWV' \
             'YkIdYjLMQqCAD0kKECcuynGtmJq9q4+pFtMYFLsR7nFQV0sS8aDWGIEv/Z55UUbncaZKsMD9OQNRwR2SoOCS1RJlegquoYLt' \
             '6G7msqatxhR84bsQKBgQDWEuBhw2l5VzW/dmfzixtsFokEA3qD0Ak8gxU8X73fC70tzfVX5XL13B3xoj34LROoP2D56QFt1nUTZ' \
             'Z4X5/OAkaTkqjNyA5mc1meaK21fR15lvUS6aeH+R0WDZlOCy1MsIxvPdZSW3BYZgtbfF4vDsRuF7FFRA10KzrOZlxBPRwKBgQC4' \
             'EMQVq+BIkgqBSMvIC4AK8qxSNhUAo2kzVcVwoUnC36NDB9aMRgxFnur1Tr3q0bEjOWukeuZ7pS54p2dGqEVczBMKNP/AsGIRuBseo' \
             'rzh+KKKSolSMwireAxL+M2pHAN3o6LsPRZ5bERHF43v3i6UZCjfHUSjRha/S1PGtVrfLQKBgANTQ70BBhBmdGVG95Jm5MQnDXXMgAi' \
             'wIJSaDKhlbFOcoRGnE1qMK975zlVEieXi/V0trtny7pzAKg1lFLGWXsfuezs6EZaBy88N3YodhpNmTmcSK5Eht+r1PHUwD7gGZIJZAUO' \
             'Vtfsp7AX1bFUGzpr5k03fP9wcS0OxtkR6fjxdAoGAMjHgR0in0SKCWt9PMy5vrIyhEYpOD+6AMc+iGCTjyJDUJONuTrKLhjD' \
             'gQiVHBVJJzCFMiX46fF1/XsfIEiyxPa0pRA9P72wqUkqympgmijkTmkLZT+E67AfA0rb23rcU+vtU4reF+Xbc58Y0nsUoTq' \
             '9BthZ1MVFbwq74Gag7L8ECgYAu4NSoDCu0QkIee5UxF97hntQHSipIAqLwoX4v7l5xsGcyR1NuGwKR10tXm9s0JibfegMLax' \
             '5Lec6EMG9H8gr0zTMTsaRxiwClTkYgs18VIKQEHLsrUmvYTwmT9WROWl3gjyspZEB0bhiK8RUWSlVwRwoPzeL1jPXYdBWzASXvuQ=='

group_code = '11429245'


def run_hubstudio_connector():
    command = r'D:\Program Files\Hubstudio\hubstudio_connector.exe'
    arguments = [
        '--server_mode=http',
        '--threads=20',
        '--http_port=6873',
        f'--app_id={app_id}',
        f'--group_code={group_code}',
        f'--app_secret={app_secret}'
    ]

    full_command = [command] + arguments

    try:
        process = subprocess.Popen(full_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, text=True, encoding='utf-8')

        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                print(output.strip())

        process.communicate()

    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")
        return str(e), "", 1


async def request_(url, headers=None, data=None, method='get'):
    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(limit=64, ssl=False)) as session:
        async with session.request(method=method, url=url, data=json.dumps(data), headers=headers) as response:
            return await response.json()


async def get_env():
    # 所有环境名
    env_code_info = {}

    # 获取环境列表
    url = f"{base_url}/api/v1/env/list"
    headers = {'Content-Type': 'application/json'}
    data = {
        "current": 1,
        "size": 200,
        "tagNames": ['寰球运营']  # , '自运营', '联合运营'
    }
    result = await request_(url, headers, data, method='post')

    if result['code'] == 0:
        for env in result['data']['list']:
            container_code = env['containerCode']
            container_name = env['containerName']
            env_code_info[container_name] = container_code

    return env_code_info


async def get_browser_context(playwright, debugging_port):
    browser = await playwright.chromium.connect_over_cdp("http://127.0.0.1:" + str(debugging_port))
    browser_context = browser.contexts[0]

    return browser_context


async def start_env(container_code):
    # 打开环境
    url = f"{base_url}/api/v1/browser/start"
    headers = {'Content-Type': 'application/json'}
    data = {
        "containerCode": container_code,
        "isHeadless": True,
        "skipSystemResourceCheck": True,
        # "containerTabs": ["https://csp.aliexpress.com/"],
        "args": [
            '--disable-infobars',
            '--disable-blink-features=AutomationControlled',
            '--blink-settings=imagesEnabled=false'
        ]  # "--headless=new",
    }
    result = await request_(url, headers, data, method='post')
    if result['code'] == 0:
        debugging_port = result['data']['debuggingPort']
        async with async_playwright() as playwright:
            browser = await get_browser_context(playwright, debugging_port)
            page = await browser.new_page()
            js = """
                    Object.defineProperties(navigator, {webdriver:{get:()=>undefined}});
                    """
            await page.add_init_script(js)
            await page.goto('https://csp.aliexpress.com/')
            await page.locator("//div[@class='ae-layout-menu-item-inner']//div[string()='交易']").click()
            await page.wait_for_timeout(1000)
            await page.locator("//div[@class='ae-layout-menu-item-inner']//a[string()='所有订单']").click()
            await page.locator("//div[@class='ui-board-wrap PageCard reload-none']//*[text()='今日新订单']").click()

            order_count = await page.locator(
                "//div[@class='ui-board-wrap PageCard reload-none']//*[text()='今日新订单']/preceding-sibling::span"
            ).text_content()


async def main():
    subprocess_thread = Thread(target=run_hubstudio_connector)
    subprocess_thread.start()
    await asyncio.sleep(3)
    env_code_info = await get_env()
    with open("店铺名.txt", 'r', encoding='utf-8') as f:
        text = f.readlines()

    tasks = []
    for name in text:
        if name == '':
            continue
        code = env_code_info[name.strip('\n')]
        tasks.append(start_env(code))
    await asyncio.gather(*tasks)


if __name__ == "__main__":
    asyncio.run(main())

