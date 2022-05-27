from django.db import models
from django.db.models import F, Sum
from django.utils import timezone
from django.core.validators import MinValueValidator
from phonenumber_field.modelfields import PhoneNumberField


class Restaurant(models.Model):
    name = models.CharField(
        'название',
        max_length=50
    )
    address = models.CharField(
        'адрес',
        max_length=100,
        blank=True,
    )
    contact_phone = models.CharField(
        'контактный телефон',
        max_length=50,
        blank=True,
    )

    class Meta:
        verbose_name = 'ресторан'
        verbose_name_plural = 'рестораны'

    def __str__(self):
        return self.name


class ProductQuerySet(models.QuerySet):
    def available(self):
        products = (
            RestaurantMenuItem.objects
            .filter(availability=True)
            .values_list('product')
        )
        return self.filter(pk__in=products)


class ProductCategory(models.Model):
    name = models.CharField(
        'название',
        max_length=50
    )

    class Meta:
        verbose_name = 'категория'
        verbose_name_plural = 'категории'

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(
        'название',
        max_length=50
    )
    category = models.ForeignKey(
        ProductCategory,
        verbose_name='категория',
        related_name='products',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    price = models.DecimalField(
        'цена',
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    image = models.ImageField(
        'картинка'
    )
    special_status = models.BooleanField(
        'спец.предложение',
        default=False,
        db_index=True,
    )
    description = models.TextField(
        'описание',
        max_length=300,
        blank=True,
    )

    objects = ProductQuerySet.as_manager()

    class Meta:
        verbose_name = 'товар'
        verbose_name_plural = 'товары'

    def __str__(self):
        return self.name


class RestaurantMenuItem(models.Model):
    restaurant = models.ForeignKey(
        Restaurant,
        related_name='menu_items',
        verbose_name="ресторан",
        on_delete=models.CASCADE,
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='menu_items',
        verbose_name='продукт',
    )
    availability = models.BooleanField(
        'в продаже',
        default=True,
        db_index=True
    )

    class Meta:
        verbose_name = 'пункт меню ресторана'
        verbose_name_plural = 'пункты меню ресторана'
        unique_together = [
            ['restaurant', 'product']
        ]

    def __str__(self):
        return f"{self.restaurant.name} - {self.product.name}"


class OrderQuerySet(models.QuerySet):
    def with_order_sum(self):
        return self.prefetch_related('products').annotate(
            order_sum=Sum(F('products__quantity') * F('products__price'))
        )


class Order(models.Model):
    UNPROCESSED = 'UNPRCSSED'
    IN_PROCESS = 'INPROCESS'
    COMPLETED = 'COMPLETED'

    BANK_CARD = 'B'
    CASH = 'C'
    NOT_DEFINED = 'N'

    ORDER_STATUS_CHOICES = [
        (UNPROCESSED, 'Не обработан'),
        (IN_PROCESS, 'В процессе'),
        (COMPLETED, 'Завершен')
    ]

    ORDER_PAYMENT_CHOICES = [
        (BANK_CARD, 'Картой'),
        (CASH, 'Наличными'),
        (NOT_DEFINED, 'Не определен')
    ]

    firstname = models.CharField(
        'имя клиента',
        max_length=50,
    )
    lastname = models.CharField(
        'фамилия клиента',
        max_length=50,
    )
    address = models.CharField(
        'адрес',
        max_length=100,
    )
    phonenumber = PhoneNumberField(
        'номер телефона клиента',
        db_index=True,
    )
    status = models.CharField(
        'статус заказа',
        max_length=9,
        choices=ORDER_STATUS_CHOICES,
        default=UNPROCESSED,
        db_index=True
    )
    payment_method = models.CharField(
        'способ платежа',
        max_length=1,
        choices=ORDER_PAYMENT_CHOICES,
        default=NOT_DEFINED,
        db_index=True
    )
    comment = models.TextField(
        'комментарий',
        blank=True
    )
    registered_at = models.DateTimeField(
        'зарегистрирован',
        default=timezone.now,
        db_index=True
    )
    called_at = models.DateTimeField(
        'совершен звонок',
        blank=True,
        null=True,
        db_index=True
    )
    delivered_at = models.DateTimeField(
        'доставлен',
        blank=True,
        null=True,
        db_index=True
    )

    objects = OrderQuerySet.as_manager()

    class Meta:
        verbose_name = 'заказ'
        verbose_name_plural = 'заказы'

    def __str__(self):
        return f"{self.firstname} {self.lastname} {self.phonenumber}"


class OrderItem(models.Model):
    order = models.ForeignKey(
        Order,
        related_name='products',
        verbose_name='заказ',
        on_delete=models.CASCADE,
    )
    product = models.ForeignKey(
        Product,
        verbose_name='продукт',
        on_delete=models.PROTECT,
    )
    quantity = models.SmallIntegerField(
        'количество',
        validators=[MinValueValidator(1)]
    )
    price = models.DecimalField(
        'Цена',
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )

    class Meta:
        verbose_name = 'позиция заказа'
        verbose_name_plural = 'позиции в заказе'
