from django.contrib import admin
from unfold.admin import ModelAdmin, StackedInline, TabularInline

from catalog.models import Category, Fabric, Product, ProductFabricPrice, ProductShadeImage, Shade


class ChildCategoryInline(TabularInline):
    model = Category
    fk_name = 'parent'
    extra = 0
    fields = ('name_uk', 'name_ru', 'slug', 'sort', 'is_active', 'image')


class FabricPriceInline(TabularInline):
    model = ProductFabricPrice
    extra = 0
    fields = ('fabric', 'price', 'sku')
    autocomplete_fields = ('fabric',)
    ordering = ('fabric__sort', 'fabric_id')
    show_change_link = True
    tab = True
    verbose_name = 'Ціна за категорію тканини'
    verbose_name_plural = 'Ціни за категоріями тканини (1–7)'


class ShadeImageInline(TabularInline):
    model = ProductShadeImage
    extra = 0
    tab = True


@admin.register(Category)
class CategoryAdmin(ModelAdmin):
    list_display = ('name_uk', 'parent', 'slug', 'sort', 'is_active')
    list_editable = ('sort', 'is_active')
    list_filter = ('is_active', 'parent')
    search_fields = ('name_uk', 'name_ru', 'slug')
    prepopulated_fields = {'slug': ('name_uk',)}
    inlines = [ChildCategoryInline]


@admin.register(Fabric)
class FabricAdmin(ModelAdmin):
    list_display = ('name_uk', 'surcharge', 'sort', 'is_active')
    list_editable = ('sort', 'is_active')
    search_fields = ('name_uk', 'name_ru', 'slug')
    ordering = ('sort', 'id')


@admin.register(Shade)
class ShadeAdmin(ModelAdmin):
    list_display = ('name_uk', 'fabric', 'hex_color', 'sort', 'is_active')
    list_filter = ('fabric', 'is_active')
    search_fields = ('name_uk', 'name_ru', 'slug')


@admin.register(Product)
class ProductAdmin(ModelAdmin):
    list_display = ('name_uk', 'category', 'base_price', 'badge', 'is_available', 'is_active')
    list_filter = ('category', 'badge', 'is_available', 'is_active')
    search_fields = ('name_uk', 'name_ru', 'sku')
    prepopulated_fields = {'slug': ('name_uk',)}
    inlines = [FabricPriceInline, ShadeImageInline]
    fieldsets = (
        (None, {'fields': ('name_uk', 'name_ru', 'slug', 'sku', 'category', 'type_uk', 'type_ru')}),
        ('Ціна та наявність', {
            'fields': ('base_price', 'badge', 'is_available', 'is_active', 'default_image'),
            'description': 'Базова ціна — орієнтир. Фактичні ціни по категоріях тканини 1–7 задаються нижче у вкладці цін.',
        }),
        ('Опис', {'fields': ('description_uk', 'description_ru', 'care_uk', 'care_ru', 'dims_uk', 'dims_ru')}),
        ('Характеристики', {
            'fields': (
                'spec_frame_uk', 'spec_frame_ru',
                'spec_filling_uk', 'spec_filling_ru',
                'spec_mechanism_uk', 'spec_mechanism_ru',
                'spec_textile_uk', 'spec_textile_ru',
                'spec_storage_uk', 'spec_storage_ru',
            ),
        }),
        ('SEO', {'fields': ('seo_title_uk', 'seo_title_ru', 'seo_description_uk', 'seo_description_ru')}),
    )
