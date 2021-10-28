import time
import requests
import random
import os
import sys
import bs4
import csv
from selenium.common.exceptions import NoSuchElementException

from selenium import webdriver as wd
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup as bs
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

account = ''
chrome_binary = r"chrome.exe"
url_follower_list =[]
follower_account = []
url = 'https://www.instagram.com/accounts/login/'
#url_gallery = 'https://www.instagram.com/mmcakorea/'

def login(driver):

    FB_ID = 'jangmi0827@gmail.com'
    FB_PW = 'wkdal0664!'

    #아이디, 패스워드 입력
    driver.find_element_by_name('username').send_keys(FB_ID)
    driver.find_element_by_name('password').send_keys(FB_PW)
    time.sleep(2)
    driver.find_element_by_xpath('//form[1]/div[3]/button[1]').submit()
    time.sleep(3)  

def scrape_followers(driver, account):

    #get url
    with open('Collecting_followers_kukjegallery.csv','r') as f:
        reader = csv.reader(f)
        #next(reader)
        for row in reader:
            follower_account.append(row)
    if len(follower_account) > 0:

        for target in follower_account:
            url_follower_list = ('https://www.instagram.com/%s'  % target[0])
        
            driver.get(url_follower_list.format(account))

        # Click the 'Follower(s)' link
            driver.find_element_by_partial_link_text("팔로우").click()
            time.sleep(5)

        # Wait for the followers modal to load
            dialog = driver.find_element_by_xpath('//div[@class="isgrP"]//a')
    
        # 방향키 내리기
            number_click = 8
            while number_click:
                dialog = driver.find_element_by_xpath('//div[@class="isgrP"]//a')
                dialog.send_keys(Keys.ARROW_DOWN)
                time.sleep(0.5)
                number_click-=1
    
            driver.implicitly_wait(7)

        # 페이지 횟수 만큼 내리기
            no_of_pagedowns = 100
            while no_of_pagedowns:
                dialog.send_keys(Keys.END)
                time.sleep(0.8)
                no_of_pagedowns-=1
 
        # Finally, scrape the followers
            xpath = "/html/body/div[2]/div/div[2]/ul/div/li"
            followers_elems = driver.find_elements_by_xpath(xpath)
            followers_temp = [e.text for e in followers_elems]  # List of followers (username, full name, follow text)
            followers = []  # List of followers (usernames only)

        # Go through each entry in the list, append the username to the followers list
            for i in followers_temp:
                username, sep, name = i.partition('\n')
                followers.append(username)

            with open('Collecting_following_%s.csv' % target[0], mode = 'w', encoding='utf-8', newline='') as csvfile: #CSV 저장
                csvwriter = csv.writer(csvfile, delimiter =',')
                for i in range(0, len(followers)):
                    csvwriter.writerow([followers[i]])

            print(followers)
            print("______________________________________")
            print("I found %d following" % len(followers))
            print("______________________________________")
            print('%s All Done' %follower_account[i])

    return

if __name__ == "__main__":
    
    driver = wd.Chrome() #드라이버 구동
    driver.get(url) #url 열기
    time.sleep(1) #1초 기다리기    
    login(driver) #로그인
    scrape_followers(driver, account) #팔로워 찾기
