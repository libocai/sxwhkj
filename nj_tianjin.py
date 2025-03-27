import json
import os
from time import sleep

import jsonlines
import requests
from selenium import webdriver
from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

# 设置 Chrome for Testing 的路径
chrome_path = "/Users/cailibo/Documents/tools/chrome-mac-arm64/Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing"  # 将此路径替换为实际 Chrome for Testing 的路径
# 配置 Chrome 选项
chrome_options = Options()
chrome_options.binary_location = chrome_path  # 指定 Chrome for Testing 的二进制文件位置
chrome_options.add_argument("--headless")  # 无头模式
# chrome_options.add_argument("--disable-gpu")  # 如果系统支持 GPU，加快无头模式
# chrome_options.add_argument("--no-sandbox")  # 一些环境需要此参数
# chrome_options.add_argument("--disable-dev-shm-usage")  # 防止资源不足导致的启动卡顿
# chrome_options.add_argument("--disable-extensions")  # 禁用扩展
# chrome_options.add_argument("--disable-blink-features=AutomationControlled")  # 隐藏自动化特征

# 启动 Chrome 浏览器
driver = webdriver.Chrome(options=chrome_options)

"""
o = "e3xFjZ4ezDBUbyMbdwwTH+GzxbOe7kHsn4YNMr1j4KerhffMsEXu5GEVad4hpIj2XRQkBRAfKFhk1u5IlLdKLw==";

function d(e) {
            var t = l.encrypt(e, o);
            return t
        }

{"applyType":1,"year":2025,"buyerName":"","code":"","areaCode":"","status":"","distributor":"","enterpriseId":"","factoryNumber":"","purchaseDateStart":"","purchaseDateEnd":"","pageNum":2,"pageSize":15}
"""


def get_province_details(url_local, province_name_local, district, year, page_index):
    driver.get(url_local)
    sleep(2)

    # 1. 点击菜单，使其展开
    search_form_box = driver.find_element(By.ID, "search-form-box")
    dropdown_toggle = search_form_box.find_element(By.CLASS_NAME, "select-dropdown")
    dropdown_toggle.click()
    sleep(1)  # 等待菜单展开

    # 2. 选择年份项（例如选择 2022 年）
    year_option = driver.find_element(By.XPATH, "//li[text()='" + year + "']")
    year_option.click()

    # 点击“查询”按钮
    search_button = driver.find_element(By.XPATH, "//button[contains(text(), '查询')]")
    search_button.click()
    sleep(2)

    # 使用requests请求分页数据

    if page_index:
        find_page_index = True
        while find_page_index:
            try:
                page_item_element = driver.find_element(By.CLASS_NAME, "pagerItem")
                page_item_list = page_item_element.find_elements(By.TAG_NAME, "a")
                for index, page_item in enumerate(page_item_list):
                    page_no = page_item.text
                    if page_no == str(page_index):
                        find_page_index = False
                        page_item_list[index + 1].click()
                    if index >= len(page_item_list) / 2 and page_no == '...':
                        print('current page ' + page_item_list[index - 1].text)
                        page_item.click()
                        sleep(1)

            except StaleElementReferenceException:
                print("元素变得不可用，重新定位元素")
                sleep(1)  # 稍等片刻再重新获取元素
            except Exception as e:
                print("翻页结束或出错:", e)
                break  # 如果找不到“下一页”按钮，退出循环

    has_next_page = True

    while has_next_page:
        # 等待页面渲染完成并获取 tbody
        WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.TAG_NAME, "tbody"))
        )

        # 等待 tbody 内部的 tr 标签加载完成
        WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.TAG_NAME, "tr"))
        )
        # 筛选table节点
        tbody_element = driver.find_element(By.TAG_NAME, "tbody")
        # 获取 <tbody> 下的所有 <tr> 行
        rows = tbody_element.find_elements(By.TAG_NAME, "tr")
        # 遍历每一行 <tr> 并获取所有 <td> 单元格内容
        for row in rows:
            # 获取当前行中的所有 <td> 单元格
            cells = row.find_elements(By.TAG_NAME, "td")
            # 提取并打印每个单元格中的文本
            row_data = [cell.text for cell in cells]
            print(row_data)
            with jsonlines.open(province_name_local + "_" + year + ".json", mode='a') as writer:
                writer.write(row_data)  # 自动处理每行写入
        # 定位“下一页”按钮
        try:
            page_item_element = driver.find_element(By.CLASS_NAME, "pagerItem")
            page_item_list = page_item_element.find_elements(By.TAG_NAME, "a")
            for index, page_item in enumerate(page_item_list):
                if 'current' == page_item.get_attribute("class") and index == len(page_item_list) - 3:
                    has_next_page = False
                if 'current' == page_item.get_attribute("class"):
                    print('current page ' + page_item_list[index + 1].text)
                    page_item_list[index + 1].click()
                    sleep(2)

        except StaleElementReferenceException:
            print("元素变得不可用，重新定位元素")
            sleep(1)  # 稍等片刻再重新获取元素
        except Exception as e:
            print("翻页结束或出错:", e)
            break  # 如果找不到“下一页”按钮，退出循环


