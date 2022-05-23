import json
from collections import OrderedDict

from django.http import JsonResponse
from django.templatetags.static import static
import phonenumbers
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import serializers


from .models import Product, Order, OrderProductItem


def banners_list_api(request):
    # FIXME move data to db?
    return JsonResponse([
        {
            'title': 'Burger',
            'src': static('burger.jpg'),
            'text': 'Tasty Burger at your door step',
        },
        {
            'title': 'Spices',
            'src': static('food.jpg'),
            'text': 'All Cuisines',
        },
        {
            'title': 'New York',
            'src': static('tasty.jpg'),
            'text': 'Food is incomplete without a tasty dessert',
        }
    ], safe=False, json_dumps_params={
        'ensure_ascii': False,
        'indent': 4,
    })


def product_list_api(request):
    products = Product.objects.select_related('category').available()

    dumped_products = []
    for product in products:
        dumped_product = {
            'id': product.id,
            'name': product.name,
            'price': product.price,
            'special_status': product.special_status,
            'description': product.description,
            'category': {
                'id': product.category.id,
                'name': product.category.name,
            } if product.category else None,
            'image': product.image.url,
            'restaurant': {
                'id': product.id,
                'name': product.name,
            }
        }
        dumped_products.append(dumped_product)
    return JsonResponse(dumped_products, safe=False, json_dumps_params={
        'ensure_ascii': False,
        'indent': 4,
    })


class OrderProductItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderProductItem
        fields = ['product', 'quantity']


class OrderSerializer(serializers.ModelSerializer):
    products = OrderProductItemSerializer(many=True, allow_empty=False)

    class Meta:
        model = Order
        fields = ['firstname', 'lastname', 'address', 'phonenumber', 'products']
        extra_kwargs = {
            "phonenumber": {
                "validators": [],
            },
        }

    def validate_phonenumber(self, value):
        try:
            parsed_phone_number = phonenumbers.parse(
                value,
                'RU'
            )
        except phonenumbers.NumberParseException:
            raise serializers.ValidationError(['Некорректный номер телефона'])
        if not phonenumbers.is_valid_number(parsed_phone_number):
            raise serializers.ValidationError(['Некорректный номер телефона'])
        normalized_phone_number = phonenumbers.format_number(
            parsed_phone_number,
            phonenumbers.PhoneNumberFormat.E164
        )
        return normalized_phone_number

    def create(self, validated_data):
        order_items_data = validated_data.pop('products')
        order = Order.objects.create(**validated_data)
        for order_item_data in order_items_data:
            OrderProductItem.objects.create(order=order, **order_item_data)
        return order


@api_view(['POST'])
def register_order(request):
    serializer = OrderSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(serializer.data)
