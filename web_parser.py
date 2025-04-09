import logging
import os.path
import random
import time

import dotenv
from bs4 import BeautifulSoup
from selenium.webdriver import ActionChains
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager

dotenv.load_dotenv()


def init_driver(on_vps=True):
    options = webdriver.ChromeOptions()
    if on_vps:
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-software-rasterizer")
        options.add_argument("--headless")

    options.add_argument('--blink-settings=imagesEnabled=false')
    options.add_argument("--window-size=1920,1080")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.set_page_load_timeout(60)
    driver.implicitly_wait(10)

    return driver


def login(driver, _try=0):
    try:
        driver.get(f'https://japonskie.ru/login')
        driver.find_element(By.NAME, 'login').send_keys(os.environ['JAPONSKIE_LOGIN'])
        driver.find_element(By.NAME, 'pass').send_keys(os.environ['JAPONSKIE_PASSWORD'])
        button = driver.find_element(By.TAG_NAME, 'button')
        if button.text == 'Вход':
            button.click()

        time.sleep(1)
        driver.get(f'https://japonskie.ru/')
        time.sleep(1)
        driver.refresh()
    except:
        time.sleep(3 + _try)
        return login(driver, _try+1) if _try < 3 else None


def get_numbers(driver):
    try:
        driver.get('https://japonskie.ru/')

        for tp, val in [('size', 6), ('filtr', 0)]:
            sel = driver.find_element(By.ID, tp)
            sel.click()
            time.sleep(1)
            sel.find_elements(By.TAG_NAME, 'option')[val].click()
            time.sleep(1)

        driver.find_element(By.ID, 'findbutdiv').find_element(By.TAG_NAME, 'img').click()
        time.sleep(1)
        table = driver.find_element(by=By.ID, value='catitems')

        numbers = []
        for a in table.find_elements(By.CLASS_NAME, value='catitem'):
            if a.text.split('#')[-1].strip().isdigit():
                numbers.append(int(a.text.strip().split('#')[-1]))

        return [random.choice(numbers)]
    except Exception as e:
        logging.error('Get numbers error:' + str(e))


def _parse_color(element):
    clr = element.get('style').split('background-color')[1]
    if '#' in clr:
        hex_color = clr.split('#')[1].split(';')[0]
        res = tuple(int(hex_color[i:i + 2], 16) for i in (0, 2, 4))
    else:
        rgb = clr.split('(')[1].split(')')[0].split(',')
        res = tuple(map(int, rgb))
    return res


def get_puzzle(driver, k):
    try:
        try:
            driver.get(f'https://japonskie.ru/{k}')
        except:
            driver = init_driver()
            driver.get(f'https://japonskie.ru/{k}')

        if os.path.exists(f'static/japonskie/puzzle_{k}.html'):
            with open(f'static/japonskie/puzzle_{k}.html', 'r') as f:
                response = f.read()
        else:
            response = driver.page_source
            if os.path.exists(f'static/japonskie/'):
                with open(f'static/japonskie/puzzle_{k}.html', 'w') as f:
                    f.write(response)

        soup = BeautifulSoup(response, 'lxml')
        puzzle = soup.find('table', id='full_cross_tbl')
        button_colors = soup.find('div', id='maincolors').find_all('button', class_='color_button')[:-1]

        bc = 'background-color'
        colors_conv = {_parse_color(e): i + 1 for i, e in enumerate(button_colors)}
        colors = {i: v for v, i in colors_conv.items()}
        colors[0] = (60, 60, 60)

        cols_divs = puzzle.find('table', id='cross_top').find_all('td')
        deep = len(puzzle.find('table', id='cross_top').find_all('tr'))
        n = len(cols_divs) // deep
        cols, cols_colors = [[] for _ in range(n)], [[] for _ in range(n)]
        for i, e in enumerate(cols_divs):
            if e.text.isdigit():
                cols[i % n].append(int(e.text))
                if e.get('style') and bc in e.get('style'):
                    cols_colors[i % n].append(colors_conv[_parse_color(e)])
                else:
                    cols_colors[i % n].append(1)

        rows_divs = puzzle.find('table', id='cross_left').find_all('td')
        m = len(puzzle.find('table', id='cross_left').find_all('tr'))
        deep = len(rows_divs) // m
        rows, rows_colors = [[] for _ in range(m)], [[] for _ in range(m)]
        for i, e in enumerate(rows_divs):
            if e.text.isdigit():
                rows[i // deep].append(int(e.text))
                if e.get('style') and bc in e.get('style'):
                    rows_colors[i // deep].append(colors_conv[_parse_color(e)])
                else:
                    rows_colors[i // deep].append(1)

        deep = (len(max(rows, key=len)), len(max(cols, key=len)))
        return rows, cols, rows_colors, cols_colors, colors, deep
    except Exception as e:
        logging.error('Get puzzle error:' + str(e))


def paste_puzzle(driver, k, a):
    try:
        try:
            driver.get(f'https://japonskie.ru/{k}')
        except:
            driver = init_driver()
            login(driver)
            driver.get(f'https://japonskie.ru/{k}')

        action = ActionChains(driver, duration=1)
        table = driver.find_element(By.ID, 'cross_main')
        button_colors = driver.find_element(By.ID, value='maincolors').find_elements(By.CLASS_NAME, 'color_button')
        for i_b in range(len(button_colors) - 1):
            button_colors[i_b].click()
            for i, row in enumerate(table.find_elements(By.TAG_NAME, 'tr')):
                if not [e for i1 in range(i, len(a)) for e in a[i1] if e == i_b + 1]:
                    break

                if len(a) < 30 or len(a) >= 30 and i > 8:
                    driver.execute_script("window.scrollBy(0, 15)")

                line = row.find_elements(By.TAG_NAME, 'td')
                pressed = False
                for j, cell in enumerate(line):
                    if a[i][j] == i_b + 1 and not pressed:
                        action.click_and_hold(cell)
                        pressed = True

                    if a[i][j] == i_b + 1 and (j + 1 == len(line) or a[i][j + 1] != i_b + 1):
                        action.release(cell)
                        pressed = False

                action.perform()

        time.sleep(5)
        logging.warning('DONE')
    except:
        print(f'Paste error: {k}')