def sendRequest(url, year, page_index, token, cookie, province, retry_times):
    retry_times = retry_times + 1
    if retry_times > 3:
        return
    # 设置请求头
    headers = {
        "Accept": "*/*",
        "Accept-Language": "zh-CN,zh;q=0.9",
        "Cache-Control": "no-cache",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "Pragma": "no-cache",
        "Proxy-Connection": "keep-alive",
        "Referer": "https://bt.sdnj.org.cn:2021/pub/GongShiSearch",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
        "X-Requested-With": "XMLHttpRequest"
    }

    # 设置请求数据
    data = {
        "__RequestVerificationToken": token,
        "YearNum": year,
        "areaName": "",
        "AreaCode": "",
        "n": "",
        "JiJuLeiXing": "",
        "JiJuLeiXingCode": "",
        "FactoryName": "",
        "BusinessName": "",
        "ChuCBH": "",
        "StartGJRiQi": "",
        "EndGJRiQi": "",
        "StateValue": "",
        "StateName": "",
        "qy": "",
        "PageIndex": page_index,
        "t": ""
    }

    # 发送 POST 请求
    response = requests.post(url + "?pageIndex=" + page_index, headers=headers,
                             data=data,
                             verify=False, cookies=cookie)

    # 输出响应
    print("page_index " + page_index + ":" + str(response.status_code))
    # print(response.text)
    # 解析请求结果
    if response.status_code == 200:
        dir_path = os.path.join(province, year)
        os.makedirs(dir_path, exist_ok=True)  # 自动创建目录

        filename = f"{year}_{page_index}.txt"
        file_path = os.path.join(dir_path, filename)

        with open(file_path, 'a', encoding='utf-8') as file:
            file.write(response.text)
    else:
        print("重试当前页数:" + page_index + "\t重试次数:" + str(retry_times))
        # 重试
        sleep(1)
        sendRequest(url, year, page_index, token, cookie, province, retry_times)
    # sleep(1)


def get_token_value(cookies):
    """
    从字典中获取包含RequestVerificationToken的键值
    返回第一个匹配项的值，没有则返回None
    """
    return next((v for k, v in cookies.items()
                 if 'RequestVerificationToken' in k), None)


def get_province_details_by_requests(url_local, province_name_local, year, start_page, page_total):
    driver.get(url_local)
    sleep(2)

    print("开始爬取" + province_name_local)
    # 1. 点击菜单，使其展开
    search_form_box = driver.find_element(By.ID, "search-form-box")
    dropdown_toggle = search_form_box.find_element(By.CLASS_NAME, "select-dropdown")
    dropdown_toggle.click()
    sleep(1)  # 等待菜单展开

    # 2. 选择年份项（例如选择 2022 年）
    year_option = driver.find_element(By.XPATH, "//li[text()='" + year + "']")
    year_option.click()

    # 点击“查询”按钮
    search_button = driver.find_element(By.XPATH, "//button[contains(text(), '查询')]")
    search_button.click()
    sleep(2)

    # 从 Selenium 获取 cookies
    selenium_cookies = driver.get_cookies()

    # 转换为 requests 的 cookies 格式
    requests_cookies = {cookie['name']: cookie['value'] for cookie in selenium_cookies}
    token = get_token_value(requests_cookies)
    current_page = int(start_page)
    while current_page <= int(page_total):
        sendRequest(driver.current_url, year, str(current_page), token, requests_cookies, province_name_local, 0)
        current_page = current_page + 1


try:
    driver.get("https://td.sxwhkj.com/Account/BuTCapitalGongS")
    sleep(2)
    province_element = driver.find_element(By.CLASS_NAME, "province-box")
    province_element_list = province_element.find_elements(By.XPATH, "//a")
    provinces = list()
    for province in province_element_list:
        province_dict = dict()
        province_dict['url'] = province.get_attribute("href")
        province_dict['name'] = province.get_attribute("text")
        provinces.append(province_dict)
    # 确保文件是以文本模式打开的
    with open("nj.json", "w", encoding="utf-8") as f:
        json.dump(provinces, f, ensure_ascii=False, indent=4)

    # 遍历省份
    for province in provinces:
        if province['name'] == '天津市':
            url = province['url']
            province_name = province['name']
            # get_province_details(url, province_name, '2021')
            # get_province_details(url, province_name, '', '2022', 3452)
            # get_province_details(url, province_name, '2023')
            get_province_details_by_requests(url, province_name, '2025', '1', '50')

finally:
    # 关闭浏览器
    driver.quit()
