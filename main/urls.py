from django.urls import path
from . import views

app_name = 'main'

urlpatterns = [
    path("<int:id>", views.index, name='index'),
    path("", views.homepage, name="homepage"),
    path("index/", views.index, name='index'),
    path("register/", views.register_request, name="register"),
    # path("homepage/", views.homepage, name="homepage"),
    path("login/", views.login_request, name="login"),
    path("logout", views.logout_request, name= "logout"),
    path("search", views.search, name= "search"),
    path("observe", views.observe_offer, name="observe_offer"),
    path("observe_list", views.observe_offers_list, name="observe_list"),
    path('health', views.health_check, name='health_check'),

]
