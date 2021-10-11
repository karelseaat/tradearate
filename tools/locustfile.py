import time
from locust import HttpUser, task, between
import json
import random
import urllib.parse
from bs4 import BeautifulSoup

class QuickstartUser(HttpUser):
    wait_time = between(1, 2.5)
    appids = []
    reviewids = []
    tradeids = []

    storeids = ['com.sixdots.dicepro', 'com.sixdots.ghostly', 'com.sixdots.dice_game', 'com.sixdots.tanky', 'com.sixdots.alpy', 'com.egeaappdesign.altimeterpro', 'com.sixdots.picsurelylite', 'travel.minskguide.geotag', 'com.tappytaps.android.geotagphotospro2', 'com.BlindEyeGames.Yatzy3D', 'de.koljatm.android.diceroller.genesys']

    def on_start(self):
        with self.client.post('/customlogin', data={"beest":"Lollozotoeoobnenfmnbsf"}, catch_response=True, verify=False) as response:
            if 'success' not in response.text:
                response.failure('login failed')
                quit()

    @task
    def test_index(self):
        with self.client.get("/") as response:
            soup = BeautifulSoup(response.text, features="lxml")
            leltext = soup.find("div", {"class" : "frame__body"}).text
            print(leltext)

    @task
    def test_overviewapps(self):
        with self.client.get("/overviewapps" ) as response:
            soup = BeautifulSoup(response.text, features="lxml")
            leltext = soup.find_all("td")
            print(leltext)

    @task
    def test_overviewtrades(self):
        with self.client.get("/overviewtrades") as response:
            soup = BeautifulSoup(response.text, features="lxml")
            leltext = soup.find_all("td")
            print(leltext)

    @task
    def test_overviewreviews(self):
        with self.client.get("/overviewreviews") as response:
            soup = BeautifulSoup(response.text, features="lxml")
            leltext = soup.find_all("td")
            print(leltext)

    @task
    def test_trades(self):
        with self.client.get("/trades") as response:
            soup = BeautifulSoup(response.text, features="lxml")
            leltext = soup.find_all("td")
            print(leltext)

    @task
    def test_userprofile(self):
        with self.client.get("/userprofile") as response:
            print("yesw !")

    @task
    def test_add_trade(self):
        with self.client.get("/add?redirectto=/overview") as response:
            print("yesw !")

    @task
    def test_add_trade(self):
        with self.client.get("/join?redirectto=/overview") as response:
            print("yesw !")

    @task
    def test_add_trade(self):
        with self.client.post("/processadd?redirectto=/overview", data={"appid":""}) as response:
            print("yesw !")

    @task
    def test_add_trade(self):
        with self.client.post("/processjoin?redirectto=/overview", data={"appid":"", "tradeid":""}) as response:
            print("yesw !")
