import re

from django import forms
from django.contrib import admin
from django.utils.html import format_html
from catalog.models import (
    Category,
    Characteristic,
    Fabric,
    Product,
    ProductCharacteristic,
    ProductColor,
    ProductColorImage,
    ProductColorOption,
    ProductFabricPrice,
    Shade,
)
from core.admin_base import ModelAdmin, TabularInline
from core.admin_widgets import CmsAdminColorWidget, CmsAdminImageWidget


def _subcategory_queryset():
    return (
        Category.objects
        .filter(parent__isnull=False)
        .select_related('parent')
        .order_by('parent__sort', 'parent_id', 'sort', 'id')
    )


def _subcategory_label(obj: Category) -> str:
    if obj.parent_id:
        return f'{obj.parent.name_uk} → {obj.name_uk}'
    return obj.name_uk


class ProductAdminForm(forms.ModelForm):
    type_subcategory = forms.ModelChoiceField(
        label='Тип',
        queryset=Category.objects.none(),
        required=False,
        empty_label='— оберіть підкатегорію —',
        widget=forms.Select(attrs={'class': 'rs-admin-btn-select'}),
    )

    class Meta:
        model = Product
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        qs = _subcategory_queryset()
        field = self.fields['type_subcategory']
        field.queryset = qs
        field.label_from_instance = _subcategory_label

        initial = None
        instance = self.instance
        if instance and instance.pk:
            if instance.type_uk:
                initial = qs.filter(name_uk=instance.type_uk).first()
            if initial is None and instance.category_id and instance.category.parent_id:
                initial = qs.filter(pk=instance.category_id).first()
        if initial is not None:
            field.initial = initial.pk

    def save(self, commit=True):
        instance = super().save(commit=False)
        sub = self.cleaned_data.get('type_subcategory')
        if sub:
            instance.type_uk = sub.name_uk
            instance.type_ru = sub.name_ru or ''
        if commit:
            instance.save()
            self.save_m2m()
        return instance


class ChildCategoryInline(TabularInline):
    model = Category
    fk_name = 'parent'
    extra = 0
    fields = ('name_uk', 'slug', 'sort', 'is_active')
    readonly_fields = ('slug',)
    verbose_name = 'Підкатегорія'
    verbose_name_plural = 'Підкатегорії (2 рівень)'
    show_change_link = True
    tab = True


class FabricPriceInline(TabularInline):
    model = ProductFabricPrice
    extra = 0
    fields = ('fabric', 'price', 'sale_price', 'sku')
    autocomplete_fields = ('fabric',)
    ordering = ('fabric__sort', 'fabric_id')
    show_change_link = True
    tab = True
    verbose_name = 'Ціна за категорію тканини'
    verbose_name_plural = 'Ціни за категоріями тканини (1–7)'


class ProductColorInline(TabularInline):
    model = ProductColor
    extra = 1
    fields = ('color', 'sort', 'is_active')
    ordering = ('sort', 'id')
    tab = True
    verbose_name = 'Колір'
    verbose_name_plural = 'Кольори товару'
    show_change_link = True

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'color':
            kwargs['queryset'] = ProductColorOption.objects.filter(is_active=True).order_by('sort', 'id')
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


class ProductColorImageForm(forms.ModelForm):
    """Нові рядки без файлу ігноруються (порожній extra не валить збереження)."""

    class Meta:
        model = ProductColorImage
        fields = ('image', 'sort')

    def has_changed(self):
        if self.instance.pk:
            return super().has_changed()
        if not self.is_bound:
            return False
        return bool(self.files.get(self.add_prefix('image')))


