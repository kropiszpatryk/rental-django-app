from django.core.management.base import BaseCommand
from main.robots.morizon_scrapper import MorizonScrapper


class Command(BaseCommand):

    def handle(self, *args, **kwargs):
        bl = MorizonScrapper()
        bl.get_flat_offers()