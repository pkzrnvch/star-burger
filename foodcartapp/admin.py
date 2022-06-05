from collections import defaultdict

from django.contrib import admin
from django.shortcuts import reverse, redirect
from django.templatetags.static import static
from django.utils.html import format_html
from django.utils.http import url_has_allowed_host_and_scheme
from django.conf import settings
from django import forms

from .models import Product
from .models import ProductCategory
from .models import Restaurant
from .models import RestaurantMenuItem
from .models import Order
from .models import OrderItem


class RestaurantMenuItemInline(admin.TabularInline):
    model = RestaurantMenuItem
    extra = 0


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    readonly_fields = ('price',)
    extra = 0


@admin.register(Restaurant)
class RestaurantAdmin(admin.ModelAdmin):
    search_fields = [
        'name',
        'address',
        'contact_phone',
    ]
    list_display = [
        'name',
        'address',
        'contact_phone',
    ]
    inlines = [
        RestaurantMenuItemInline
    ]


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = [
        'get_image_list_preview',
        'name',
        'category',
        'price',
    ]
    list_display_links = [
        'name',
    ]
    list_filter = [
        'category',
    ]
    search_fields = [
        # FIXME SQLite can not convert letter case for cyrillic words properly, so search will be buggy.
        # Migration to PostgreSQL is necessary
        'name',
        'category__name',
    ]

    inlines = [
        RestaurantMenuItemInline
    ]
    fieldsets = (
        ('Общее', {
            'fields': [
                'name',
                'category',
                'image',
                'get_image_preview',
                'price',
            ]
        }),
        ('Подробно', {
            'fields': [
                'special_status',
                'description',
            ],
            'classes': [
                'wide'
            ],
        }),
    )

    readonly_fields = [
        'get_image_preview',
    ]

    class Media:
        css = {
            "all": (
                static("admin/foodcartapp.css")
            )
        }

    def get_image_preview(self, obj):
        if not obj.image:
            return 'выберите картинку'
        return format_html('<img src="{url}" style="max-height: 200px;"/>', url=obj.image.url)
    get_image_preview.short_description = 'превью'

    def get_image_list_preview(self, obj):
        if not obj.image or not obj.id:
            return 'нет картинки'
        edit_url = reverse('admin:foodcartapp_product_change', args=(obj.id,))
        return format_html('<a href="{edit_url}"><img src="{src}" style="max-height: 50px;"/></a>', edit_url=edit_url, src=obj.image.url)
    get_image_list_preview.short_description = 'превью'


@admin.register(ProductCategory)
class ProductAdmin(admin.ModelAdmin):
    pass


class OrderAdminForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(OrderAdminForm, self).__init__(*args, **kwargs)
        product_ids = (order_item.product_id for order_item in self.instance.items.all())
        restaurants_for_products = defaultdict(set)
        restaurant_menu_items = (RestaurantMenuItem.objects
                                 .filter(availability=True))
        for menu_item in restaurant_menu_items:
            restaurants_for_products[menu_item.product_id].add(menu_item.restaurant_id)
        available_restaurants = restaurants_for_products[next(product_ids)]
        for product_id in product_ids:
            available_restaurants &= restaurants_for_products[product_id]
        self.fields['restaurant'].queryset = \
            self.fields['restaurant'].queryset.filter(id__in=available_restaurants)


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_select_related = True
    search_fields = [
        'phonenumber',
    ]
    inlines = [
        OrderItemInline
    ]
    form = OrderAdminForm

    def response_post_save_change(self, request, obj):
        standard_response = super().response_post_save_change(request, obj)
        redirect_to = request.GET.get('next')
        url_is_safe = url_has_allowed_host_and_scheme(
            url=redirect_to,
            allowed_hosts=settings.ALLOWED_HOSTS,
        )
        if redirect_to and url_is_safe:
            return redirect(redirect_to)
        else:
            return standard_response

    def save_formset(self, request, form, formset, change):
        instances = formset.save(commit=False)
        for instance in instances:
            if not instance.price:
                instance.price = instance.product.price
            instance.save()
        formset.save()
