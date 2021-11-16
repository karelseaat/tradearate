#!/usr/bin/env python

import re
import json
from bs4 import BeautifulSoup
import requests

PLAYSTOREURL = "https://play.google.com"

def get_app(appid, country='us'):
    results = {'rating':None, 'title':None, 'icon':None}
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

if __name__ == "__main__":
    thedict = get_app("org.ssandon.altimeterpro", country='nl')
    print(thedict)
