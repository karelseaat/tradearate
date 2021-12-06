#!/usr/bin/env python

import sys
sys.path.append('..')

from selenium import webdriver
from selenium.webdriver.firefox.options import Options
import time
import sqlalchemy
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import *

options = Options()
options.add_argument("--headless")

driver = webdriver.Firefox(executable_path= r"/home/aat/Desktop/geckodriver", options=options)

driver.get('https://play.google.com/store/search?q=altitude meter&c=apps')


SCROLL_PAUSE_TIME = 5

# Get scroll height
last_height = driver.execute_script("return document.body.scrollHeight")

while True:
    # Scroll down to bottom
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

    # Wait to load page
    time.sleep(SCROLL_PAUSE_TIME)

    # Calculate new scroll height and compare with last scroll height
    new_height = driver.execute_script("return document.body.scrollHeight")
    if new_height == last_height:
        break
    last_height = new_height


books = driver.find_element_by_class_name("Ktdaqe").find_elements_by_tag_name('c-wiz')

# books = driver.find_elements_by_tag_name('c-wiz')

for book in books:

    ass = book.find_elements_by_tag_name('a')
    if len(ass) >= 4:

        print(ass[2].find_elements_by_tag_name('div')[0].get_attribute('innerHTML'))
        print(ass[0].get_attribute('href'))
