from django.db import models


class Offers(models.Model):
    id = models.BigAutoField(primary_key=True)
    create_date = models.DateTimeField(blank=True, null=True, auto_now_add=True)
    title = models.CharField(max_length=255, blank=True, null=True)
    surface = models.CharField(max_length=255, blank=True, null=True)
    rooms = models.IntegerField(blank=True, null=True)
    floor = models.IntegerField(blank=True, null=True)
    price = models.FloatField(blank=True, null=True)
    url = models.CharField(max_length=255, blank=True, null=True, unique=True)
    img_url = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=255, blank=True, null=True)
    province = models.CharField(max_length=255, blank=True, null=True)
    build_year = models.CharField(max_length=255, blank=True, null=True)
    type_of_building = models.CharField(max_length=255, blank=True, null=True)
    source = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return self.title


class ObservedOffers(models.Model):
    id = models.BigAutoField(primary_key=True)
    create_date = models.DateTimeField(blank=True, null=True, auto_now_add=True)
    offer_id = models.IntegerField(null=True)
    user_id = models.IntegerField(null=True)

