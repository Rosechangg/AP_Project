# pip install bs4 selenium lxml

import configparser
import urllib.request
from selenium import webdriver
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from urllib.error import URLError, HTTPError, ContentTooShortError
import itertools
import traceback
import time
import re
import pandas as pd

# CONF = configparser.ConfigParser()
# CONF.read('crawler/config.ini')
ID = "kaistibd@gmail.com"
PW = "ibd5104!@3"
TIME_SLEEP = 3

# Create a chrome browser agent
def create_browser():
    options = webdriver.ChromeOptions()
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36")
    browser = webdriver.Remote("http://172.17.0.2:4444/wd/hub", options = options)
    return browser

# Move to the url using the browser
def move(browser, url):
    browser.get(url)
    print(f"Get into {url}")
    time.sleep(TIME_SLEEP)

# Get a url to search instagram with a tag
def get_url_of_tag_search(tag):
    return f"https://www.instagram.com/explore/tags/{tag}/"

# Get a url to view a post of instagram
def get_url_of_post(pid):
    if "https://" in pid:
        return pid
    else:
        return f"https://www.instagram.com/{pid}"

# Login to Instagram
def instagram_login(browser):
    # USER_ID = CONF["INSTAGRAM"]["ID"]
    # USER_PW = CONF["INSTAGRAM"]["PW"]
    USER_ID = ID
    USER_PW = PW

    # Move to the login page
    login_url = "https://www.instagram.com/accounts/login/?source=auth_switcher"
    move(browser, login_url)

    # Get the input elements of id/pw
    id_input = browser.find_element(By.NAME, "username")
    pw_input = browser.find_element(By.NAME, "password")

    # Send login keys
    id_input.send_keys(USER_ID)
    pw_input.send_keys(USER_PW)
    pw_input.send_keys(webdriver.common.keys.Keys.ENTER)
    print(f"Login - {USER_ID}")
    time.sleep(TIME_SLEEP)

# Search Instagram with a tag and return parsed data in Dataframe
def instagram_tag_crawl(browser, tag, n = 10):
    # Move to the search results
    url = get_url_of_tag_search(tag)
    move(browser, url)

    # Click the first post on the results
    _click_first_post_(browser)

    datarows = []
    for i in range(0, n):
        # Parse the post
        data = _parse_instagram_post_(browser)
        datarows.append(data)
        print(f"Stores {tag} #{i+1}")

        # Move to the next page
        _click_right_post_(browser)

    # Flush results
    pd.DataFrame(datarows).to_csv(f"./results_{tag}.csv")
    print(f"Data of {tag} - Successfully Stored")

# Click the first post on a results page
def _click_first_post_(browser):
    # (!) The broswer must be at a result page of tag-search
    post_css_selector = "div.v1Nh3.kIKUG._bz0w"
    error_count = 0
    while True:
        try:
            post = browser.find_elements(By.CSS_SELECTOR, post_css_selector)[0]
            link = post.find_elements(By.CSS_SELECTOR, 'a')[0] # post link
#            link = post.find_elements(By.CSS_SELECTOR, 'a')[0].get_attribute('href') # post link
#            move(browser, get_url_of_post(link))
            link.click()
            break
        except:
            # Wait for Page Loading
            if error_count >= 5:
                browser.quit()
                quit()
            traceback.print_exc()
            error_count += 1
            time.sleep(5)

# Move to the next page of a post
def _click_right_post_(browser):
    # (!) The browser must be at a post page
    right_arrow_css_selector = "a.coreSpriteRightPaginationArrow"
    right_arrow_css_selector_new = "div.l8mY4"
    sub_right_arrow_xpath = "//svg[@aria-label='Next']/ancestor::button[1]"

    error_count = 0
    try:
        right = browser.find_elements(By.CSS_SELECTOR, right_arrow_css_selector_new)[0]
        btn = right.find_elements(By.CSS_SELECTOR, 'button')[0]
        right.click()
        time.sleep(TIME_SLEEP)
    except:
            # Wait for Page Loading
            if error_count >= 5:
                browser.quit()
                quit()
            traceback.print_exc()
            error_count += 1
            time.sleep(5)

# Parse a posting
def _parse_instagram_post_(browser):
    # Fetch images (with webDriverWait)
    img_urls = _fetch_images_v2_(browser)

    html = browser.page_source
    soup = BeautifulSoup(html, 'lxml')

    # Fetch other information
    content = _fetch_content_(soup)
    tags = re.findall(r'#[^\s#,\\]+', content)
    date = _fetch_date_(soup)
    like = _fetch_like_(soup)
    place = _fetch_location_(soup)
    writer = _fetch_writer_(soup)

    data = {
        'writer':writer,
        'date':date,
        'content':content,
        'like':like,
        'hashtags':tags,
        'location':place,
        'imgs':img_urls,        
    }
    return data

