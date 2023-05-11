import time
from bs4 import BeautifulSoup
import requests
from datetime import datetime
from main.models import Offers
import json
import logging

logging.basicConfig(level=logging.INFO,
                    filename=fr"log_morizon.txt", filemode="a+",
                    format="%(asctime)-15s %(levelname)-8s %(message)s")


class MorizonScrapper:
    def __init__(self):
        logging.info(f"Robot started working!")
        self.page_checker = 'https://www.morizon.pl/do-wynajecia/mieszkania/?search=1'
        self.page_all = 'https://www.morizon.pl/do-wynajecia/mieszkania/?page={}'
        self.list_to_sql_offers = []
        self.now = datetime.now()
        f = open('config.json')
        self._config = json.load(f)

    def get_pages_count(self):
        page_checker_req = requests.get(self.page_checker)
        soup = BeautifulSoup(page_checker_req.content, 'lxml')
        product_list_elem = soup.find("footer", {"class": "row"})
        pages = product_list_elem.text.strip().split()[-1]

        return int(pages)

    def fetch_site_content(self, index):
        r = requests.get((self.page_all.format(index)))
        return r.content

    def fetch_offer_content(self, offer):
        r = requests.get(offer)
        return r.content

    def get_flat_offers(self):
        pages = self.get_pages_count()
        for i in range(pages + 1):
            print('===== PAGE', i + 1, '=====')
            logging.info(f"Page: {i}")
            conn = BeautifulSoup(self.fetch_site_content(i + 1), 'lxml')
            offer_list = conn.find_all("a", {"class": "property_link property-url"})
            for x in offer_list:

                url = x['href']
                fetch_data_from_correct_offer = BeautifulSoup(self.fetch_offer_content(url), 'lxml')
                img_find = fetch_data_from_correct_offer.find("div", {"class": "row multimediaBoxPhotos"})
                img = img_find.find("div", {"class": "imageBig"})
                img_url = img.find("img", {"id": "imageBig"})['src']
                print(img_url)
                location = fetch_data_from_correct_offer.find("div", {"class": "mz-card__item"})
                x = location.find("div", {"class": "col-xs-9"}).text.strip().replace("Mieszkanie do wynajęcia", "").replace("\n", "").replace("\n", "").replace("\n", "").split(',')
                provincion = fetch_data_from_correct_offer.find("div", {"class": "col-xs-12"}).text.strip().replace("\n","").split(" ")
                try:
                    province = provincion[2]
                    city = provincion[3]
                    street = provincion[-1]
                except Exception as e:
                    logging.info(f"[423498374] - {e}")
                    continue
                title = fetch_data_from_correct_offer.find("div", {"class": "summaryTypeTransaction clearfix"}).text.replace('\n', '')
                toolbasr = fetch_data_from_correct_offer.find("ul", {"class": "list-unstyled list-inline paramIcons"}).text.strip().split('\n')
                rooms_list = toolbasr[-1].split(' ')
                rooms = rooms_list[-1]
                surface = toolbasr[-4].replace(" m²", "").replace("Powierzchnia ", "").replace(",00", "")
                try:
                    price = int(toolbasr[0].replace("\xa0zł","").replace("Cena ",""))
                except Exception as e:
                    logging.info(f"[48374837] - {e}")
                    continue
                tab_th = []
                tab_td = []
                tables = fetch_data_from_correct_offer.find("section", {"class": "params clearfix"})
                tables_th = tables.find_all("th")
                for x in tables_th:
                    tab_th.append(x.text.replace('\n', '').replace(': ', ''))
                tables_td = tables.find_all("td")
                for x in tables_td:
                    tab_td.append(x.text.replace('\n', ''))

                offers_dict = dict(zip(tab_th, tab_td))

                try:
                    if offers_dict['Piętro'] == 'parter':
                        offers_dict['Piętro'] = 1
                    else:
                        offers_dict['Piętro'] = offers_dict['Piętro'].split('/')
                        x = offers_dict['Piętro'][0]
                        offers_dict['Piętro'] = int(x)
                    offers_dict['Typ budynku'] = offers_dict['Typ budynku']
                    offers_dict['Rok budowy'] = offers_dict['Rok budowy']
                    offers_dict['title'] = title
                    offers_dict['price'] = price
                    offers_dict['city'] = city
                    offers_dict['province'] = province
                    offers_dict['rooms'] = int(rooms)

                except Exception as e:
                    logging.info(f"[3242844] - {e}")
                    continue

                try:
                    d = {
                        'create_date': self.now,
                        'Surface': int(surface),
                        'title': title,
                        'Room_count': int(offers_dict['rooms']),
                        'Floor': int(offers_dict['Piętro']),
                        'Price': float(price),
                        'url': url,
                        'img_url': img_url,
                        'Province': offers_dict['province'],
                        'build_year': offers_dict['Rok budowy'],
                        'type_of_building': offers_dict['Typ budynku'],
                        'City': offers_dict['city'],
                        'source': 'morizon.pl'
                    }
                    self.list_to_sql_offers.append(d)
                    print(self.list_to_sql_offers)

                    print("SUCCESS")
                except Exception as e:
                    logging.info(f"[43827487] - {e}")
                    continue
                print('*' * 100)
            self.create_sql()
            self.list_to_sql_offers.clear()

    def create_sql(self):
        to_save = []
        try:
            for d in self.list_to_sql_offers:
                morizon_scrap = Offers(
                                create_date=d.get('create_date'),
                                title=d.get('title'),
                                surface=d.get('Surface'),
                                rooms=d.get('Room_count'),
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

                to_save.append(morizon_scrap)
            Offers.objects.bulk_create(to_save)
            print("SUCCESFUL SAVED TO DATABASE!!")
            logging.info(f"SUCCESFUL SAVED TO DATABASE!!")
        except Exception as e:
            print(e)
            logging.info(f"[32489493] - {e}")
