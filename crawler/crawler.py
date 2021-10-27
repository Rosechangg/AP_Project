import configparser
import urllib.request
from selenium import webdriver
from urllib.error import URLError, HTTPError, ContentTooShortError
import itertools
import time

CONF = configparser.ConfigParser()
CONF.read('config.ini')

# Create a chrome browser agent
def create_browser():
    options = webdriver.ChromeOptions()
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36")
    browser = webdriver.Chrome(options = options)
    return browser

# Login Instagram
def instagram_login(browser):
    USER_ID = CONF["INSTAGRAM"]["ID"]
    USER_PW = CONF["INSTAGRAM"]["PW"]

    # Move to the login page
    login_url = "https://www.instagram.com/accounts/login/?source=auth_switcher"
    browser.get(login_url)
    time.sleep(3)

    # Get the input elements of id/pw
    id_input = browser.find_element_by_name("username")
    pw_input = browser.find_element_by_name("username")

    # Send login keys
    id_input.send_keys(USER_ID)
    pw_input.send_keys(USER_PW)
    pw_input.send_keys(webdriver.common.keys.Keys.ENTER)

# Search with a hashtag and then crawl data from a result page
def instagram_crawl(browser, tag):
    # Get a search result page
    url = "https://www.instagram.com/explore/tags/{tag}/"
    browser.get(url)

    # Parse the result page
    shared_data = browser.execute_script("return window._sharedData;")
    post = shared_data["entry_data"]["ProfilePage"][0]["graphql"]["user"]["edge_owner_to_timeline_media"]["edges"][0]["node"]
    print(f"Found image: {post['display_url']}")

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

def crawl_pages(url, id_max = 10, error_max = 5):
    for page in itertools.count(id_max):
        pg_url = f"{url}{page}"
        print(pg_url)
        html = download(pg_url)
        if html is None:
            # When the page raised errors
            n_errors += 1
            if n_errors >= error_max:
                break

def main():
    keyword = "%EC%84%B1%EC%8B%AC%EB%8B%B9"

    browser = create_browser()
    instagram_login(browser)
    download(f"https://www.instagram.com/explore/tags/{keyword}/")

if __name__ == "__main__":
    main()
