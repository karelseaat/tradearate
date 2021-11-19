#!/usr/bin/env python

import re
import json
import time
from bs4 import BeautifulSoup
import requests
import pprint

from google_play_scraper import app


PLAYSTOREURL = "https://play.google.com"


def get_app(appid, country='us'):
    """My own version to get app info from the playstore page, just a scraper"""
    results = {'rating':None, 'title':None, 'icon':None, 'price':None, 'klont':'Turbo Turbo !'}
    requesturl = f"{PLAYSTOREURL}/store/apps/details?id={appid}&hl={country}"
    result = requests.get(requesturl)
    soup = BeautifulSoup(result.text, features="lxml")
    leltext = soup.find("script", {"type" : "application/ld+json"}).text

    temp = json.loads(leltext)
    results['free'] = not int(-(-float(temp['offers'][0]['price']) // 1))
    if 'aggregateRating' in temp:
        results['ratings'] = temp['aggregateRating']['ratingCount']
    else:
        results['ratings'] = 0
    results['title'] = temp['name']
    results['icon'] = temp['image']
    return results


def get_app_alt(appid, country='us'):
    """The propper way to get an app with a official ? api"""
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