class EmptyColorGalleryInline(TabularInline):
    """
    Вкладка «Фото» на add / поки немає кольорів.
    Лише підказка — завантажувати фото ще нікуди (потрібен color_id).
    """

    model = ProductColorImage
    form = ProductColorImageForm
    fk_name = 'product'
    extra = 0
    max_num = 0
    can_delete = False
    fields = ('image', 'sort')
    tab = True
    show_title = False
    verbose_name = 'Фото'
    verbose_name_plural = 'Фото'
    gallery_color_id = 0
    gallery_color_name = ''
    template = 'admin/catalog/product/color_gallery_tabular.html'
    template_before = 'admin/catalog/product/color_gallery_swatches.html'

    def get_queryset(self, request):
        return super().get_queryset(request).none()

    def has_add_permission(self, request, obj=None):
        return False

    def get_formset(self, request, obj=None, **kwargs):
        FormSet = super().get_formset(request, obj, **kwargs)

        class EmptyGalleryFormSet(FormSet):
            @classmethod
            def get_default_prefix(cls):
                return 'color_images'

        return EmptyGalleryFormSet


def _color_gallery_inline(color_option_id: int, title: str, *, is_primary: bool = False):
    """
    Окремий formset на колір — color_id ставить СЕРВЕР (як у 569b534).
    У UI всі панелі живуть у вкладці «Фото»; кружечки лише перемикають видимість.
    """
    cid = int(color_option_id)

    class ColorGalleryInline(TabularInline):
        model = ProductColorImage
        form = ProductColorImageForm
        fk_name = 'product'
        extra = 1
        fields = ('image', 'sort')
        ordering = ('sort', 'id')
        # Лише перший створює вкладку «Фото»; решта панелей теж у ній (x-show у template).
        tab = is_primary
        show_title = False
        verbose_name = 'Фото'
        verbose_name_plural = 'Фото'
        gallery_color_id = cid
        gallery_color_name = title
        template = 'admin/catalog/product/color_gallery_tabular.html'
        # Кружечки рендеряться ПОЗА панеллю (див. color_gallery_tabular.html).
        template_before = (
            'admin/catalog/product/color_gallery_swatches.html' if is_primary else None
        )

        def get_queryset(self, request):
            return super().get_queryset(request).filter(color_id=cid)

        def get_formset(self, request, obj=None, **kwargs):
            FormSet = super().get_formset(request, obj, **kwargs)
            # Вкладка «Фото» = #color_images; інші кольори — окремі префікси.
            prefix = 'color_images' if is_primary else f'color_images_{cid}'

            class ColorBoundFormSet(FormSet):
                @classmethod
                def get_default_prefix(cls):
                    return prefix

                def save_new(self, form, commit=True):
                    instance = super().save_new(form, commit=False)
                    instance.color_id = cid
                    if commit:
                        instance.save()
                        form.save_m2m()
                    return instance

                def save_existing(self, form, instance, commit=True):
                    instance.color_id = cid
                    return super().save_existing(form, instance, commit)

            return ColorBoundFormSet

        def formfield_for_dbfield(self, db_field, request, **kwargs):
            if db_field.name == 'image':
                kwargs['widget'] = CmsAdminImageWidget()
            return super().formfield_for_dbfield(db_field, request, **kwargs)

    ColorGalleryInline.__name__ = f'ColorGalleryInline_{cid}'
    ColorGalleryInline.__qualname__ = f'ColorGalleryInline_{cid}'
    return ColorGalleryInline


class ProductCharacteristicInline(TabularInline):
    model = ProductCharacteristic
    extra = 0
    fields = ('characteristic', 'value_uk', 'value_ru', 'sort')
    ordering = ('characteristic__sort', 'sort', 'id')
    autocomplete_fields = ('characteristic',)
    tab = True
    verbose_name = 'Характеристика'
    verbose_name_plural = 'Характеристики'
    show_change_link = True

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'characteristic':
            kwargs['queryset'] = Characteristic.objects.filter(is_active=True).order_by('sort', 'id')
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


