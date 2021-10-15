#!/usr/bin/env python
import requests
from bs4 import BeautifulSoup
import re
import json

playstoreurl = "https://play.google.com"

def get_app(appid, country='us'):
    results = {'rating':None, 'title':None, 'icon':None}
    requesturl = "{}/store/apps/details?id={}&hl={}".format(playstoreurl, appid, country)
    x = requests.get(requesturl)
    soup = BeautifulSoup(x.text, features="lxml")
    leltext = soup.find("script", {"type" : re.compile('.*')}).text
    temp = json.loads(leltext)
    results['price'] = temp['offers'][0]['price']
    results['rating'] = temp['aggregateRating']['ratingCount']
    results['title'] = temp['name']
    results['icon'] = temp['image']
    return results

if __name__ == "__main__":
    thedict = get_app("com.chucklefish.stardewvalley", country='nl')
    print(thedict)
