from django.core.management.base import BaseCommand
from main.robots.gratka_scrapper import GratkaScrapper


class Command(BaseCommand):

    def handle(self, *args, **kwargs):
        bl = GratkaScrapper()
        bl.get_flat_offers()