# ================================================================
# ======================== Data Fetchers =========================
# ================================================================

# Get urls of images from a post
def _fetch_images_(browser):
    # (!) The browser must be in a post page
    img_urls = set()
    error_count = 0
    while True:
        img_i = len(img_urls)
        try:
            elements = browser.find_elements(By.CLASS_NAME, '_6CZji')
            elements[img_i].click()
            time.sleep(1)
        except IndexError:
            error_count += 1
            time.sleep(1)
            if error_count == 2:
                break
        img_url = browser.find_elements(By.CLASS_NAME, 'KL4Bh')[img_i].\
            find_element(By.TAG_NAME, 'img').get_attribute('src')
        img_urls.add(img_url)
        error_count = 0 # reset error

    return list(img_urls)

def _fetch_images_v2_(browser):
    css_selector = "._97aPb img"
    img_urls = set()
    while True:
        # Get image elements
        elements = None
        try:
            WebDriverWait(browser, timeout = 30).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, css_selector))
            )
            elements = browser.find_elements(By.CSS_SELECTOR, css_selector)
        except TimeoutException:
            print("...Timeout while finding images")

        # Fetch sources
        if isinstance(elements, list):
            elements = browser.find_elements(By.CSS_SELECTOR, css_selector) # this is a duplicated line but for handling a stale element exception
            for ele_img in elements:
                if ele_img.aria_role == 'img':
                    img_urls.add(ele_img.get_attribute("src"))
        else:
            break

        # Move to next images
        btn_css_selector = "._6CZji .coreSpriteRightChevron"
        try:
            next_photo_btn = browser.find_element(By.CSS_SELECTOR, btn_css_selector)
            next_photo_btn.click()
            time.sleep(0.3)
        except NoSuchElementException:
            break

    return list(img_urls)

def _fetch_content_(soup):
    content_selector = 'div.C4VMK > span'
    try:
        content = soup.select(content_selector)[0].text
    except:
        content = ''
    return content

def _fetch_date_(soup):
    date_selector = 'time._1o9PC'
    try:
        date = soup.select(date_selector)[0]['datetime'][:10]
    except:
        date = ''
    return date

def _fetch_like_(soup):
    like_selector = 'a.zV_Nj'
    try:
        like = soup.select(like_selector)[0].text.split(' ')[0]
    except:
        like = 0
    return like

def _fetch_location_ (soup):
    place_selector = 'div.M30cS'
    try:
        place = soup.select(place_selector)[0].text
    except:
        place = ''
    return place

def _fetch_writer_(soup):
    writer_selector = 'a.sqdOP.yWX7d._8A5w5.ZIAjV'
    try:
        writer = soup.select(writer_selector)[0].text
    except:
        writer = ''
    return writer

# ================================================================
# ================================================================
# ================================================================

# Doanload an html pafe using a URL
def download(url, user_agent = 'wswp', n_retries = 2, charset = 'utf-8'):
    print (f"Downloading {url}")

    # Set user agent to the request header
    request = urllib.request.Request(url)
    request.add_header('User-agent', user_agent)

    try:
        # Get the response
        resp = urllib.request.urlopen(request)
        print (f"Download succeeded")

        # encoding the response text
        cs = resp.headers.get_content_charset()
        if not cs:
            cs = charset
        html = resp.read().decode(cs)

    # Handle download errors
    except (URLError, HTTPError, ContentTooShortError) as e:
        print(f"Download error: {e.reason}")
        html = None
        if n_retries > 0:
            # If the error code is 5xx, retry to download
            if hasattr(e, 'code') and 500 <= e.code < 600:
                return download(url, n_retries-1)
    return html

# def crawl_pages(url, id_max = 10, error_max = 5):
#     for page in itertools.count(id_max):
#         pg_url = f"{url}{page}"
#         print(pg_url)
#         html = download(pg_url)
#         if html is None:
#             # When the page raised errors
#             n_errors += 1
#             if n_errors >= error_max:
#                 break

def main():
    keyword = "성심당"

    browser = create_browser()
    instagram_login(browser)
    instagram_tag_crawl(browser, keyword, n = 100)

    browser.quit()

if __name__ == "__main__":
    main()
