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
import time, lxml, cchardet, os

print('starting')
if os.getenv('CI'):
    from pyvirtualdisplay import Display
    display = Display(visible=0, size=(800, 800))  
    display.start()
print('init display')

chromedriver_autoinstaller.install()

BASE_LINK = "https://www.selver.ee"
PRODUCTS_PER_PAGE = 1500

def get_driver():
    chrome_options = Options()
    #  chrome_options.headless = True
    #  chrome_options.add_argument('--headless')
    chrome_options.add_argument('--window-size=800,800')
    #  chrome_options.add_argument('--no-sandbox')
    #  chrome_options.add_argument('--disable-dev-shm-usage')
    #  chrome_options.add_argument("--disable-setuid-sandbox")
    chrome_options.add_argument("--ignore-certificate-errors")
    chrome_options.experimental_options['prefs'] = {
    'profile.default_content_setting_values':{
        'images': 2,
        # 'javascript': 2
    }
    }
    driver = webdriver.Chrome(options=chrome_options)
    return driver

def parse_products(soup, product_list: list):
    items = soup.findAll("div", {"class": "ProductCard__info"})
    print('items len:', len(items))
    for item in items:
        name = item.find('h3', {'class': 'ProductCard__title'}).text.strip()
        price = [0,0]
        try:
            price = [
                float(i.split()[0].strip().replace(',', '.'))
                for i in
                item.find('div', {'class': 'ProductPrice'}).strings
                ]
        except:
            print('missing price')
        # id, name, price, price/kg
        product_list.append((name, price[0], price[1]))

driver = get_driver()
print('got driver')


products_links = [f'/tooted?limit={PRODUCTS_PER_PAGE}']

shopping_list = []
all_timer_start = time.time()
for products_link in products_links:
    page_counter = 1
    driver.get(BASE_LINK+products_link)
    time0 =time.time()

    try:        
        elem = WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.CLASS_NAME, "ProductListing")))
    finally:        
        print(f'loaded {products_link}')

    while PRODUCTS_PER_PAGE!=len(driver.find_elements(By.CLASS_NAME, 'ProductCard__info')):
        time.sleep(0.01)


    while True:
        print('next page', page_counter)
        page_counter+=1
        soup = BeautifulSoup(driver.page_source, 'lxml')     # lxml parser instal
        print('parsing')
        parse_products(soup, shopping_list)
        try:
            next_link = soup.find('div', {'class': 'sf-pagination__item sf-pagination__item--next'}).find('a')['href']
            
            old_page = driver.current_url
            driver.get(BASE_LINK+next_link)
            while driver.current_url == old_page:
                time.sleep(.01)
            print(next_link)
            # driver.execute_script("window.scrollTo(0, 1800)") 

            while PRODUCTS_PER_PAGE!=len(driver.find_elements(By.CLASS_NAME, 'ProductCard__info')):
                time.sleep(0.01)

            element = WebDriverWait(driver, 4).until(EC.presence_of_element_located((By.CLASS_NAME, "ProductCard__title")))
            time.sleep(1)
        except:
            break
    print(f'Time per page = {time.time()-time0}')

print('all-in-all:', time.time()-all_timer_start)

df = pd.DataFrame(shopping_list, columns=['name', 'price', 'price/kg'])
df.to_csv('selver.csv', index=False)
    