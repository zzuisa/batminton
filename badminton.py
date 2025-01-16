from datetime import datetime, timedelta
import datetime as dt
import time
import warnings
import logging
import requests
from bs4 import BeautifulSoup
import os
import json
warnings.filterwarnings("ignore")

logging.basicConfig(
    filename='badminton_log.txt',  # 日志文件路径
    level=logging.INFO,  # 设置日志级别（DEBUG, INFO, WARNING, ERROR, CRITICAL）
    format='%(asctime)s - %(levelname)s - %(message)s',  # 日志格式
)

# 记录日志的记录器
logger = logging.getLogger()
def filter_dates_within_two_weeks(date_list, target_days, target_time):
    """
    筛选两周内符合条件的日期

    :param date_list: List[str] 日期列表，格式为 'YYYY-MM-DD HH:MM:SS'
    :param target_days: set[int] 目标星期几集合 (0=周一, 1=周二, ..., 6=周日)
    :param target_time: str 目标时间字符串，格式为 'HH:MM:SS'
    :return: List[str] 符合条件的日期列表
    """
    # 转换为 datetime 对象
    dates = [datetime.strptime(date, '%Y-%m-%d %H:%M:%S') for date in date_list]
    
    # 当前时间
    now = datetime.now()
    
    # 两周后的时间
    two_weeks_later = now + timedelta(weeks=2)
    
    # 转换目标时间为 datetime.time 对象
    target_time_obj = datetime.strptime(target_time, "%H:%M:%S").time()
    
    # 筛选符合条件的日期
    filtered_dates = [
        dt.strftime('%Y-%m-%d %H:%M:%S') for dt in dates
        if now <= dt <= two_weeks_later  # 在两周内
        and dt.weekday() in target_days  # 是目标星期几
        and dt.time() == target_time_obj # 时间是目标时间
    ]
    
    return filtered_dates
def parse_cookies(cookie_str):
    # 创建一个空字典用于存储最终的 cookie 键值对
    cookies = {}

    # 将 cookie 字符串按 ',' 分割
    cookie_items = cookie_str.split(',')

    for item in cookie_items:
        # 去除多余的空格
        item = item.strip()

        # 通过 '=' 分割每个 cookie 的键和值
        if '=' in item:
            key, value = item.split('=', 1)

            # 只保留实际的 cookie 键值对，忽略其他属性
            if key in ['csrf-token', 'sessionid']:  # 可根据实际需求增加更多 cookie 键
                cookies[key] = value.split(';')[0]  # 只保留值，去掉其他信息

    return cookies

# Badminton
def start():
    headers = {
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'accept-language': 'en-US,en;q=0.9',
        'cache-control': 'no-cache',
        'pragma': 'no-cache',
        'priority': 'u=0, i',
        'sec-ch-ua': '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'document',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-site': 'none',
        'sec-fetch-user': '?1',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
    }
    response = requests.get('https://lavo.fun/badminton', headers=headers)
    sk = response.headers['set-cookie']
    # lavo DOC 
    headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Language': 'en-US,en;q=0.9',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
        'Pragma': 'no-cache',
        'cookie': sk,
        'Referer': 'https://lavo.fun/',
        'Sec-Fetch-Dest': 'iframe',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'cross-site',
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
        'sec-ch-ua': '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
    }

    lavo_response = requests.get('https://reservise.com/en/online/lavo/', headers=headers, verify=False)
    lavo_csrf_token=''
    set_cookie = lavo_response.headers['Set-Cookie']
    for cookie in set_cookie.split(';'):
        cookie = cookie.strip()  # 去掉多余的空格
        if cookie.startswith('csrf-token'):
            lavo_csrf_token = cookie.split('=')[1]
            break

    calendar_cookies = {
        'csrf-token': lavo_csrf_token,
    }
    # calendar
    calendar_response = requests.get('https://reservise.com/online/774/calendar/', cookies=calendar_cookies, headers=headers, verify=False)
    # 检查请求是否成功
    # 解析 HTML 内容
    json_data = calendar_response.json()  # 解析为 Python 字典
    # 假设 JSON 中有一个键 "html" 存放 HTML 数据
    html_content = json_data.get("html", "")

    calendar_soup = BeautifulSoup(html_content, 'html.parser')
    # 打印 HTML 内容
    # print(calendar_soup.prettify())
    # 示例：提取所有链接
    calendar_links = [a['data-begin'] for a in calendar_soup.find_all('a', class_="free text-center")]

    ## GET CREATE
    create_response = requests.get('https://reservise.com/online/774/reservation/create/', headers=headers, cookies=calendar_cookies, verify=False)
    create_json_data = create_response.json()
    create_html_content = create_json_data.get("html", "")
    create_soup = BeautifulSoup(create_html_content, 'html.parser')

    # 打印 HTML 内容
    create_csrf = create_soup.find('input', attrs={'name': 'csrfmiddlewaretoken', 'type': 'hidden'})
    step = create_soup.find('input', attrs={'id': 'id_reservation_wizard-current_step', 'type': 'hidden'})
    f_set_cookie = create_response.headers['set-cookie']
    f_cookies = parse_cookies(f_set_cookie)
    csrfmiddlewaretoken = create_csrf.get('value')
    current_step = step.get('value')
    # print(csrfmiddlewaretoken)
    # print(current_step)
    # print(f_cookies)
    return f_cookies, csrfmiddlewaretoken,calendar_links
