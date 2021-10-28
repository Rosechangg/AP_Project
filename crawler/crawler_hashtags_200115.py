import re
import csv
import time

from tqdm import tqdm
from random import uniform
from bs4 import BeautifulSoup
from selenium import webdriver as wd
from selenium.common.exceptions import *


def instagram_login(driver, username, password):
    """
    Login to instagram
    """
    driver.get('https://www.instagram.com/accounts/login/')
    driver.implicitly_wait(3)

    driver.find_element_by_xpath('//*[@name="username"]').send_keys(username)
    driver.find_element_by_xpath('//*[@name="password"]').send_keys(password)
    time.sleep(1)

    driver.find_element_by_xpath('//*[@type="submit"]').submit()
    time.sleep(5)

    try:
        driver.find_element_by_css_selector('button.aOOlW.HoLwm').click()
        driver.implicitly_wait(uniform(3, 7))

    except:
        pass


def load_nodelist(filename):
    nodes = []

    for node in csv.reader(open(filename, 'r', encoding='utf-8')):
        nodes.append(node[0])

    return nodes


def account_availability(driver, account):
    """
    Confirm the account exists and is public.
    The unavailable accounts would be logged to another file.
    """
    try:
        is_private = driver.find_element_by_css_selector('h2.rkEop')
        if is_private.is_displayed():
            print('{} is private account.'.format(account))
            csv.writer(open('users_to_exclude.csv', 'a', encoding='utf-8', newline=''), delimiter=',').writerow(
                [account])
            return False

    except NoSuchElementException:

        try:
            not_exist = driver.find_element_by_xpath('/html/body/div/div[1]/div/div/h2')
            if not_exist.is_displayed():
                print('{} does not exist.'.format(account))
                csv.writer(open('users_to_exclude.csv', 'a', encoding='utf-8', newline=''), delimiter=',').writerow(
                    [account])
                return False

        except NoSuchElementException:
            return True


def load_links(driver, account, no_of_posts):
    outputs = set()

    try:
        SCROLL_PAUSE_TIME = uniform(1, 3)

        last_height = driver.execute_script("return document.body.scrollHeight")

        while True:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

            time.sleep(SCROLL_PAUSE_TIME)
            links = driver.find_elements_by_css_selector('div.v1Nh3.kIKUG._bz0w')
            for link in links:
                outputs.add(link.find_element_by_css_selector('a').get_attribute('href'))

            new_height = driver.execute_script("return document.body.scrollHeight")

            if new_height == last_height:
                break

            last_height = new_height

    except NoSuchElementException:
        print('{} posted nothing.'.format(account))

    return outputs


def retrieve_hashtags(driver, account, url):
    """
    Return a list of hashtags from the inputted page.
    """
    hashtags = []

    try:
        caption = driver.find_element_by_class_name('C4VMK')

        try:
            for tag in caption.find_elements_by_css_selector('a'):
                if tag.text.startswith('#'):
                    hashtags.append(tag.text)

        except NoSuchElementException:
            pass

    except NoSuchElementException:
        pass

    return hashtags


if __name__ == '__main__':

    # update the path to locate the chrome driver
    driver_path = 'C:/Users/admin/Desktop/장미/파이썬/NRF_Gallery/chromedriver.exe'
    driver = wd.Chrome(executable_path=driver_path)

    instagram_login(driver, 'rose_husband0220', 'cjswo4857!')

    accounts = load_nodelist('hashtags_ac.csv')

    for account in tqdm(accounts):

        link = "https://www.instagram.com/{}".format(account)
        driver.get(link)
        driver.implicitly_wait(uniform(2, 4))

        if account_availability(driver, account):
            try:
                error_msg = driver.find_element_by_class_name(
                    'error-container.-cx-PRIVATE-ErrorPage__errorContainer.-cx-PRIVATE-ErrorPage__errorContainer__')
                if error_msg.is_displayed():
                    print("Failed to start scraping the account {}.".format(account))
                    csv.writer(open('error_users_links.csv', 'a', encoding='utf-8', newline=''),
                               delimiter=',').writerow([account])

            except NoSuchElementException:

                no_of_posts = int(driver.find_elements_by_css_selector('span.g47SY')[0].text.replace(',', ''))

                print("Collecting all post links from user: {} ...".format(account))
                urls = load_links(driver, account, no_of_posts)

                while len(urls) != no_of_posts:
                    if abs(len(urls) - no_of_posts) > len(urls) * 0.05:
                        print("Failed to collect all post links, re-attempting user {}.".format(account))
                        driver.refresh()
                        urls = load_links(driver, account, no_of_posts)
                    else:
                        break

                print("Collecting all hashtags from posts by user: {} ...".format(account))

                for url in urls:

                    driver.get(url)
                    driver.implicitly_wait(uniform(3, 5))

                    try:
                        error_msg = driver.find_element_by_class_name('error-container.-cx-PRIVATE-ErrorPage__errorContainer.-cx-PRIVATE-ErrorPage__errorContainer__')
                        if error_msg.is_displayed():
                            print("Failed to start scraping the post {} by user {}.".format(url, account))
                            csv.writer(open('error_posts_links.csv', 'a', encoding='utf-8', newline=''),
                                       delimiter=',').writerow([url])

                    except NoSuchElementException:
                        with open('hashtags_of_{}.csv'.format(account), 'a', encoding='utf-8', newline='') as tags_file:
                            writer = csv.writer(tags_file, delimiter=",")

                            hashtags = retrieve_hashtags(driver, account, url)

                            if len(hashtags) >= 1:
                                for tag in hashtags:
                                    writer.writerow([tag])