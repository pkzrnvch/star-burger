import json

from django.http import JsonResponse
from django.templatetags.static import static
import phonenumbers

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


def register_order(request):
    try:
        serialized_order = json.loads(request.body.decode())
    except ValueError:
        return JsonResponse({
            'error': 'Cannot serialize json',
        })
    parsed_phone_number = phonenumbers.parse(
        serialized_order['phonenumber'],
        'RU'
    )
    normalized_phone_number = phonenumbers.format_number(
                parsed_phone_number,
                phonenumbers.PhoneNumberFormat.E164
            )
    order = Order.objects.create(
        client_name=serialized_order['firstname'],
        client_surname=serialized_order['lastname'],
        address=serialized_order['address'],
        contact_phone=normalized_phone_number
    )
    for position in serialized_order['products']:
        order.items.create(
            product_id=position['product'],
            quantity=position['quantity']
        )
    return JsonResponse(data=serialized_order)
