from django.contrib import admin
from django.utils.html import format_html
from .models import Banner, BannerCarousel

from adminsortable2.admin import SortableStackedInline, SortableAdminBase


class BannerStackedInline(SortableStackedInline):
    model = Banner
    readonly_fields = ('preview_image',)
    fields = ('title', 'text', 'image', 'preview_image', 'order')
    ordering = ('order',)

    def preview_image(self, obj):
        return format_html(
            '<img src="{}" width=auto height=200px />',
            obj.image.url,
        )

    def get_extra(self, request, obj=None, **kwargs):
        return 0


@admin.register(BannerCarousel)
class BannerCarouselAdmin(SortableAdminBase, admin.ModelAdmin):
    inlines = [BannerStackedInline]
