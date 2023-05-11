from bs4 import BeautifulSoup
import requests
import datetime
import time
from datetime import datetime
from main.models import Offers
import json
import logging

logging.basicConfig(level=logging.INFO,
                    filename=fr"log_gratka.txt", filemode="a+",
                    format="%(asctime)-15s %(levelname)-8s %(message)s")


class GratkaScrapper:
    def __init__(self):
        logging.info(f"Robot started working!")
        self.page_checker = 'https://gratka.pl/nieruchomosci/mieszkania?page=1'
        self.page_all = 'https://gratka.pl/nieruchomosci/mieszkania/wynajem?page={}'
        self.list_to_sql_offers = []
        self.now = datetime.now()
        f = open('config.json')
        self._config = json.load(f)

    def get_pages_count(self):
        page_checker_req = requests.get(self.page_checker)
        soup = BeautifulSoup(page_checker_req.content, 'lxml')
        product_list_elem = soup.find("div", {"class": "pagination"})
        pages = product_list_elem.text.strip().replace("\n", "")[-3:]

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
            print('===== PAGE', i +1, '=====')
            logging.info(f"Page: {i}")
            conn = BeautifulSoup(self.fetch_site_content(i +1), 'lxml')
            off = conn.find_all("div", {"class": "listing"})
            for x in off:
                offer_list = x.find_all("article", {"class": "teaserUnified"})
                for z in offer_list:
                    href = z['data-href']
                    price = z.find("p", {"class": "teaserUnified__price"}).get_text().strip().replace("              ", "").replace("zł", "").replace("/mc", "").replace(" ","").split("\n")
                    title = z.find("a", {"class": "teaserUnified__anchor"}).get_text()

                    fetch_data_from_correct_offer = BeautifulSoup(self.fetch_offer_content(href), 'lxml')
                    try:
                        img = fetch_data_from_correct_offer.find("div", {"class": "gallery"})
                        img_url_search = img.find("div", {"class": "gallery__container gallery__container--4"})
                        search_img_deep = img_url_search.find("div", {"class": "gallery__imageContainer"})
                        img_url = search_img_deep.find("img", {"class": "gallery__image"})['src']
                    except:
                        continue
                    print(img_url)

                    offer_spec = fetch_data_from_correct_offer.find_all("div", {"class": "parameters__container"})

                    for a in offer_spec:
                        li = a.find_all('span')
                        of = a.find_all("b", {"class": "parameters__value"})
                        offer_list = []
                        offer_titles = []
                        for d in of:
                            a = d.text.split()
                            offer_list.append(a)
                        for x in li:
                            f = x.text
                            offer_titles.append(f)

                        offers_dict = dict(zip(offer_titles, offer_list))

                        try:
                            offers_dict['Miasto'] = offers_dict['Lokalizacja'][0]
                            offers_dict['Województwo'] = offers_dict['Lokalizacja'][-1]
                            offers_dict['Powierzchnia w m2'] = offers_dict['Powierzchnia w m2'][0]
                            offers_dict['Liczba pokoi'] = offers_dict['Liczba pokoi'][0]
                            offers_dict['Piętro'] = offers_dict['Piętro'][0]
                            offers_dict['Rok budowy'] = offers_dict['Rok budowy'][0]
                            offers_dict['Typ zabudowy'] = offers_dict['Typ zabudowy'][0]
                        except Exception as e:
                            logging.info(f"[23847324] - {e}")
                            continue
                        try:
                            d = {
                                'create_date': self.now,
                                'Surface': offers_dict['Powierzchnia w m2'],
                                'title': title,
                                'Room_count': int(offers_dict['Liczba pokoi']),
                                'Floor': int(offers_dict['Piętro']),
                                'Price': float(price[0]),
                                'url': href,
                                'img_url' : img_url,
                                'Province': offers_dict['Lokalizacja'][-1],
                                'build_year': offers_dict['Rok budowy'],
                                'type_of_building': offers_dict['Typ zabudowy'],
                                'City': offers_dict['Lokalizacja'][0].replace(",", ""),
                                'source': 'gratka.pl'
                            }
                            self.list_to_sql_offers.append(d)
                            print("SUCCESS")
                            print(offers_dict)
                            logging.info(f"Page: {i} scrapped successfully")
                        except Exception as e:
                            logging.info(f"[09238473] - {e}")
                            continue

            self.create_sql_costs()
            self.list_to_sql_offers.clear()

    def create_sql_costs(self):
        to_save = []
        try:
            for d in self.list_to_sql_offers:
                gratka_scrap = Offers(
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

                try:
                    gratka_scrap.save()
                    print("SUCCESFUL SAVED TO DATABASE!!")
                    logging.info(f"SUCCESFUL SAVED TO DATABASE!!")
                except Exception as e:
                    print(e)
                    continue

        except Exception as e:
            logging.info(f"[230473847] - {e}")

