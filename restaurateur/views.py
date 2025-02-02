from collections import defaultdict

import requests
from geopy import distance

from django import forms
from django.conf import settings
from django.contrib.auth import authenticate, login
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views import View

from coordinates.models import Place
from foodcartapp.models import Product, Restaurant, Order, RestaurantMenuItem


class Login(forms.Form):
    username = forms.CharField(
        label='Логин', max_length=75, required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Укажите имя пользователя'
        })
    )
    password = forms.CharField(
        label='Пароль', max_length=75, required=True,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите пароль'
        })
    )


class LoginView(View):
    def get(self, request, *args, **kwargs):
        form = Login()
        return render(request, "login.html", context={
            'form': form
        })

    def post(self, request):
        form = Login(request.POST)

        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']

            user = authenticate(request, username=username, password=password)
            if user:
                login(request, user)
                if user.is_staff:  # FIXME replace with specific permission
                    return redirect("restaurateur:RestaurantView")
                return redirect("start_page")

        return render(request, "login.html", context={
            'form': form,
            'ivalid': True,
        })


class LogoutView(auth_views.LogoutView):
    next_page = reverse_lazy('restaurateur:login')


def is_manager(user):
    return user.is_staff  # FIXME replace with specific permission


@user_passes_test(is_manager, login_url='restaurateur:login')
def view_products(request):
    restaurants = list(Restaurant.objects.order_by('name'))
    products = list(Product.objects.prefetch_related('menu_items'))

    default_availability = {restaurant.id: False for restaurant in restaurants}
    products_with_restaurants = []
    for product in products:

        availability = {
            **default_availability,
            **{item.restaurant_id: item.availability for item in product.menu_items.all()},
        }
        orderer_availability = [availability[restaurant.id] for restaurant in restaurants]

        products_with_restaurants.append(
            (product, orderer_availability)
        )

    return render(request, template_name="products_list.html", context={
        'products_with_restaurants': products_with_restaurants,
        'restaurants': restaurants,
    })


@user_passes_test(is_manager, login_url='restaurateur:login')
def view_restaurants(request):
    return render(request, template_name="restaurants_list.html", context={
        'restaurants': Restaurant.objects.all(),
    })


def fetch_coordinates(address):
    geocoder_api_key = settings.YANDEX_GEOCODER_KEY
    base_url = "https://geocode-maps.yandex.ru/1.x"
    response = requests.get(base_url, params={
        "geocode": address,
        "apikey": geocoder_api_key,
        "format": "json",
    })
    response.raise_for_status()
    found_places = response.json()['response']['GeoObjectCollection']['featureMember']

    if not found_places:
        return None

    most_relevant = found_places[0]
    lon, lat = most_relevant['GeoObject']['Point']['pos'].split(" ")
    return lon, lat


def get_coordinates(address):
    place, created = Place.objects.get_or_create(
        address=address
    )
    if created:
        coordinates = fetch_coordinates(address)
        if not coordinates:
            place.delete()
            return None
        lon, lat = coordinates
        place.lon = lon
        place.lat = lat
        place.save()
    return place.lat, place.lon


@user_passes_test(is_manager, login_url='restaurateur:login')
def view_orders(request):
    orders_to_show = (Order.objects
                           .with_order_sum()
                           .order_by('-status')
                           .exclude(status=Order.COMPLETED)
                           .with_available_restaurants())
    addresses = set()
    all_restaurants = Restaurant.objects.all()
    for restaurant in all_restaurants:
        addresses.add(restaurant.address)
    for order in orders_to_show:
        addresses.add(order.address)
    places = Place.objects.filter(address__in=addresses)
    coordinates_for_place = {}
    for place in places:
        coordinates_for_place[place.address] = (place.lat, place.lon)
    for restaurant in all_restaurants:
        if restaurant.address not in coordinates_for_place:
            coordinates_for_place[restaurant.address] = \
                get_coordinates(restaurant.address)
    for order in orders_to_show:
        order_coordinates = coordinates_for_place.get(order.address)
        if not order_coordinates:
            order_coordinates = get_coordinates(order.address)
        for restaurant in order.available_restaurants:
            restaurant.coordinates = coordinates_for_place[restaurant.address]
            if order_coordinates and restaurant.coordinates:
                distance_to_order = distance.distance(
                    order_coordinates,
                    restaurant.coordinates
                ).km
                restaurant.distance_to_order = f'{round(distance_to_order, 3)} км'
            else:
                restaurant.distance_to_order = 'Ошибка геокодера'
    return render(request, template_name='order_items.html', context={
        'order_items': orders_to_show
    })
