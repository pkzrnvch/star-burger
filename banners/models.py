from django.db import models


class BannerCarousel(models.Model):
    page = models.CharField(
        'страница',
        max_length=100,
    )
    slug = models.SlugField(
        'слаг',
    )

    class Meta:
        verbose_name = 'карусель'
        verbose_name_plural = 'карусели'

    def __str__(self):
        return f'{self.page} {self.slug}'


class Banner(models.Model):
    title = models.CharField(
        'заголовок',
        max_length=50,
        blank=True,
    )
    text = models.TextField(
        'текст баннера',
        blank=True,
    )
    image = models.ImageField(
        'картинка',
        upload_to='banners/',
    )
    place = models.ForeignKey(
        BannerCarousel,
        related_name='banners',
        verbose_name='место баннера',
        on_delete=models.CASCADE,
    )
    order = models.PositiveSmallIntegerField(
        'порядок',
        default=0,
        db_index=True,
    )

    class Meta:
        verbose_name = 'баннер'
        verbose_name_plural = 'баннеры'
        ordering = ['order']

    def __str__(self):
        return self.title
