import json
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.http import HttpResponse
from .models import ObservedOffers, Offers
from .forms import NewUserForm
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required


def health_check(request):
    return JsonResponse({"status": "healthy"}, status=200)

def homepage(request):
    return render(request=request, template_name='main/home.html')


def search(request):
    return render(request, 'main/search.html', {})


def qs_with_filter(request):
    qs = Offers.objects.all()
    if request.GET.get('pietro_od'):
        qs = qs.filter(floor__gte=request.GET.get('pietro_od'))
    if request.GET.get('pietro_do'):
        qs = qs.filter(floor__lte=request.GET.get('pietro_do'))

    return qs


def index(request):
    return render(request, 'main/index.html', {'all_records': qs_with_filter(request)})


def register_request(request):
    if request.method == "POST":
        form = NewUserForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Registration successful.")
            return redirect("main:homepage")
        messages.error(request, "Unsuccessful registration. Invalid information.")
    form = NewUserForm()
    return render(request=request, template_name="main/register.html", context={"register_form": form})


def login_request(request):
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.info(request, f"You are now logged in as {username}.")
                return redirect("main:homepage")
            else:
                messages.error(request, "Invalid username or password.")
        else:
            messages.error(request, "Invalid username or password.")
    form = AuthenticationForm()
    return render(request=request, template_name="main/login.html", context={"login_form": form})


def logout_request(request):
    logout(request)
    messages.info(request, "You have successfully logged out.")
    return redirect("main:homepage")


@login_required(login_url='/login')
def observe_offer(request):
    if request.method == "POST":
        if request.POST.get('btn-1'):
            obs_offer = ObservedOffers()
            obs_offer.user_id = request.user.id
            obs_offer.offer_id = request.POST.get('btn-1')
            obs_offer.save()
            messages.info(request, f"Success.")
            return redirect('/index')


@login_required(login_url='/login')
def observe_offers_list(request):
    all_user_observe_offers = ObservedOffers.objects.filter(user_id=request.user.id).values_list('offer_id', flat=True)

    all_observe = Offers.objects.filter(id__in=all_user_observe_offers)

    return render(request, 'main/observe.html', {'all_records': all_observe})