def getAllDates(f_cookies, calendar_links):
    current_date = datetime.now()
    date_7_days_later = (current_date + timedelta(days=7)).strftime("%Y-%m-%d")
    date_14_days_later = (current_date + timedelta(days=14)).strftime("%Y-%m-%d")
    cookies = f_cookies
    headers = {
        'Accept': '*/*',
        'Accept-Language': 'en-US,en;q=0.9',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        # 'Cookie': 'csrf-token=FQtdgRgQ13oKhc25WlROfOFPyubuwzftb0u319x5jHxAL2XnYzMnoO1iqMXB3eGe; sessionid=v2pty4kdx20kcrzw2l3bi85wu6a59swe',
        'Origin': 'https://reservise.com',
        'Pragma': 'no-cache',
        'Referer': 'https://reservise.com/en/online/lavo/',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-origin',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
        'X-CSRFToken': f_cookies['csrf-token'],
        'X-Requested-With': 'XMLHttpRequest',
        'sec-ch-ua': '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
    }
    data = {
        'begin_date': date_7_days_later,
        'end_date': date_14_days_later,
        'duration': '3600',
    }

    calendar_response2 = requests.post('https://reservise.com/online/774/calendar/', cookies=cookies, headers=headers, data=data, verify=False)
    json_data2 = calendar_response2.json()  # 解析为 Python 字典
    # 假设 JSON 中有一个键 "html" 存放 HTML 数据
    html_content2 = json_data2.get("html", "")

    calendar_soup2 = BeautifulSoup(html_content2, 'html.parser')
    # 打印 HTML 内容
    # print(calendar_soup.prettify())
    # 示例：提取所有链接
    calendar_links2 = []
    calendar_links2 = [a['data-begin'] for a in calendar_soup2.find_all('a', class_="free text-center")]
    calendar_links_all = calendar_links + calendar_links2
    valid_dates_20 = filter_dates_within_two_weeks(calendar_links_all,{1,2,3},"20:00:00")
    valid_dates_21 = filter_dates_within_two_weeks(calendar_links_all,{1,2,3},"21:00:00")
    valid_dates = valid_dates_20 + valid_dates_21
    return valid_dates
#POST CREATE1
def postCreate1(f_cookies, csrfmiddlewaretoken, time_begin):
    cookies = f_cookies
    headers = {
        'Accept': '*/*',
        'Accept-Language': 'en-US,en;q=0.9',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        # 'Cookie': 'csrf-token=FQtdgRgQ13oKhc25WlROfOFPyubuwzftb0u319x5jHxAL2XnYzMnoO1iqMXB3eGe; sessionid=v2pty4kdx20kcrzw2l3bi85wu6a59swe',
        'Origin': 'https://reservise.com',
        'Pragma': 'no-cache',
        'Referer': 'https://reservise.com/en/online/lavo/',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-origin',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
        'X-CSRFToken': f_cookies['csrf-token'],
        'X-Requested-With': 'XMLHttpRequest',
        'sec-ch-ua': '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
    }

    data = {
        'csrfmiddlewaretoken': csrfmiddlewaretoken,
        'reservation_wizard-current_step': 'time',
        'time-duration': '3600',
        'time-begin': time_begin,
    }

    create_response = requests.post('https://reservise.com/online/774/reservation/create/', cookies=cookies, headers=headers, data=data, verify=False)
    # print('create_response',create_response.text)
    create_json_data = create_response.json()
    create_html_content = create_json_data.get("html", "")
    create_soup = BeautifulSoup(create_html_content, 'html.parser')
    
    # 打印 HTML 内容
    create_csrf = create_soup.find('input', attrs={'name': 'csrfmiddlewaretoken', 'type': 'hidden'})
    step = create_soup.find('input', attrs={'id': 'id_reservation_wizard-current_step', 'type': 'hidden'})
    f_set_cookie = create_response.headers['set-cookie']
    f_cookies = parse_cookies(f_set_cookie)
    csrfmiddlewaretoken = create_csrf.get('value')
    # print(csrfmiddlewaretoken)
    # print(current_step)
    # print(f_cookies)
    # 找到 <select> 元素
    select_element = create_soup.find('select', id='id_details-sport_object')
    # 查找所有 <option> 元素并提取 value 属性
    option_values = [option['value'] for option in select_element.find_all('option')]
    return f_cookies, option_values
