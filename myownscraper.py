#!/usr/bin/env python
import requests
from bs4 import BeautifulSoup
import re
import json

playstoreurl = "https://play.google.com"

def get_app(appid, country='us'):
    results = {'rating':None, 'title':None, 'icon':None}
    x = requests.get("{}/store/apps/details?id={}&hl={}".format(playstoreurl, appid, country))
    soup = BeautifulSoup(x.text, features="lxml")
    leltext = soup.find("script", {"type" : re.compile('.*')}).text
    temp = json.loads(leltext)
    results['rating'] = temp['aggregateRating']['ratingCount']
    results['title'] = temp['name']
    results['icon'] = temp['image']
    return results

if __name__ == "__main__":
    thedict = get_app("com.sixdots.alpy", country='nl')
    print(thedict)
