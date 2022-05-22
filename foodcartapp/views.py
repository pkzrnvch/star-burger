import json

from django.http import JsonResponse
from django.templatetags.static import static
import phonenumbers
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


@api_view(['POST'])
def register_order(request):
    order_details = request.data
    if 'products' not in order_details:
        return Response(['Products field is required'], status=400)
    if order_details['products'] is None:
        return Response(['Products field cannot be empty'], status=400)
    if not isinstance(order_details['products'], list):
        return Response(['Products must be a list'], status=400)
    if not order_details['products']:
        return Response(['Products cannot be an empty list'], status=400)
    all_product_ids = list(Product.objects.all().values_list('id', flat=True))
    order_product_ids = [position['product'] for position in order_details['products']]
    print(order_product_ids)
    for product_id in order_product_ids:
        if product_id not in all_product_ids:
            return Response(['Invalid product id'], status=400)
    if any(not i for i in order_details.values()):
        return Response(['This field cannot be empty'], status=400)
    keys_to_check = ['firstname', 'lastname', 'address', 'phonenumber']
    for key in keys_to_check:
        if key not in order_details:
            return Response(['Missing a required field'], status=400)
        if not isinstance(order_details[key], str):
            return Response(['This field has to be string'], status=400)
    print(order_details)
    parsed_phone_number = phonenumbers.parse(
        order_details['phonenumber'],
        'RU'
    )
    if not phonenumbers.is_valid_number(parsed_phone_number):
        return Response(['Invalid phone number'], status=400)
    normalized_phone_number = phonenumbers.format_number(
                parsed_phone_number,
                phonenumbers.PhoneNumberFormat.E164
            )
    order = Order.objects.create(
        client_name=order_details['firstname'],
        client_surname=order_details['lastname'],
        address=order_details['address'],
        contact_phone=normalized_phone_number
    )
    for position in order_details['products']:
        order.items.create(
            product_id=position['product'],
            quantity=position['quantity']
        )
    return Response(order_details)