@admin.register(Category)
class CategoryAdmin(ModelAdmin):
    list_display = ('name_uk', 'parent', 'slug', 'sort', 'is_active')
    list_editable = ('sort', 'is_active')
    list_filter = ('is_active', 'parent')
    search_fields = ('name_uk', 'name_ru', 'slug')
    readonly_fields = ('slug',)
    inlines = [ChildCategoryInline]
    autocomplete_fields = ('parent',)
    fieldsets = (
        ('Контент (ukr)', {
            'classes': ('tab',),
            'fields': (
                'parent',
                'name_uk',
                'slug',
                'sort',
                'is_active',
                'seo_title_uk',
                'seo_description_uk',
            ),
            'description': (
                'Батьківська категорія порожня = категорія 1 рівня. '
                'Якщо обрати батька — це буде підкатегорія (2 рівень). '
                'URL-адреса генерується з назви (ukr) автоматично.'
            ),
        }),
        ('Контент (ru)', {
            'classes': ('tab',),
            'fields': (
                'name_ru',
                'seo_title_ru',
                'seo_description_ru',
            ),
        }),
    )


@admin.register(Characteristic)
class CharacteristicAdmin(ModelAdmin):
    list_display = ('name_uk', 'name_ru', 'sort', 'is_active')
    list_editable = ('sort', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name_uk', 'name_ru')
    ordering = ('sort', 'id')
    fieldsets = (
        ('Контент (ukr)', {
            'classes': ('tab',),
            'fields': (
                'name_uk',
                'sort',
                'is_active',
            ),
            'description': (
                'Типи характеристик для карток товарів. '
                'У товарі обираєте тип зі списку і вказуєте значення.'
            ),
        }),
        ('Контент (ru)', {
            'classes': ('tab',),
            'fields': ('name_ru',),
        }),
    )


@admin.register(Fabric)
class FabricAdmin(ModelAdmin):
    list_display = ('name_uk', 'slug', 'surcharge', 'sort', 'is_active')
    list_editable = ('sort', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name_uk', 'name_ru', 'slug')
    readonly_fields = ('slug',)
    ordering = ('sort', 'id')
    fieldsets = (
        ('Контент (ukr)', {
            'classes': ('tab',),
            'fields': (
                'name_uk',
                'slug',
                'surcharge',
                'sort',
                'is_active',
            ),
        }),
        ('Контент (ru)', {
            'classes': ('tab',),
            'fields': ('name_ru',),
        }),
    )


@admin.register(Shade)
class ShadeAdmin(ModelAdmin):
    list_display = ('name_uk', 'fabric', 'slug', 'hex_color', 'sort', 'is_active')
    list_filter = ('fabric', 'is_active')
    search_fields = ('name_uk', 'name_ru', 'slug')
    readonly_fields = ('slug',)
    autocomplete_fields = ('fabric',)
    fieldsets = (
        ('Контент (ukr)', {
            'classes': ('tab',),
            'fields': (
                'fabric',
                'name_uk',
                'slug',
                'hex_color',
                'swatch',
                'sort',
                'is_active',
            ),
        }),
        ('Контент (ru)', {
            'classes': ('tab',),
            'fields': ('name_ru',),
        }),
    )

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        if db_field.name == 'hex_color':
            kwargs['widget'] = CmsAdminColorWidget(default_color='#D4C4A8')
        return super().formfield_for_dbfield(db_field, request, **kwargs)


@admin.register(ProductColorOption)
class ProductColorOptionAdmin(ModelAdmin):
    list_display = ('swatch_preview', 'name_uk', 'name_ru', 'hex_color', 'slug', 'sort', 'is_active')
    list_editable = ('sort', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name_uk', 'name_ru', 'slug', 'hex_color')
    readonly_fields = ('slug',)
    ordering = ('sort', 'id')
    fieldsets = (
        ('Контент (ukr)', {
            'classes': ('tab',),
            'fields': (
                'name_uk',
                'slug',
                'hex_color',
                'sort',
                'is_active',
            ),
            'description': (
                'Стандартні кольори для кружечків товарів. '
                'Новий колір можна додати пікером і використовувати в інших моделях.'
            ),
        }),
        ('Контент (ru)', {
            'classes': ('tab',),
            'fields': ('name_ru',),
        }),
    )

    @admin.display(description='')
    def swatch_preview(self, obj):
        hex_color = (obj.hex_color or '').strip() or '#ccc'
        if not re.fullmatch(r'#[0-9A-Fa-f]{3}([0-9A-Fa-f]{3})?', hex_color):
            hex_color = '#ccc'
        return format_html(
            '<span style="display:inline-block;width:1.25rem;height:1.25rem;'
            'border-radius:999px;background:{};border:1px solid #d0cdc8;"></span>',
            hex_color,
        )

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        if db_field.name == 'hex_color':
            kwargs['widget'] = CmsAdminColorWidget(default_color='#D4C4A8')
        return super().formfield_for_dbfield(db_field, request, **kwargs)


@admin.register(Product)
class ProductAdmin(ModelAdmin):
    form = ProductAdminForm
    list_display = (
        'name_uk', 'category', 'base_price', 'is_on_sale', 'sale_price',
        'badge', 'is_available', 'is_active',
    )
    list_filter = ('category', 'badge', 'is_on_sale', 'is_available', 'is_active')
    list_editable = ('is_on_sale',)
    search_fields = ('name_uk', 'name_ru', 'sku')
    readonly_fields = ('slug', 'type_ru')
    inlines = [FabricPriceInline, ProductColorInline, ProductCharacteristicInline]
    fieldsets = (
        ('Контент (ukr)', {
            'classes': ('tab',),
            'fields': (
                'name_uk',
                'slug',
                'sku',
                'category',
                'type_subcategory',
                'base_price',
                'is_on_sale',
                'sale_price',
                'badge',
                'is_available',
                'is_active',
                'description_uk',
                'care_uk',
                'dims_uk',
                'seo_title_uk',
                'seo_description_uk',
            ),
        }),
        ('Контент (ru)', {
            'classes': ('tab',),
            'fields': (
                'name_ru',
                'type_ru',
                'description_ru',
                'care_ru',
                'dims_ru',
                'seo_title_ru',
                'seo_description_ru',
            ),
        }),
    )

    change_form_template = 'admin/catalog/product/change_form.html'

    @property
    def media(self):
        return super().media + forms.Media(
            css={'all': ('css/admin/product_form.css',)},
            js=('js/admin/product_color_gallery.js',),
        )

    def get_inlines(self, request, obj=None):
        inlines = [FabricPriceInline, ProductColorInline]
        rows = []
        if obj is not None:
            rows = list(
                ProductColor.objects
                .filter(product_id=obj.pk)
                .select_related('color')
                .order_by('sort', 'id')
            )
        gallery_added = False
        for index, row in enumerate(rows):
            if not row.color_id:
                continue
            name = row.color.name_uk if row.color_id else f'#{row.pk}'
            inlines.append(
                _color_gallery_inline(
                    row.color_id,
                    name,
                    is_primary=(index == 0),
                )
            )
            gallery_added = True
        # Add / товар без кольорів — вкладка «Фото» з підказкою
        if not gallery_added:
            inlines.append(EmptyColorGalleryInline)
        inlines.append(ProductCharacteristicInline)
        return inlines

    def changeform_view(self, request, object_id=None, form_url='', extra_context=None):
        extra_context = extra_context or {}
        swatches = []
        if object_id:
            rows = (
                ProductColor.objects
                .filter(product_id=object_id)
                .select_related('color')
                .order_by('sort', 'id')
            )
            for row in rows:
                opt = row.color
                if not opt:
                    continue
                hex_color = (opt.hex_color or '').strip() or '#ccc'
                if not re.fullmatch(r'#[0-9A-Fa-f]{3}([0-9A-Fa-f]{3})?', hex_color):
                    hex_color = '#ccc'
                swatches.append({
                    'id': opt.pk,
                    'name': opt.name_uk,
                    'hex': hex_color,
                })
        extra_context['product_color_swatches'] = swatches
        return super().changeform_view(request, object_id, form_url, extra_context)

