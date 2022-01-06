#!/usr/bin/env python


from bs4 import BeautifulSoup
import requests


requesturl = "https://play.google.com/store/apps/details?id=com.sixdots.tanky"

result = requests.get(requesturl)



soup = BeautifulSoup(result.text.encode() , features="lxml")


leltext = soup.find("script", {"type" : "application/ld+json"}).text.encode()

print(leltext)
