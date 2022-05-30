from django.db import models
from django.utils import timezone


class Place(models.Model):
    address = models.CharField(
        'адрес',
        max_length=100,
        unique=True
    )
    lat = models.DecimalField(
        'Широта',
        decimal_places=6,
        max_digits=8,
        null=True,
        blank=True
    )
    lon = models.DecimalField(
        'Долгота',
        decimal_places=6,
        max_digits=9,
        null=True,
        blank=True
    )
    fetched_at = models.DateTimeField(
        'Дата записи координат',
        default=timezone.now
    )

    class Meta:
        verbose_name = 'место'
        verbose_name_plural = 'места'

    def __str__(self):
        return f'{self.address}: {self.lon}, {self.lat}'
