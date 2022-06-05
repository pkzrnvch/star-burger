import phonenumbers
from django.db import transaction
from django.http import JsonResponse
from django.templatetags.static import static
from rest_framework import serializers
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import Product, Order, OrderItem


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


class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ['product', 'quantity']


class OrderSerializer(serializers.ModelSerializer):
    products = OrderItemSerializer(many=True, allow_empty=False, source='items')

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

    @transaction.atomic
    def create(self, validated_data):
        order_items_details = validated_data.pop('items')
        order = Order.objects.create(**validated_data)
        order_items = []
        for order_item_details in order_items_details:
            order_items.append(OrderItem(
                order=order,
                price=order_item_details['product'].price,
                **order_item_details
            ))
        OrderItem.objects.bulk_create(order_items)
        return order


@api_view(['POST'])
def register_order(request):
    serializer = OrderSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(serializer.data)
