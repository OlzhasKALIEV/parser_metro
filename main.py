import csv
import os
import re
import time

import requests
from bs4 import BeautifulSoup
from lxml import etree
from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By

chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument('--headless')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')
chrome_options.add_argument("--window-size=1920,1080")  # Установите нужное разрешение экрана
chrome_path = '/usr/bin/chromedriver'
os.environ['PATH'] = f"{os.environ['PATH']}:{chrome_path}"

url = "https://online.metro-cc.ru/"

browser = webdriver.Chrome(options=chrome_options)
browser.get(url)
time.sleep(5)
city = browser.find_element(By.XPATH,
                            '//*[@id="__layout"]/div/div/div[1]/header/div[2]/div[1]/div[1]/div[2]/div/div[2]/button[2]/span')
city.click()
time.sleep(3)
city = browser.find_element(By.XPATH, "//span[contains(text(), 'Москва')]")
city.click()
product = browser.find_element(By.XPATH, '//*[@id="__layout"]/div/div/div[1]/header/div[2]/div[2]/ul/li[11]/a')
product.click()
time.sleep(3)
html = browser.page_source

while True:
    button = browser.find_element(By.XPATH, '//*[@id="catalog-wrapper"]/main/div[2]/button/span')
    actions = ActionChains(browser)
    actions.move_to_element(button).perform()
    time.sleep(1)
    actions.click(button).perform()
    time.sleep(3)
    browser.execute_script("window.scrollBy(0, 500);")
    time.sleep(3)
    try:
        button = browser.find_element(By.XPATH, '//*[@id="catalog-wrapper"]/main/div[2]/button/span')
    except:
        browser.execute_script("window.scrollBy(0, 1000);")
        time.sleep(3)
        break

records = []

soup = BeautifulSoup(browser.page_source, 'lxml')
product_links = soup.find_all('div',
                              class_='catalog-2-level-product-card product-card subcategory-or-type__products-item with-rating with-prices-drop')

for product_link in product_links:
    url_product = product_link.find('a', class_='product-card-name')
    url_product = 'https://online.metro-cc.ru' + url_product['href']
    response = requests.get(url_product)
    tree = etree.HTML(response.text)
    script_content = tree.xpath('/html/body/script[1]/text()')[0]
    pattern_id = r'CatalogProductPage:0":{pageData:{id:(\d+)'
    match_id = re.search(pattern_id, script_content)
    product_name = product_link.find('span', class_='product-card-name__text').text.strip()
    price_product = product_link.find('span', class_='product-price__sum-rubles').text.strip()
    soup = BeautifulSoup(requests.get(url_product).text, "html.parser")
    brand = soup.find_all('a', class_='product-attributes__list-item-link reset-link active-blue-text')
    records.append({
        'id': match_id.group(1),
        'name': product_name,
        'url': url_product,
        'brand': brand[0].text.strip(),
        'price': price_product
    })
    if len(records) == 100:  # --- Корректировка кол-во записей
        break
csv_file = 'output.csv'

with open(csv_file, 'w', newline='', encoding='cp1251') as file:
    writer = csv.DictWriter(file, fieldnames=['id', 'name', 'url', 'brand', 'price'])
    writer.writeheader()
    writer.writerows(records)

print(f"Запись данных прошла успешно. Название файла: {csv_file}")

browser.quit()
