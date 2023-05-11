from django.core.management.base import BaseCommand
from main.robots.otodom_scrapper import OtodomScrapper


class Command(BaseCommand):

    def handle(self, *args, **kwargs):
        bl = OtodomScrapper()
        bl.get_flat_offers()