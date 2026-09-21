from django.core.management.base import BaseCommand

from catalog.models import Category, Fabric, Product, ProductFabricPrice, ProductShadeImage, Shade
from core.management.seed_media import attach
from core.models import AboutPage, CollabPage, HomePage, LegalPage, SiteSettings, ValueProp


class Command(BaseCommand):
    help = 'Ідемпотентний демо-контент з дизайн-прототипу ROSSA'

    def handle(self, *args, **options):
        self._settings()
        self._home()
        self._value_props()
        self._about()
        self._collab()
        self._legal()
        fabrics = self._fabrics()
        categories = self._categories()
        self._products(categories, fabrics)
        self.stdout.write(self.style.SUCCESS('seed_demo OK'))

    def _settings(self):
        obj, _ = SiteSettings.objects.get_or_create(pk=1, defaults={
            'phone': '+380 44 123 45 67',
            'email': 'hello@rossa.ua',
            'telegram_url': 'https://t.me/rossaukr',
            'telegram_handle': '@rossaukr',
            'address_uk': 'м. Київ, вул. Індустріальна, 12',
            'address_ru': 'г. Киев, ул. Индустриальная, 12',
            'hours_uk': 'Пн–Сб, 10:00–19:00',
            'hours_ru': 'Пн–Сб, 10:00–19:00',
            'footer_tagline_uk': 'М’які меблі преміум-класу власного виробництва.',
            'footer_tagline_ru': 'Мягкая мебель премиум-класса собственного производства.',
            'guarantee_uk': 'Гарантія: 18 місяців',
            'guarantee_ru': 'Гарантия: 18 месяцев',
            'delivery_label_uk': 'Доставка: від 3 тижнів',
            'delivery_label_ru': 'Доставка: от 3 недель',
        })
        attach(obj.logo, 'logo/rossa-logo.png')
        attach(obj.map_image, 'slots/contact-map.webp')
        obj.save()

    def _home(self):
        obj, _ = HomePage.objects.get_or_create(pk=1, defaults={
            'hero_title_uk': 'Меблі, створені для дому',
            'hero_title_ru': 'Мебель, созданная для дома',
            'hero_sub_uk': 'М’які меблі з натуральних матеріалів. Індивідуальний пошив, доставка по всій Україні.',
            'hero_sub_ru': 'Мягкая мебель из натуральных материалов. Индивидуальный пошив, доставка по всей Украине.',
            'cta_catalog_uk': 'Дивитись каталог',
            'cta_catalog_ru': 'Смотреть каталог',
            'section_categories_uk': 'Категорії',
            'section_categories_ru': 'Категории',
            'section_bestsellers_uk': 'Популярні моделі',
            'section_bestsellers_ru': 'Популярные модели',
            'craft_title_uk': 'Кожна деталь має значення',
            'craft_title_ru': 'Каждая деталь имеет значение',
            'craft_body_uk': 'Каркаси з масиву дерева, незалежні пружинні блоки та тканини від європейських постачальників. Ми контролюємо якість на кожному етапі виробництва.',
            'craft_body_ru': 'Каркасы из массива дерева, независимые пружинные блоки и ткани от европейских поставщиков. Мы контролируем качество на каждом этапе производства.',
            'craft_link_uk': 'Дізнатись більше про нас',
            'craft_link_ru': 'Узнать больше о нас',
            'cta_banner_title_uk': 'Не можете обрати модель? Ми допоможемо підібрати меблі під ваш інтер’єр.',
            'cta_banner_title_ru': 'Не можете выбрать модель? Мы поможем подобрать мебель под ваш интерьер.',
            'seo_title_uk': 'ROSSA — м’які меблі власного виробництва',
            'seo_title_ru': 'ROSSA — мягкая мебель собственного производства',
            'seo_description_uk': 'Дивани, ліжка та пуфи. Індивідуальний пошив тканини, доставка по Україні.',
            'seo_description_ru': 'Диваны, кровати и пуфы. Индивидуальный пошив ткани, доставка по Украине.',
        })
        attach(obj.hero_poster, 'slots/hero-video.webp')
        attach(obj.craft_image, 'craft.jpg')
        obj.save()

    def _value_props(self):
        items = [
            ('01', 'Матеріали преміум-класу', 'Материалы премиум-класса',
             'Тканини та шкіра від перевірених європейських постачальників.',
             'Ткани и кожа от проверенных европейских поставщиков.'),
            ('02', 'Гарантія 5 років', 'Гарантия 5 лет',
             'На каркас та механізми трансформації.',
             'На каркас и механизмы трансформации.'),
            ('03', 'Доставка по Україні', 'Доставка по Украине',
             'Збірка та підйом на поверх включені у вартість.',
             'Сборка и подъём на этаж включены в стоимость.'),
            ('04', 'Індивідуальний пошив', 'Индивидуальный пошив',
             'Оберіть тканину та розміри під ваш простір.',
             'Выберите ткань и размеры под ваше пространство.'),
        ]
        for i, (num, tu, tr, bu, br) in enumerate(items):
            ValueProp.objects.get_or_create(number=num, defaults={
                'title_uk': tu, 'title_ru': tr, 'body_uk': bu, 'body_ru': br, 'sort': i,
            })

    def _about(self):
        obj, _ = AboutPage.objects.get_or_create(pk=1, defaults={
            'title_uk': 'Про ROSSA',
            'title_ru': 'О ROSSA',
            'body_uk': 'ROSSA — бренд м’яких меблів власного виробництва. Ми поєднуємо традиційну столярну майстерність із сучасним дизайном, щоб створювати меблі, які служать роками. Кожна модель проходить через руки майстрів — від розкрою тканини до фінальної збірки.',
            'body_ru': 'ROSSA — бренд мягкой мебели собственного производства. Мы соединяем традиционное столярное мастерство с современным дизайном, чтобы создавать мебель, которая служит годами. Каждая модель проходит через руки мастеров — от раскроя ткани до финальной сборки.',
            'milestones': [
                {'year': '2011', 'body_uk': 'Заснування майстерні, перші дивани на замовлення.', 'body_ru': 'Основание мастерской, первые диваны на заказ.'},
                {'year': '2016', 'body_uk': 'Власне виробництво каркасів і пружинних блоків.', 'body_ru': 'Собственное производство каркасов и пружинных блоков.'},
                {'year': '2020', 'body_uk': 'Розширення асортименту: ліжка та пуфи.', 'body_ru': 'Расширение ассортимента: кровати и пуфы.'},
                {'year': '2024', 'body_uk': 'Шоурум і доставка по всій Україні.', 'body_ru': 'Шоурум и доставка по всей Украине.'},
            ],
            'values': [
                {'num': '01', 'title_uk': 'Якість', 'title_ru': 'Качество', 'body_uk': 'Контроль на кожному етапі виробництва.', 'body_ru': 'Контроль на каждом этапе производства.'},
                {'num': '02', 'title_uk': 'Довговічність', 'title_ru': 'Долговечность', 'body_uk': 'Матеріали, розраховані на роки використання.', 'body_ru': 'Материалы, рассчитанные на годы использования.'},
                {'num': '03', 'title_uk': 'Дизайн', 'title_ru': 'Дизайн', 'body_uk': 'Лаконічні форми для сучасного інтер’єру.', 'body_ru': 'Лаконичные формы для современного интерьера.'},
                {'num': '04', 'title_uk': 'Сервіс', 'title_ru': 'Сервис', 'body_uk': 'Гарантія та підтримка після покупки.', 'body_ru': 'Гарантия и поддержка после покупки.'},
            ],
            'seo_title_uk': 'Про нас — ROSSA',
            'seo_description_uk': 'Історія бренду ROSSA, виробництво та цінності.',
        })
        attach(obj.hero_image, 'slots/about-hero.webp')
        if not obj.craft_images:
            mapping = [
                ('about-fabric.webp', 'Тканини', 'Ткани'),
                ('about-frame.webp', 'Каркас і наповнення', 'Каркас и наполнение'),
                ('about-assembly.webp', 'Ручна збірка', 'Ручная сборка'),
            ]
            items = []
            for filename, lu, lr in mapping:
                from django.core.files.storage import default_storage
                from django.core.files import File
                from pathlib import Path
                src = Path(__file__).resolve().parents[2] / 'static' / 'images' / 'slots' / filename
                dest = f'about/{filename}'
                if src.exists() and not default_storage.exists(dest):
                    with src.open('rb') as fh:
                        dest = default_storage.save(dest, File(fh))
                items.append({'image': f'/media/{dest}', 'label_uk': lu, 'label_ru': lr})
            obj.craft_images = items
        obj.save()

    def _collab(self):
        obj, _ = CollabPage.objects.get_or_create(pk=1, defaults={
            'title_uk': 'Співпраця з ROSSA',
            'title_ru': 'Сотрудничество с ROSSA',
            'sub_uk': 'Оптові умови для дизайнерів інтер’єру, дилерів та готельного бізнесу.',
            'sub_ru': 'Оптовые условия для дизайнеров интерьера, дилеров и гостиничного бизнеса.',
            'form_title_uk': 'Залишити заявку на співпрацю',
            'form_title_ru': 'Оставить заявку на сотрудничество',
            'benefits': [
                {'num': '01', 'title_uk': 'Дилерські ціни', 'title_ru': 'Дилерские цены', 'body_uk': 'Спеціальні умови від обсягу закупівлі.', 'body_ru': 'Специальные условия от объёма закупки.'},
                {'num': '02', 'title_uk': 'Каталог для дизайнерів', 'title_ru': 'Каталог для дизайнеров', 'body_uk': 'Технічні креслення та зразки тканин на запит.', 'body_ru': 'Технические чертежи и образцы тканей по запросу.'},
                {'num': '03', 'title_uk': 'Персональний менеджер', 'title_ru': 'Персональный менеджер', 'body_uk': 'Супровід проєкту від замовлення до монтажу.', 'body_ru': 'Сопровождение проекта от заказа до монтажа.'},
            ],
            'seo_title_uk': 'Співпраця — ROSSA',
            'seo_description_uk': 'Оптові умови для дилерів, салонів і дизайнерів.',
        })
        attach(obj.hero_image, 'slots/collab-hero.webp')
        obj.save()

    def _legal(self):
        pages = [
            ('otrymannya', 'Як отримати замовлення', 'Как получить заказ',
             'Після заявки менеджер телефонує, щоб узгодити комплектацію.\n\nСамовивіз / завантаження — на виробництві.\n\nДоставка власним авто клієнта.\n\nОнлайн-оплати та тарифів перевізників на сайті немає.'),
            ('oferta', 'Договір оферти', 'Договор оферты',
             'TODO: юридичний текст оферти замовника. Редагується в адмінці.'),
            ('privacy', 'Політика конфіденційності', 'Политика конфиденциальности',
             'TODO: текст політики конфіденційності замовника. Редагується в адмінці.'),
        ]
        for slug, tu, tr, body in pages:
            LegalPage.objects.get_or_create(slug=slug, defaults={
                'title_uk': tu, 'title_ru': tr, 'body_uk': body, 'body_ru': body,
            })

    def _fabrics(self):
        data = [
            ('rogozhka', 'Рогожка', 'Рогожка', 0, 0),
            ('oksamyt', 'Оксамит', 'Бархат', 3200, 1),
            ('ecoshkira', 'Екошкіра', 'Экокожа', 5800, 2),
        ]
        out = {}
        for slug, uk, ru, surcharge, sort in data:
            obj, _ = Fabric.objects.get_or_create(slug=slug, defaults={
                'name_uk': uk, 'name_ru': ru, 'surcharge': surcharge, 'sort': sort,
            })
            out[slug] = obj
        shades = {
            'rogozhka': [('taupe', 'Тауп', '#6B6255'), ('sand', 'Пісок', '#C7BBA3'), ('wine', 'Вино', '#903838')],
            'oksamyt': [('ivory', 'Айворі', '#C9BFA5'), ('stone', 'Камінь', '#7C7267'), ('forest', 'Ліс', '#4A5A52')],
            'ecoshkira': [('cream', 'Крем', '#D8CFC0'), ('graphite', 'Графіт', '#3E4B5C'), ('black', 'Чорний', '#1A1817')],
        }
        for fabric_slug, items in shades.items():
            fabric = out[fabric_slug]
            for i, (slug, name, hex_color) in enumerate(items):
                Shade.objects.get_or_create(fabric=fabric, slug=slug, defaults={
                    'name_uk': name, 'name_ru': name, 'hex_color': hex_color, 'sort': i,
                })
        return out

    def _categories(self):
        sofas, _ = Category.objects.get_or_create(slug='divany', parent=None, defaults={
            'name_uk': 'Дивани', 'name_ru': 'Диваны', 'sort': 0,
            'intro_uk': 'Модульні, кутові та прямі дивани власного виробництва з можливістю вибору тканини.',
            'intro_ru': 'Модульные, угловые и прямые диваны собственного производства с возможностью выбора ткани.',
        })
        attach(sofas.image, 'slots/cat-sofas.webp')
        sofas.save()
        beds, _ = Category.objects.get_or_create(slug='lizhka', parent=None, defaults={
            'name_uk': 'Ліжка', 'name_ru': 'Кровати', 'sort': 1,
        })
        attach(beds.image, 'slots/cat-beds.webp')
        beds.save()
        poufs, _ = Category.objects.get_or_create(slug='pufy', parent=None, defaults={
            'name_uk': 'Пуфи', 'name_ru': 'Пуфы', 'sort': 2,
        })
        attach(poufs.image, 'slots/cat-poufs.webp')
        poufs.save()
        subs = [
            ('modulni', 'Модульні', 'Модульные', 0),
            ('kutovi', 'Кутові', 'Угловые', 1),
            ('pryami', 'Прямі', 'Прямые', 2),
        ]
        children = {}
        for slug, uk, ru, sort in subs:
            obj, _ = Category.objects.get_or_create(slug=slug, parent=sofas, defaults={
                'name_uk': uk, 'name_ru': ru, 'sort': sort,
            })
            children[slug] = obj
        return {'sofas': sofas, 'beds': beds, 'poufs': poufs, **children}

    def _products(self, categories, fabrics):
        from catalog.models import Shade
        catalog = [
            {
                'slug': 'milan', 'name_uk': 'Мілан', 'name_ru': 'Милан',
                'type_uk': 'Модульний диван', 'type_ru': 'Модульный диван',
                'cat': 'modulni', 'price': 42900, 'badge': Product.Badge.NEW,
                'dims_uk': '320×95×82 см (модульна конфігурація)',
                'description_uk': 'Модульний диван «Мілан» дозволяє зібрати конфігурацію під форму вашої вітальні — від компактного двомісного варіанта до великого кутового ансамблю. Каркас із масиву бука, незалежний пружинний блок.',
                'care_uk': 'Знімні чохли, машинне прання за температури до 30°C. Рекомендовано хімчистку раз на рік.',
                'image': 'products/milan.png', 'slot': 'p1-a.webp',
            },
            {
                'slug': 'ontario', 'name_uk': 'Онтаріо', 'name_ru': 'Онтарио',
                'type_uk': 'Кутовий диван', 'type_ru': 'Угловой диван',
                'cat': 'kutovi', 'price': 38500, 'badge': Product.Badge.HIT,
                'dims_uk': '280×165×88 см',
                'description_uk': 'Кутовий диван «Онтаріо» поєднує глибоке сидіння та широкі підлокітники. Ідеальний для сімейного перегляду фільмів чи денного відпочинку.',
                'care_uk': 'Тканина стійка до стирання, знімні подушки, сухе чищення.',
                'image': 'products/ontario.png', 'slot': 'p2-a.webp',
            },
            {
                'slug': 'verona', 'name_uk': 'Верона', 'name_ru': 'Верона',
                'type_uk': 'Прямий диван', 'type_ru': 'Прямой диван',
                'cat': 'pryami', 'price': 27900, 'badge': '',
                'dims_uk': '210×90×80 см',
                'description_uk': 'Лаконічний прямий диван «Верона» для невеликих просторів. Дерев’яні ніжки, чіткі лінії, універсальний масштаб.',
                'care_uk': 'Знімний чохол, чищення мильним розчином.',
                'image': 'slots/p3-a.webp', 'slot': 'p3-a.webp',
            },
            {
                'slug': 'solo', 'name_uk': 'Соло', 'name_ru': 'Соло',
                'type_uk': 'Ліжко', 'type_ru': 'Кровать',
                'cat': 'beds', 'price': 24900, 'badge': Product.Badge.TOP,
                'dims_uk': '160×200 см, узголів’я 110 см',
                'description_uk': 'Ліжко «Соло» з м’яким тканинним узголів’ям і масивною основою з ламелями. Безшумний підйомний механізм для зберігання постільної білизни.',
                'care_uk': 'Узголів’я знімне, сухе чищення тканини раз на пів року.',
                'image': 'slots/p4-a.webp', 'slot': 'p4-a.webp',
            },
            {
                'slug': 'kyoto', 'name_uk': 'Кіото', 'name_ru': 'Киото',
                'type_uk': 'Пуф', 'type_ru': 'Пуф',
                'cat': 'poufs', 'price': 4200, 'badge': '',
                'dims_uk': '45×45×40 см',
                'description_uk': 'Компактний пуф «Кіото» — додаткове місце для сидіння або підставка для ніг. Легко переставляється по кімнаті.',
                'care_uk': 'Знімний чохол, машинне прання.',
                'image': 'slots/p5-a.webp', 'slot': 'p5-a.webp',
            },
            {
                'slug': 'loks', 'name_uk': 'Локс', 'name_ru': 'Локс',
                'type_uk': 'Кутовий модульний диван', 'type_ru': 'Угловой модульный диван',
                'cat': 'kutovi', 'price': 45000, 'badge': Product.Badge.NEW,
                'dims_uk': '340×180×85 см (модульна конфігурація)',
                'description_uk': 'Диван «Локс» — модульна кутова система з можливістю трансформації в спальне місце. Підходить для великих вітальнь.',
                'care_uk': 'Знімні чохли, машинне прання, регулярне збивання наповнювача подушок.',
                'image': 'slots/p6-a.webp', 'slot': 'p6-a.webp',
            },
        ]
        for item in catalog:
            product, created = Product.objects.get_or_create(slug=item['slug'], defaults={
                'name_uk': item['name_uk'], 'name_ru': item['name_ru'],
                'type_uk': item['type_uk'], 'type_ru': item['type_ru'],
                'category': categories[item['cat']],
                'base_price': item['price'],
                'badge': item['badge'],
                'dims_uk': item['dims_uk'],
                'description_uk': item['description_uk'],
                'care_uk': item['care_uk'],
                'sku': item['slug'].upper(),
            })
            attach(product.default_image, item['image'])
            product.save()
            for fabric in fabrics.values():
                ProductFabricPrice.objects.get_or_create(
                    product=product, fabric=fabric,
                    defaults={'price': product.base_price + fabric.surcharge, 'sku': f'{product.sku}-{fabric.slug[:3].upper()}'},
                )
            for shade in Shade.objects.filter(is_active=True):
                img, created = ProductShadeImage.objects.get_or_create(
                    product=product, shade=shade, sort=0,
                )
                if not img.image:
                    attach(img.image, f'slots/{item["slot"]}', dest_name=f'{product.slug}-{shade.slug}.webp')
                    img.save()
