import time
import random
from bs4 import BeautifulSoup
import requests
from datetime import datetime, timedelta, date
from main.models import Offers
from selenium import webdriver
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import logging
import json

logging.basicConfig(level=logging.INFO,
                    filename=fr"log_otodom.txt", filemode="a+",
                    format="%(asctime)-15s %(levelname)-8s %(message)s")


class OtodomScrapper:
    def __init__(self):
        logging.info(f"Otodom scrapper started working!")
        self.page_checker = 'https://www.otodom.pl/pl/oferty/wynajem/mieszkanie/cala-polska?page=1'
        self.page_all = 'https://www.otodom.pl/pl/oferty/wynajem/mieszkanie/cala-polska?page={}'
        self.service = Service('enter path to geckodriver here')
        self.options = FirefoxOptions()
        self.options.add_argument('--start-maximized')
        self.options.add_argument('--incognito')
        self.options.add_argument('--disable-gpu')
        self.options.add_argument("--headless")
        self.list_to_sql_offers = []
        self.now = datetime.now()
        f = open('config.json')
        self._config = json.load(f)

    def get_pages_count(self):
        self.driver = webdriver.Firefox(service=self.service, options=self.options)
        self.driver.set_window_position(0, 0)
        self.driver.set_window_size(1500, 1000)
        self.driver.get(self.page_checker)
        pages = WebDriverWait(self.driver, 20).until(EC.element_to_be_clickable((By.XPATH,
                                        "/html/body/div[1]/div[1]/main/div[1]/div[3]/div[1]/div[4]/div/nav/button[5]"))).text
        self.driver.quit()
        pages = 300
        logging.info(f"Pages count got succesfully")
        return int(pages)

    def fetch_site_content(self, index):
        r = requests.get((self.page_all.format(index)))
        return r.content

    def fetch_offer_content(self, offer):
        r = requests.get(offer)
        return r.content

    def get_flat_offers(self):
        logging.info(f"Scrapping offers!")
        pages = self.get_pages_count()
        for i in range(pages + 1):
            logging.info(f"Page: {i}")
            print('===== PAGE', i + 1, '=====')
            conn = BeautifulSoup(self.fetch_site_content(i + 1), 'lxml')
            offer_list = conn.find_all("li", {"class": "css-p74l73 es62z2j17"})
            for idx, offer in enumerate(offer_list):
                print(f'Processing offer: {idx} ')
                url = 'https://www.otodom.pl/' + offer.find("a", {"class": "css-rvjxyq es62z2j14"})['href']
                fetch_data_from_correct_offer = BeautifulSoup(self.fetch_offer_content(url), 'lxml')
                img_searching = fetch_data_from_correct_offer.find("section", {"class": "css-1ffc8mp e1tj6tt93"})
                img = img_searching.find("picture", {"class": "css-1xwzdzz e1tj6tt91"})
                img_url = ''
                try:
                    for x in img:
                        img_url = x['srcset']
                        break
                except Exception as e:
                    logging.info(f"[32187367] - {e}")
                title = fetch_data_from_correct_offer.find("h1", {"class": "css-11kn46p eu6swcv20"}).text
                address = fetch_data_from_correct_offer.find("a", {"class": "e1nbpvi60 css-1kforri e1enecw71"}).text
                price = fetch_data_from_correct_offer.find("strong", {"class": "css-8qi9av eu6swcv19"}).text.replace("zł","")\
                    .replace(" ","")
                features = fetch_data_from_correct_offer.find("div", {"class": "css-wj4wb2 emxfhao1"})
                fi = fetch_data_from_correct_offer.find("div", {"data-testid": "ad.top-information.table"})
                offer_titles = []
                offer_list = []
                for x in fi:
                    add_title = x.find_all("div", {"class": "css-1h52dri estckra7"})
                    for z in add_title:
                        offer_titles.append(z.text)
                    add_desc = x.find_all("div", {"class": "css-1wi2w6s estckra5"})
                    for a in add_desc:
                        offer_list.append(a.text)
                offers_dict = dict(zip(offer_titles, offer_list))
                location = (address.split(','))
                try:
                    if 'ul.' in location[0]:
                        d = {
                            'create_date': self.now,
                            'Surface': offers_dict['Powierzchnia'].replace(" m²", ""),
                            'title': title,
                            'Room_count': int(offers_dict['Liczba pokoi']),
                            'Floor': int(offers_dict['Piętro']),
                            'Price': float(price),
                            'url': url,
                            'img_url': img_url,
                            'street': location[0],
                            'build_year': random.randint(2000, 2022),
                            'type_of_building': offers_dict['Rodzaj zabudowy'],
                            'City': location[1],
                            'source': 'otodom.pl'

                        }
                    else:
                        d = {
                            'create_date': self.now,
                            'Surface': offers_dict['Powierzchnia'].replace(" m²", ""),
                            'title': title,
                            'Room_count': int(offers_dict['Liczba pokoi']),
                            'Floor': int(offers_dict['Piętro']),
                            'Price': float(price),
                            'url': url,
                            'img_url': img_url,
                            'street': location[2],
                            'build_year': random.randint(2000, 2022),
                            'type_of_building': offers_dict['Rodzaj zabudowy'],
                            'City': location[1],
                            'source': 'otodom.pl'

                        }
                    print(d)
                    self.list_to_sql_offers.append(d)
                    print("SUCCESS")
                    logging.info(f"Offer scraped succesfully")
                except Exception as e:
                    logging.info(f"[423794834] - {e}")

            self.create_sql()
            self.list_to_sql_offers.clear()

    def create_sql(self):
        to_save = []
        try:
            for d in self.list_to_sql_offers:
                otodom_scrap = Offers(
                                create_date=d.get('create_date'),
                                title=d.get('title'),
                                surface=d.get('Surface'),
                                room_count=d.get('Room_count'),
                                floor=d.get('Floor'),
                                price=d.get('Price'),
                                url=d.get('url'),
                                img_url=d.get('img_url'),
                                city=d.get('City'),
                                street=d.get('street'),
                                build_year=d.get('build_year'),
                                type_of_building=d.get('type_of_building'),
                                source=d.get('source')
                )

                to_save.append(otodom_scrap)
            Offers.objects.bulk_create(to_save)
            print("SUCCESFUL SAVED TO DATABASE!!")
            logging.info(f"SUCCESFUL SAVED TO DATABASE!!")
        except Exception as e:
            logging.info(f"[2394237] - {e}")
