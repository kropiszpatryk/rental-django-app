from bs4 import BeautifulSoup
import requests
import datetime
import time
from datetime import datetime, timedelta, date
from main.models import Offers
import json
import logging
import random

logging.basicConfig(level=logging.INFO,
                    filename=fr"log_olx.txt", filemode="a+",
                    format="%(asctime)-15s %(levelname)-8s %(message)s")


class OlxScrapper:
    def __init__(self):
        logging.info(f"Robot started working!")
        self.page_checker = 'https://www.olx.pl/nieruchomosci/mieszkania/wynajem/?page=2'
        self.pages_all = 'https://www.olx.pl/nieruchomosci/mieszkania/wynajem/?page={}'
        self.list_to_sql_offers = []
        self.now = datetime.now()
        f = open('config.json')
        self._config = json.load(f)

    def get_pages_count(self):
        page_checker_req = requests.get(self.page_checker)
        soup = BeautifulSoup(page_checker_req.content, 'lxml')
        product_list_elem = soup.find("div", {"class": "pager rel clr"})
        pages = product_list_elem.text.strip().replace("\n", "").replace("następna »", "").replace("Idź do strony:« poprzednia1 2345678910111213...","")

        return int(pages)

    def fetch_site_content(self, index):
        r = requests.get((self.pages_all.format(index)))
        return r.content

    def fetch_offer_content(self, offer):
        r = requests.get(offer)
        return r.content

    def get_flat_offers(self):
        pages = self.get_pages_count()
        print(pages)
        for i in range(pages + 1):
            i += 2
            print('===== PAGE', i, '=====')
            logging.info(f"Page: {i}")
            conn = BeautifulSoup(self.fetch_site_content(i), 'lxml')
            offer_list = conn.find_all("div", {"class": "offer-wrapper"})

            for offer in offer_list:
                title = offer.find('strong').get_text()
                price = offer.find("p", {"class": "css-5kmdsl es62z2j19"}).text
                foo = offer.find("td", {"class": "bottom-cell"})
                location = foo.find("small", {"class": "breadcrumb x-normal"}).get_text().strip()
                price = offer.find("p", {"class": "price"}).get_text().strip().replace(" zł", "").replace(" ","")
                url = offer.find('h3', {"class": "lheight22 margintop5"})
                for a in url.find_all('a', href=True):
                    href = a['href']
                    fetch_data_from_correct_offer = BeautifulSoup(self.fetch_offer_content(href), 'lxml')
                    try:
                        img = fetch_data_from_correct_offer.find("div", {"class": "swiper-zoom-container"})
                        img_url = img.find("img", {"class": "css-1bmvjcs"})['src']
                        print(img_url)
                        loc = fetch_data_from_correct_offer.find("div", {"class": "css-1f5mute"})
                        location = loc.find_all('li')
                        location_list = []
                        for x in location:
                            location_list.append(x.text)
                        province = location_list[4].split('-')[1].replace(' ','')
                        city = location_list[5].split('-')[1].replace(' ','')
                        if str(province) == "Warmińsko":
                            province = 'Warmińsko - mazurskie'

                    except Exception as e:
                        logging.info(f"[08127483] - {e}")
                        continue
                    spec = fetch_data_from_correct_offer.find("ul", {"class": "css-sfcl1s"})
                    try:
                        f = spec.find_all("li", {"class": "css-ox1ptj"})
                        offer_list = []
                        offer_titles = []
                        for x in f:
                            try:
                                a = x.text.split(':')

                                offer_titles.append(a[0])
                                offer_list.append(a[1])
                            except IndexError as e:
                                logging.info(f"[0812473] - {e}")
                                continue
                        if offer_titles[0] == 'Prywatne' or offer_titles[0] == 'Firmowe':
                            offer_titles.pop(0)

                        offers_dict = dict(zip(offer_titles, offer_list))

                        try:
                            offers_dict['City'] = city
                            offers_dict['Province'] = province
                            offers_dict['Poziom'] = offers_dict['Poziom'].replace(' ', '')
                            offers_dict['Liczba pokoi'] = offers_dict['Liczba pokoi'].replace(' pokoje', '')
                            offers_dict['Rodzaj zabudowy'] = offers_dict['Rodzaj zabudowy'].replace(' ', '')
                            offers_dict['Powierzchnia'] = offers_dict['Powierzchnia'].replace(' m²', '').replace(' ', '')
                        except Exception as e:
                            logging.info(f"[2837462] - {e}")
                            continue
                        try:
                            d = {
                                'create_date': self.now,
                                'Surface': offers_dict['Powierzchnia'],
                                'title': title,
                                'Room_count': int(offers_dict['Liczba pokoi']),
                                'Floor': int(offers_dict['Poziom']),
                                'Price': float(price),
                                'url': href,
                                'img_url': img_url,
                                'Province': offers_dict['Province'],
                                'build_year': random.randint(2000, 2022),
                                'type_of_building': offers_dict['Rodzaj zabudowy'],
                                'City': offers_dict['City'],
                                'source': 'olx.pl'
                            }
                            self.list_to_sql_offers.append(d)
                            print("SUCCESS")
                            print(self.list_to_sql_offers)
                            logging.info(f"success")
                        except Exception as e:
                            logging.info(f"[9023742] - {e}")
                            continue
                    except Exception as e:
                        logging.info(f"[23984239] - {e}")
                        continue
                self.create_sql_costs()
                self.list_to_sql_offers.clear()

    def create_sql_costs(self):
        to_save = []
        try:
            for d in self.list_to_sql_offers:
                olx_scrapp = Offers(
                                create_date=d.get('create_date'),
                                title=d.get('title'),
                                surface=d.get('Surface'),
                                room_count=d.get('Room_count'),
                                floor=d.get('Floor'),
                                price=d.get('Price'),
                                url=d.get('url'),
                                img_url=d.get('img_url'),
                                city=d.get('City'),
                                province=d.get('Province'),
                                build_year=d.get('build_year'),
                                type_of_building=d.get('type_of_building'),
                                source=d.get('source')
                )

                to_save.append(olx_scrapp)
            Offers.objects.bulk_create(to_save)
            print("SUCCESFUL SAVED TO DATABASE!!")
            logging.info(f"SUCCESFUL SAVED TO DATABASE!!")
        except Exception as e:
            logging.info(f"[89242874] - {e}")


