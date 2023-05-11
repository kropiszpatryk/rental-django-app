from django.core.management.base import BaseCommand
from main.robots.olx_scrapper import OlxScrapper


class Command(BaseCommand):

    def handle(self, *args, **kwargs):
        bl = OlxScrapper()
        bl.get_flat_offers()