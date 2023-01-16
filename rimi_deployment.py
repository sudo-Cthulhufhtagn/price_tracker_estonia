from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
import chromedriver_autoinstaller
import pandas as pd
from bs4 import BeautifulSoup
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import json
import time, lxml, cchardet

print('starting')
from pyvirtualdisplay import Display
display = Display(visible=0, size=(800, 800))  
display.start()
print('init display')

chromedriver_autoinstaller.install()

BASE_LINK = "https://www.rimi.ee"

def get_driver():
    chrome_options = Options()
    #  chrome_options.headless = True
    #  chrome_options.add_argument('--headless')
    chrome_options.add_argument('--window-size=800,800')
    #  chrome_options.add_argument('--no-sandbox')
    #  chrome_options.add_argument('--disable-dev-shm-usage')
    #  chrome_options.add_argument("--disable-setuid-sandbox")
    chrome_options.experimental_options['prefs'] = {
    'profile.default_content_setting_values':{
        'images': 2,
        # 'javascript': 2
    }
    }
    driver = webdriver.Chrome(options=chrome_options)
    return driver

def parse_products(driver, product_list: list):
    soup = BeautifulSoup(driver.page_source, 'lxml')     # lxml parser instal
    items = soup.findAll("ul", {"class": "product-grid"})[0].findAll('li')
    for item in items:
        # infos_row = i.findAll('div')[0]  # get the info of a single row
        description = json.loads(item.find('div')['data-gtm-eec-product'])
        try:
            per_kilo = float(item.find('p', {'class': 'card__price-per'}).string.strip().split('\n')[0].replace(',','.'))
        except:
            per_kilo = 0
        # print(description['id'], description['name'], description['price'], per_kilo)
        # id, name, price, price/kg
        product_list.append((description['id'], description['name'], description['price'], per_kilo))

driver = get_driver()
print('got driver')

driver.get(BASE_LINK+"/epood/en")
print('got page')

try:        
    # elem = WebDriverWait(driver, 30).until(    EC.presence_of_element_located((By.CLASS_NAME, "product-grid")))
    elem = WebDriverWait(driver, 30).until(    EC.presence_of_element_located((By.ID, "desktop_category_menu_button")))
finally:        
    print('loaded')

soup = BeautifulSoup(driver.page_source, 'lxml')     # lxml parser install
products_links = []
for menu in soup.find_all('ul', {"id" : lambda L: L and L.startswith('desktop_category_menu_')}):
    products_links.append(menu.find('a')['href'])

shopping_list = []
all_timer_start = time.time()
for products_link in products_links[:2]:
    page_counter = 1
    products_link+='?page=1&pageSize=80'
    driver.get(BASE_LINK+products_link)
    time0 =time.time()

    try:        
        elem = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "product-grid__item")))
    finally:        
        print(f'loaded {products_link}')


    while True:
        print('next page', page_counter)
        page_counter+=1
        parse_products(driver, shopping_list)
        try:
            element = WebDriverWait(driver, 2).until(EC.element_to_be_clickable((By.XPATH, "//a[@rel='next']")))
            driver.find_element(By.XPATH, "//a[@rel='next']").click() # next page
            old_page = driver.current_url
            while driver.current_url == old_page:
                time.sleep(.01)
            element = WebDriverWait(driver, 2).until(EC.presence_of_element_located((By.CLASS_NAME, "product-grid__item")))
        except:
            break
    print(f'Time per page = {time.time()-time0}')

print('all-in-all:', time.time()-all_timer_start)

df = pd.DataFrame(shopping_list, columns=['id', 'name', 'price', 'price/kg'])
df.to_csv('rimi.csv', index=False)
    