def postCreate2(csrfmiddlewaretoken, f_cookies,phone_number,sport_object):
    cookies = f_cookies
    headers = {
        'Accept': '*/*',
        'Accept-Language': 'en-US,en;q=0.9',
        # 'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        # 'Cookie': 'csrf-token=dL7kiBFKIaMlACK7NZ7L0rODlngeBKOtYwsUGLNnmN9SgGlgsCAz3Uaxrb8Qy8ut; sessionid=q3eu4qdxq2u4qroymei142zk7ufl9qb7',
        'Origin': 'https://reservise.com',
        'Referer': 'https://reservise.com/en/online/lavo/',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-origin',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
        'X-CSRFToken': f_cookies['csrf-token'],
        'X-Requested-With': 'XMLHttpRequest',
        'sec-ch-ua': '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
    }
    data = [
        ('csrfmiddlewaretoken', csrfmiddlewaretoken),
        ('reservation_wizard-current_step', 'details'),
        ('details-phone_number', phone_number),
        ('details-sport_object', sport_object),
        ('details-single_price_list', '2898'),
        ('details-payment_method', '5'),
        ('details-referral_code', ''),
        ('details-confirm_terms', 'on'),
    ]
    response = requests.post('https://reservise.com/online/774/reservation/create/', cookies=cookies, headers=headers, data=data, verify=False)
    # form_soup = BeautifulSoup(response.json().get("html", ""), 'html.parser')
    # print(form_soup)
    return response

def main(phone_number,date_counter):
    # 获取今天的日期
    today = dt.date.today()
    # 生成从今天到14天后的日期，并为每个日期设置一个计数器
    for i in range(15):  # 从0到14，生成15天
        date = today + dt.timedelta(days=i)
        date_counter[date.strftime("%Y-%m-%d")] = 0  # 初始计数器为 0
    def check(current_date):
        # 获取当前日期
        if current_date in date_counter and date_counter[current_date] == 3:
            logger.info(f"{current_date} -> The number of sessions on the current date is full and no further appointment is required.")  # 记录时间的日志
            return False
        return True    
    
    f_cookies, csrfmiddlewaretoken, calendar_links = start()
    all_dates = getAllDates(f_cookies, calendar_links)
    if len(all_dates) == 0:
        logger.info(f"No eligible slots found: [In two weeks, Tuesday, Wednesday, Thursday, 20:00:00 - 22:00:00]")  # 记录时间的日志
    for time_begin in all_dates:
        if check(time_begin):
            cnt = 0
            logger.info(f"Processing date: {time_begin} ------")  # 记录时间的日志
            f_cookies, csrfmiddlewaretoken, calendar_links = start()
            _f_cookies, option_values = postCreate1(f_cookies, csrfmiddlewaretoken, time_begin)
            logger.info(f"option_values: {option_values}")  # 记录时间的日志
            time.sleep(3)
            for sport_object in option_values:
                time.sleep(3)
                try:
                    _f_cookies, _option_values = postCreate1(f_cookies, csrfmiddlewaretoken, time_begin)
                    if cnt < 3:
                        _res = postCreate2(csrfmiddlewaretoken, _f_cookies, phone_number, sport_object)
                        if _res.status_code == 200:
                            date_counter['time_begin'] += 1
                        logger.info(f"Sport Object {_res}{time_begin}-{sport_object} -> success")  # 记录成功信息
                        cnt += 1
                    continue
                except Exception as e:
                    logger.error(f"Error processing sport object {time_begin}-{sport_object}: {e}")  # 记录异常
                    continue
    logger.info("Processing complete.")
    save_date_counter(date_counter)
# 定义保存和加载函数
def save_date_counter(date_counter, filename='date_counter.json'):
    with open(filename, 'w') as file:
        json.dump(date_counter, file)

def load_date_counter(filename='date_counter.json'):
    if os.path.exists(filename):
        with open(filename, 'r') as file:
            return json.load(file)
    else:
        return {}
# 运行主函数
if __name__ == '__main__':
    date_counter = load_date_counter()
    while True:
        # 获取当前时间
        current_time = datetime.now()
        current_hour = current_time.hour
        current_minute = current_time.minute
        # 检查当前时间是否在 9:00 到 20:00 之间
        if 9 <= current_hour < 20:
            # 每 5 分钟执行一次任务
            main('451283860',date_counter)

            # 等待 5 分钟后再执行
            time.sleep(5 * 60)  # 5 分钟的秒数
        else:
            # 当前时间不在范围内，休眠 60 秒再检查
            time.sleep(60)
