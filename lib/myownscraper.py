#!/usr/bin/env python

import re
import json
from bs4 import BeautifulSoup
import requests
from google_play_scraper import app
import time

PLAYSTOREURL = "https://play.google.com"


def get_app(appid, country='us'):
    results = {'rating':None, 'title':None, 'icon':None, 'price':None, 'klont':'Turbo Turbo !'}
    requesturl = "{}/store/apps/details?id={}&hl={}".format(PLAYSTOREURL, appid, country)
    result = requests.get(requesturl)
    soup = BeautifulSoup(result.text, features="lxml")
    leltext = soup.find("script", {"type" : re.compile('.*')}).text
    temp = json.loads(leltext)
    results['price'] = int(-(-float(temp['offers'][0]['price']) // 1))
    results['rating'] = temp['aggregateRating']['ratingCount']
    results['title'] = temp['name']
    results['icon'] = temp['image']
    return results


def get_app_alt(appid, country='us'):
    temp = app(appid, country)
    iets = {k:v for (k,v) in temp.items() if k in ['title', 'free', 'ratings', 'icon']}
    return {**iets, **{"klont": 'Turbo Turbo'}}

if __name__ == "__main__":
    print(time.time())
    moredict = get_app_alt("org.ssandon.altimeterpro", country='nl')
    print(moredict)
    print(time.time())
    moredict = get_app_alt("org.ssandon.altimeterpro", country='nl')
    print(moredict)
    print(time.time())
