from django.core.management.base import BaseCommand

from catalog.models import Category, Fabric, Product, ProductFabricPrice, ProductShadeImage, Shade
from core.management.seed_legal_texts import LEGAL_PAGES
from core.management.seed_media import attach, replace_file
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
        fields = {
            'phone': '067 540 77 11',
            'phone_2': '073 076 77 55',
            'phone_3': '050 029 05 00',
            'email': 'rossamebli2016@gmail.com',
            'telegram_url': 'https://t.me/rossaukr',
            'telegram_handle': '@rossaukr',
            'instagram_url': 'https://www.instagram.com/rossa_mebel_ua',
            'facebook_url': 'https://www.facebook.com/share/19wDTQG2Vc/',
            'tiktok_url': 'https://www.tiktok.com/@rossa_ua',
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
        }
        obj, _ = SiteSettings.objects.get_or_create(pk=1, defaults=fields)
        for key, value in fields.items():
            setattr(obj, key, value)
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
        about_defaults = {
            'about_title_uk': 'Rossa. Твій стиль. Твій комфорт.',
            'about_title_ru': 'Rossa. Твой стиль. Твой комфорт.',
            'about_body_uk': (
                'Власне виробництво і матеріали, перевірені часом. '
                'Ми створюємо м’які меблі з увагою до форми, дотику та довговічності — '
                'щоб кожна модель гармонійно жила у вашому просторі.'
            ),
            'about_body_ru': (
                'Собственное производство и материалы, проверенные временем. '
                'Мы создаём мягкую мебель с вниманием к форме, тактильности и долговечности — '
                'чтобы каждая модель гармонично жила в вашем пространстве.'
            ),
        }
        updated = False
        for key, value in about_defaults.items():
            if getattr(obj, key, None) != value:
                setattr(obj, key, value)
                updated = True
        if not obj.about_video:
            replace_file(obj.about_video, 'home/video/about-showroom.mp4')
            updated = True
        if updated:
            obj.save()
        else:
            obj.save()
        self._hero_slides(obj)

    def _hero_slides(self, page):
        from core.models import HeroSlide

        slides = [
            {
                'sort': 0,
                'image': 'home/slide-1.webp',
                'title_uk': 'Меблі, створені для дому',
                'title_ru': 'Мебель, созданная для дома',
                'subtitle_uk': 'М’які дивани, ліжка та крісла з натуральних матеріалів. Індивідуальний пошив тканини й доставка по всій Україні — щоб ваш простір відчувався завершеним.',
                'subtitle_ru': 'Мягкие диваны, кровати и кресла из натуральных материалов. Индивидуальный пошив ткани и доставка по всей Украине — чтобы ваше пространство ощущалось завершённым.',
                'image_alt_uk': 'Білий модульний диван Rossa',
                'image_alt_ru': 'Белый модульный диван Rossa',
            },
            {
                'sort': 1,
                'image': 'home/slide-2.webp',
                'title_uk': 'Комфорт без компромісів',
                'title_ru': 'Комфорт без компромиссов',
                'subtitle_uk': 'Крісла та дивани для спокійних вечорів. Надійний каркас, пружні блоки й тканини, які приємно відчувати щодня — комфорт, розрахований на роки.',
                'subtitle_ru': 'Кресла и диваны для спокойных вечеров. Надёжный каркас, упругие блоки и ткани, которые приятно ощущать каждый день — комфорт, рассчитанный на годы.',
                'image_alt_uk': 'Зелений кутовий диван Rossa',
                'image_alt_ru': 'Зелёный угловой диван Rossa',
            },
            {
                'sort': 2,
                'image': 'home/slide-3.webp',
                'title_uk': 'Затишок\nу кожній деталі',
                'title_ru': 'Уют\nв каждой детали',
                'subtitle_uk': 'Текстури й матеріали, які хочеться відчувати. Відтінки, фактури та форми підбираємо так, щоб меблі гармонійно жили у вашому інтер’єрі.',
                'subtitle_ru': 'Текстуры и материалы, которые хочется ощущать. Оттенки, фактуры и формы подбираем так, чтобы мебель гармонично жила в вашем интерьере.',
                'image_alt_uk': 'Сірий диван Rossa',
                'image_alt_ru': 'Серый диван Rossa',
            },
        ]
        for item in slides:
            slide, created = HeroSlide.objects.get_or_create(
                page=page,
                sort=item['sort'],
                defaults={
                    'title_uk': item['title_uk'],
                    'title_ru': item['title_ru'],
                    'subtitle_uk': item['subtitle_uk'],
                    'subtitle_ru': item['subtitle_ru'],
                    'image_alt_uk': item['image_alt_uk'],
                    'image_alt_ru': item['image_alt_ru'],
                    'cta_uk': 'Дивитись каталог',
                    'cta_ru': 'Смотреть каталог',
                    'is_active': True,
                },
            )
            # Keep captions in sync for demo slides
            slide.title_uk = item['title_uk']
            slide.title_ru = item['title_ru']
            slide.subtitle_uk = item['subtitle_uk']
            slide.subtitle_ru = item['subtitle_ru']
            slide.image_alt_uk = item['image_alt_uk']
            slide.image_alt_ru = item['image_alt_ru']
            replace_file(slide.image, item['image'])
            slide.save()

    def _value_props(self):
        items = [
            (
                '01',
                'Каркас із сухої деревини',
                'Каркас из сухой древесины',
                'Екологічно чиста та безпечна основа виробу, що дбає про ваше здоров’я.',
                'Экологически чистая и безопасная основа изделия, заботящаяся о вашем здоровье.',
            ),
            (
                '02',
                'Надійність та довговічність',
                'Надёжность и долговечность',
                'Поєднання високоякісних матеріалів і передових технологій робить вироби Rossa втіленням надійності та довговічності.',
                'Сочетание высококачественных материалов и передовых технологий делает изделия Rossa воплощением надёжности и долговечности.',
            ),
            (
                '03',
                'Великий вибір тканин',
                'Большой выбор тканей',
                'Широка гама фактур та кольорів дозволить створити меблі, які ідеально доповнять ваш простір.',
                'Широкая гамма фактур и цветов позволит создать мебель, которая идеально дополнит ваше пространство.',
            ),
            (
                '04',
                'Індивідуальний підхід до кожного клієнта',
                'Индивидуальный подход к каждому клиенту',
                'Ми цінуємо ваші ідеї та втілюємо їх із максимальною увагою до деталей і найвищою якістю.',
                'Мы ценим ваши идеи и воплощаем их с максимальным вниманием к деталям и высочайшим качеством.',
            ),
        ]
        for i, (num, tu, tr, bu, br) in enumerate(items):
            obj, _ = ValueProp.objects.get_or_create(number=num, defaults={
                'title_uk': tu, 'title_ru': tr, 'body_uk': bu, 'body_ru': br, 'sort': i,
            })
            changed = False
            for field, value in (
                ('title_uk', tu), ('title_ru', tr),
                ('body_uk', bu), ('body_ru', br), ('sort', i),
            ):
                if getattr(obj, field) != value:
                    setattr(obj, field, value)
                    changed = True
            if changed:
                obj.save(update_fields=['title_uk', 'title_ru', 'body_uk', 'body_ru', 'sort'])

    def _about(self):
        body_uk = (
            'Усе почалося не з бізнес-плану, а з дуже особистого бажання — знайти той самий диван. '
            'Такий, на який повертаєшся після найважчого дня, скидаєш усе зайве, занурюєшся у м’які обійми тканини '
            'й нарешті видихаєш: «Я вдома».\n\n'
            'Ми обходили десятки меблевих салонів, роздивлялися сотні моделей, але постійно стикалися з розчаруванням. '
            'Одні дивани були жорсткими й незручними, інші — розчаровували посередньою якістю матеріалів, '
            'а за справді комфортні та красиві екземпляри просили якісь захмарні гроші. '
            'Ми зрозуміли: знайти справді м’який, якісний, функціональний і при цьому доступний диван — це справжній квест.\n\n'
            'І тоді ми вирішили створити його самі.\n\n'
            'Так народилася фабрика Rossa. Ми поставили собі чітку мету: довести, що функціональність, '
            'преміальний затишок, анатомічна м’якість та бездоганна якість можуть бути доступними для кожного.\n\n'
            'За два десятиліття ми пройшли шлях від локального виробництва до сучасної меблевої фабрики. '
            'Наш секрет простий: ми ніколи не зупиняємося на досягнутому та постійно розвиваємося разом із нашими клієнтами.'
        )
        body_ru = (
            'Всё началось не с бизнес-плана, а с очень личного желания — найти тот самый диван. '
            'Такой, на который возвращаешься после самого тяжёлого дня, сбрасываешь всё лишнее, '
            'погружаешься в мягкие объятия ткани и наконец выдыхаешь: «Я дома».\n\n'
            'Мы обходили десятки мебельных салонов, рассматривали сотни моделей, но постоянно сталкивались с разочарованием. '
            'Одни диваны были жёсткими и неудобными, другие — разочаровывали посредственным качеством материалов, '
            'а за по-настоящему комфортные и красивые экземпляры просили какие-то заоблачные деньги. '
            'Мы поняли: найти по-настоящему мягкий, качественный, функциональный и при этом доступный диван — настоящий квест.\n\n'
            'И тогда мы решили создать его сами.\n\n'
            'Так родилась фабрика Rossa. Мы поставили себе чёткую цель: доказать, что функциональность, '
            'премиальный уют, анатомическая мягкость и безупречное качество могут быть доступны каждому.\n\n'
            'За два десятилетия мы прошли путь от локального производства до современной мебельной фабрики. '
            'Наш секрет прост: мы никогда не останавливаемся на достигнутом и постоянно развиваемся вместе с нашими клиентами.'
        )
        fields = {
            'title_uk': 'Про ROSSA',
            'title_ru': 'О ROSSA',
            'subtitle_uk': 'Все почалося з пошуку власного дому.',
            'subtitle_ru': 'Всё началось с поиска собственного дома.',
            'body_uk': body_uk,
            'body_ru': body_ru,
            'milestones_title_uk': 'Ключові віхи нашої історії',
            'milestones_title_ru': 'Ключевые вехи нашей истории',
            'milestones': [
                {
                    'year': '2005',
                    'body_uk': (
                        'Заснування. Виробництво першого функціонального та якісного дивану для себе. '
                        'Запуск виробництва, формування базових стандартів якості та команди майстрів, '
                        'закоханих у свою справу.'
                    ),
                    'body_ru': (
                        'Основание. Производство первого функционального и качественного дивана для себя. '
                        'Запуск производства, формирование базовых стандартов качества и команды мастеров, '
                        'влюблённых в своё дело.'
                    ),
                },
                {
                    'year': '2016',
                    'body_uk': (
                        'Перший ребрендинг. Знаковий етап масштабного оновлення. Ми модернізували виробничі потужності, '
                        'розширили асортимент (включивши лінійки корпусних та м’яких меблів) і переглянули підхід до дизайну, '
                        'зробивши акцент на актуальних європейських трендах та функціональності.'
                    ),
                    'body_ru': (
                        'Первый ребрендинг. Знаковый этап масштабного обновления. Мы модернизировали производственные мощности, '
                        'расширили ассортимент (включив линейки корпусной и мягкой мебели) и пересмотрели подход к дизайну, '
                        'сделав акцент на актуальных европейских трендах и функциональности.'
                    ),
                },
                {
                    'year': '2025',
                    'body_uk': (
                        'Другий ребрендинг. Новий крок у майбутнє. Ми повністю переосмислили візуальну концепцію та сервіс, '
                        'впровадили ще вищі стандарти екологічності, ергономіки й індивідуального підходу до кожного проєкту.'
                    ),
                    'body_ru': (
                        'Второй ребрендинг. Новый шаг в будущее. Мы полностью переосмыслили визуальную концепцию и сервис, '
                        'внедрили ещё более высокие стандарты экологичности, эргономики и индивидуального подхода к каждому проекту.'
                    ),
                },
            ],
            'values': [],
            'evolution_title_uk': 'Еволюція наших диванів',
            'evolution_title_ru': 'Эволюция наших диванов',
            'logo_title_uk': 'Еволюція логотипу',
            'logo_title_ru': 'Эволюция логотипа',
            'seo_title_uk': 'Про нас — ROSSA',
            'seo_title_ru': 'О нас — ROSSA',
            'seo_description_uk': 'Історія фабрики Rossa: від особистого пошуку дому до сучасної меблевої фабрики.',
            'seo_description_ru': 'История фабрики Rossa: от личного поиска дома до современной мебельной фабрики.',
        }
        obj, _ = AboutPage.objects.get_or_create(pk=1, defaults=fields)
        for key, value in fields.items():
            setattr(obj, key, value)
        replace_file(obj.hero_image, 'slots/about-hero.webp')

        from django.core.files import File
        from django.core.files.storage import default_storage
        from pathlib import Path

        slots_dir = Path(__file__).resolve().parents[2] / 'static' / 'images' / 'slots'

        mapping = [
            ('about-fabric.webp', 'Пошив тканини', 'Пошив ткани'),
            ('about-frame.webp', 'Ручна оббивка', 'Ручная обивка'),
            ('about-assembly.webp', 'Збірка на виробництві', 'Сборка на производстве'),
        ]
        items = []
        for filename, lu, lr in mapping:
            src = slots_dir / filename
            dest = f'about/{filename}'
            if src.exists():
                if default_storage.exists(dest):
                    default_storage.delete(dest)
                with src.open('rb') as fh:
                    dest = default_storage.save(dest, File(fh))
                items.append({'image': f'/media/{dest}', 'label_uk': lu, 'label_ru': lr})
        obj.craft_images = items

        logos = []
        for year, filename, lu, lr in (
            ('2005', 'about-logo-2005.webp', 'Логотип 2005', 'Логотип 2005'),
            ('2016', 'about-logo-2016.webp', 'Логотип 2016', 'Логотип 2016'),
            ('2025', 'about-logo-2025.webp', 'Логотип 2025', 'Логотип 2025'),
        ):
            src = slots_dir / filename
            dest = f'about/logos/{filename}'
            if not src.exists():
                continue
            if default_storage.exists(dest):
                default_storage.delete(dest)
            with src.open('rb') as fh:
                dest = default_storage.save(dest, File(fh))
            logos.append({
                'image': f'/media/{dest}',
                'year': year,
                'label_uk': lu,
                'label_ru': lr,
            })
        obj.logo_images = logos

        evolution = []
        for n in range(1, 19):
            filename = f'about-evolution-{n:02d}.webp'
            src = slots_dir / filename
            dest = f'about/evolution/{filename}'
            if not src.exists():
                continue
            if default_storage.exists(dest):
                default_storage.delete(dest)
            with src.open('rb') as fh:
                dest = default_storage.save(dest, File(fh))
            evolution.append({'image': f'/media/{dest}'})
        obj.evolution_images = evolution
        obj.save()

    def _collab(self):
        benefits = [
            {
                'icon': 'years',
                'title_uk': 'Більше 20 років на ринку',
                'title_ru': 'Более 20 лет на рынке',
            },
            {
                'icon': 'production',
                'title_uk': 'Власне виробництво',
                'title_ru': 'Собственное производство',
            },
            {
                'icon': 'guarantee',
                'title_uk': 'Гарантія на вироби',
                'title_ru': 'Гарантия на изделия',
            },
            {
                'icon': 'collections',
                'title_uk': 'Постійне оновлення колекцій',
                'title_ru': 'Постоянное обновление коллекций',
            },
            {
                'icon': 'design',
                'title_uk': 'Оригінальний дизайн',
                'title_ru': 'Оригинальный дизайн',
            },
        ]
        fields = {
            'title_uk': 'Співпраця з ROSSA',
            'title_ru': 'Сотрудничество с ROSSA',
            'sub_uk': '',
            'sub_ru': '',
            'form_title_uk': 'Форма заявки',
            'form_title_ru': 'Форма заявки',
            'advantages_title_uk': 'Наші переваги',
            'advantages_title_ru': 'Наши преимущества',
            'benefits': benefits,
            'dealer_support_title_uk': 'Підтримка нашого дилера:',
            'dealer_support_title_ru': 'Поддержка нашего дилера:',
            'dealer_support': [
                {
                    'title_uk': 'постійна комунікація',
                    'title_ru': 'постоянная коммуникация',
                    'body_uk': 'Постійний зв’язок та всебічна підтримка: оперативно інформуємо про новини фабрики.',
                    'body_ru': 'Постоянная связь и всесторонняя поддержка: оперативно информируем о новостях фабрики.',
                },
                {
                    'title_uk': 'маркетингова підтримка',
                    'title_ru': 'маркетинговая поддержка',
                    'body_uk': 'Цифрові та промоматеріали у вільному доступі.',
                    'body_ru': 'Цифровые и промоматериалы в свободном доступе.',
                },
                {
                    'title_uk': 'навчання',
                    'title_ru': 'обучение',
                    'body_uk': 'Проводимо навчання менеджерів-консультантів, продавців в онлайн-режимі та надаємо індивідуальний супровід у перші місяці роботи.',
                    'body_ru': 'Проводим обучение менеджеров-консультантов, продавцов в онлайн-режиме и предоставляем индивидуальное сопровождение в первые месяцы работы.',
                },
            ],
            'seo_title_uk': 'Співпраця — ROSSA',
            'seo_title_ru': 'Сотрудничество — ROSSA',
            'seo_description_uk': 'Оптові умови для дилерів, салонів і дизайнерів.',
            'seo_description_ru': 'Оптовые условия для дилеров, салонов и дизайнеров.',
        }
        obj, _ = CollabPage.objects.get_or_create(pk=1, defaults=fields)
        for key, value in fields.items():
            setattr(obj, key, value)
        replace_file(obj.hero_image, 'slots/collab-hero.webp')
        replace_file(obj.form_image, 'slots/collab-form.webp')
        obj.save()

    def _legal(self):
        for slug, title_uk, title_ru, body_uk, body_ru in LEGAL_PAGES:
            LegalPage.objects.update_or_create(
                slug=slug,
                defaults={
                    'title_uk': title_uk,
                    'title_ru': title_ru,
                    'body_uk': body_uk,
                    'body_ru': body_ru,
                    'is_active': True,
                },
            )

    def _fabrics(self):
        # Категорії тканини 1–7 (без назв матеріалів)
        data = [
            (f'cat-{n}', str(n), str(n), 0, n - 1)
            for n in range(1, 8)
        ]
        keep_slugs = {slug for slug, *_ in data}
        Fabric.objects.exclude(slug__in=keep_slugs).delete()

        out = {}
        for slug, uk, ru, surcharge, sort in data:
            obj, _ = Fabric.objects.get_or_create(slug=slug, defaults={
                'name_uk': uk, 'name_ru': ru, 'surcharge': surcharge, 'sort': sort,
            })
            obj.name_uk = uk
            obj.name_ru = ru
            obj.surcharge = surcharge
            obj.sort = sort
            obj.is_active = True
            obj.save()
            out[slug] = obj

        # По кілька відтінків на категорію (палітра для демо)
        palette = [
            ('chocolate', 'Шоколад', 'Шоколад', '#3C2415'),
            ('beige', 'Беж', 'Беж', '#D4C4A8'),
            ('wine', 'Вино', 'Вино', '#903838'),
            ('ivory', 'Айворі', 'Айвори', '#C9BFA5'),
            ('stone', 'Камінь', 'Камень', '#7C7267'),
            ('forest', 'Ліс', 'Лес', '#4A5A52'),
            ('cream', 'Крем', 'Крем', '#D8CFC0'),
            ('graphite', 'Графіт', 'Графит', '#3E4B5C'),
            ('black', 'Чорний', 'Чёрный', '#1A1817'),
            ('moss', 'Мох', 'Мох', '#6B7B4A'),
            ('clay', 'Глина', 'Глина', '#A67C52'),
            ('sky', 'Небо', 'Небо', '#8FA4B8'),
            ('blush', 'Пудра', 'Пудра', '#C9A9A6'),
            ('ink', 'Чорнило', 'Чернила', '#2C3340'),
        ]
        for idx, (slug, fabric) in enumerate(out.items()):
            # 2 відтінки на категорію, з циклічної палітри
            for j in range(2):
                color = palette[(idx * 2 + j) % len(palette)]
                shade_slug, name_uk, name_ru, hex_color = color
                shade, _ = Shade.objects.get_or_create(
                    fabric=fabric,
                    slug=f'{shade_slug}-{j + 1}',
                    defaults={
                        'name_uk': name_uk,
                        'name_ru': name_ru,
                        'hex_color': hex_color,
                        'sort': j,
                    },
                )
                shade.name_uk = name_uk
                shade.name_ru = name_ru
                shade.hex_color = hex_color
                shade.sort = j
                shade.is_active = True
                shade.save()
            # Прибрати зайві відтінки цієї категорії
            Shade.objects.filter(fabric=fabric).exclude(
                slug__in=[f'{palette[(idx * 2 + j) % len(palette)][0]}-{j + 1}' for j in range(2)]
            ).delete()
        return out

    def _categories(self):
        sofas, _ = Category.objects.get_or_create(slug='divany', parent=None, defaults={
            'name_uk': 'Дивани', 'name_ru': 'Диваны', 'sort': 0,
            'intro_uk': 'Модульні, кутові та прямі дивани власного виробництва з можливістю вибору тканини.',
            'intro_ru': 'Модульные, угловые и прямые диваны собственного производства с возможностью выбора ткани.',
        })
        replace_file(sofas.image, 'slots/cat-sofas.webp')
        sofas.save()
        beds, _ = Category.objects.get_or_create(slug='lizhka', parent=None, defaults={
            'name_uk': 'Ліжка', 'name_ru': 'Кровати', 'sort': 1,
            'intro_uk': 'Ліжка з м’яким узголів’ям і надійним каркасом власного виробництва.',
            'intro_ru': 'Кровати с мягким изголовьем и надёжным каркасом собственного производства.',
        })
        beds.name_uk = 'Ліжка'
        beds.name_ru = 'Кровати'
        beds.intro_uk = beds.intro_uk or 'Ліжка з м’яким узголів’ям і надійним каркасом власного виробництва.'
        beds.intro_ru = 'Кровати с мягким изголовьем и надёжным каркасом собственного производства.'
        replace_file(beds.image, 'slots/cat-beds.webp')
        beds.save()
        poufs, _ = Category.objects.get_or_create(slug='pufy', parent=None, defaults={
            'name_uk': 'Пуфи', 'name_ru': 'Пуфы', 'sort': 2,
            'intro_uk': 'Пуфи як доповнення до диванів і окреме м’яке місце для сидіння.',
            'intro_ru': 'Пуфы как дополнение к диванам и отдельное мягкое место для сидения.',
        })
        poufs.name_uk = 'Пуфи'
        poufs.name_ru = 'Пуфы'
        poufs.intro_uk = poufs.intro_uk or 'Пуфи як доповнення до диванів і окреме м’яке місце для сидіння.'
        poufs.intro_ru = 'Пуфы как дополнение к диванам и отдельное мягкое место для сидения.'
        replace_file(poufs.image, 'slots/cat-poufs.webp')
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
                'dims_ru': '320×95×82 см (модульная конфигурация)',
                'description_uk': 'Модульний диван «Мілан» дозволяє зібрати конфігурацію під форму вашої вітальні — від компактного двомісного варіанта до великого кутового ансамблю. Каркас із масиву бука, незалежний пружинний блок.',
                'description_ru': 'Модульный диван «Милан» позволяет собрать конфигурацию под форму вашей гостиной — от компактного двухместного варианта до большого углового ансамбля. Каркас из массива бука, независимый пружинный блок.',
                'care_uk': 'Знімні чохли, машинне прання за температури до 30°C. Рекомендовано хімчистку раз на рік.',
                'care_ru': 'Съёмные чехлы, машинная стирка при температуре до 30°C. Рекомендуется химчистка раз в год.',
                'image': 'products/milan.webp', 'slot': 'p1-a.webp',
                'color_model': 'beige',
            },
            {
                'slug': 'ontario', 'name_uk': 'Онтаріо', 'name_ru': 'Онтарио',
                'type_uk': 'Кутовий диван', 'type_ru': 'Угловой диван',
                'cat': 'kutovi', 'price': 38500, 'badge': Product.Badge.HIT,
                'dims_uk': '280×165×88 см',
                'dims_ru': '280×165×88 см',
                'description_uk': 'Кутовий диван «Онтаріо» поєднує глибоке сидіння та широкі підлокітники. Ідеальний для сімейного перегляду фільмів чи денного відпочинку.',
                'description_ru': 'Угловой диван «Онтарио» сочетает глубокое сиденье и широкие подлокотники. Идеален для семейного просмотра фильмов или дневного отдыха.',
                'care_uk': 'Тканина стійка до стирання, знімні подушки, сухе чищення.',
                'care_ru': 'Ткань устойчива к истиранию, съёмные подушки, сухая чистка.',
                'image': 'products/ontario.webp', 'slot': 'p2-a.webp',
                'color_model': 'green',
            },
            {
                'slug': 'verona', 'name_uk': 'Верона', 'name_ru': 'Верона',
                'type_uk': 'Прямий диван', 'type_ru': 'Прямой диван',
                'cat': 'pryami', 'price': 27900, 'badge': '',
                'dims_uk': '210×90×80 см',
                'dims_ru': '210×90×80 см',
                'description_uk': 'Лаконічний прямий диван «Верона» для невеликих просторів. Дерев’яні ніжки, чіткі лінії, універсальний масштаб.',
                'description_ru': 'Лаконичный прямой диван «Верона» для небольших пространств. Деревянные ножки, чёткие линии, универсальный масштаб.',
                'care_uk': 'Знімний чохол, чищення мильним розчином.',
                'care_ru': 'Съёмный чехол, чистка мыльным раствором.',
                'image': 'products/ontario.webp', 'slot': 'p3-a.webp',
                'color_model': 'green',
            },
            {
                'slug': 'solo', 'name_uk': 'Соло', 'name_ru': 'Соло',
                'type_uk': 'Ліжко', 'type_ru': 'Кровать',
                'cat': 'beds', 'price': 24900, 'badge': Product.Badge.TOP,
                'dims_uk': '160×200 см, узголів’я 110 см',
                'dims_ru': '160×200 см, изголовье 110 см',
                'description_uk': 'Ліжко «Соло» з м’яким тканинним узголів’ям і масивною основою з ламелями. Безшумний підйомний механізм для зберігання постільної білизни.',
                'description_ru': 'Кровать «Соло» с мягким тканевым изголовьем и массивной основой с ламелями. Бесшумный подъёмный механизм для хранения постельного белья.',
                'care_uk': 'Узголів’я знімне, сухе чищення тканини раз на пів року.',
                'care_ru': 'Изголовье съёмное, сухая чистка ткани раз в полгода.',
                'image': 'slots/p4-a.webp', 'slot': 'p4-a.webp',
            },
            {
                'slug': 'kyoto', 'name_uk': 'Кіото', 'name_ru': 'Киото',
                'type_uk': 'Пуф', 'type_ru': 'Пуф',
                'cat': 'poufs', 'price': 4200, 'badge': '',
                'dims_uk': '45×45×40 см',
                'dims_ru': '45×45×40 см',
                'description_uk': 'Компактний пуф «Кіото» — додаткове місце для сидіння або підставка для ніг. Легко переставляється по кімнаті.',
                'description_ru': 'Компактный пуф «Киото» — дополнительное место для сидения или подставка для ног. Легко переставляется по комнате.',
                'care_uk': 'Знімний чохол, машинне прання.',
                'care_ru': 'Съёмный чехол, машинная стирка.',
                'image': 'slots/p5-a.webp', 'slot': 'p5-a.webp',
            },
            {
                'slug': 'loks', 'name_uk': 'Локс', 'name_ru': 'Локс',
                'type_uk': 'Кутовий модульний диван', 'type_ru': 'Угловой модульный диван',
                'cat': 'kutovi', 'price': 45000, 'badge': Product.Badge.NEW,
                'dims_uk': '340×180×85 см (модульна конфігурація)',
                'dims_ru': '340×180×85 см (модульная конфигурация)',
                'description_uk': 'Диван «Локс» — модульна кутова система з можливістю трансформації в спальне місце. Підходить для великих вітальнь.',
                'description_ru': 'Диван «Локс» — модульная угловая система с возможностью трансформации в спальное место. Подходит для больших гостиных.',
                'care_uk': 'Знімні чохли, машинне прання, регулярне збивання наповнювача подушок.',
                'care_ru': 'Съёмные чехлы, машинная стирка, регулярное взбивание наполнителя подушек.',
                'image': 'products/milan.webp', 'slot': 'p6-a.webp',
                'color_model': 'beige',
            },
        ]
        # Дві моделі диванів × 2 кольори (бежевий/темно-коричневий і зелений/бежевий)
        color_models = {
            'beige': {
                'primary': 'products/milan.webp',
                'map': {
                    'beige-2': {'image': 'products/milan.webp', 'hex': '', 'sort': 0},
                    'chocolate-1': {'image': 'products/milan-dark-brown.webp', 'hex': '', 'sort': 1},
                },
            },
            'green': {
                'primary': 'products/ontario.webp',
                'map': {
                    'chocolate-1': {'image': 'products/ontario.webp', 'hex': '#7A8B6E', 'sort': 0},
                    'beige-2': {'image': 'products/ontario-beige.webp', 'hex': '', 'sort': 1},
                },
            },
        }
        for item in catalog:
            product, created = Product.objects.get_or_create(slug=item['slug'], defaults={
                'name_uk': item['name_uk'], 'name_ru': item['name_ru'],
                'type_uk': item['type_uk'], 'type_ru': item['type_ru'],
                'category': categories[item['cat']],
                'base_price': item['price'],
                'badge': item['badge'],
                'dims_uk': item['dims_uk'],
                'dims_ru': item['dims_ru'],
                'description_uk': item['description_uk'],
                'description_ru': item['description_ru'],
                'care_uk': item['care_uk'],
                'care_ru': item['care_ru'],
                'sku': item['slug'].upper(),
            })
            product.name_uk = item['name_uk']
            product.name_ru = item['name_ru']
            product.type_uk = item['type_uk']
            product.type_ru = item['type_ru']
            product.category = categories[item['cat']]
            product.base_price = item['price']
            product.badge = item['badge']
            product.dims_uk = item['dims_uk']
            product.dims_ru = item['dims_ru']
            product.description_uk = item['description_uk']
            product.description_ru = item['description_ru']
            product.care_uk = item['care_uk']
            product.care_ru = item['care_ru']
            specs = item.get('specs') or {
                'spec_frame_uk': 'Брус хвойних порід, ДСП класу E1 та пружинна змійка',
                'spec_frame_ru': 'Брус хвойных пород, ДСП класса E1 и пружинная змейка',
                'spec_filling_uk': 'Пінополіуретан',
                'spec_filling_ru': 'Пенополиуретан',
                'spec_mechanism_uk': 'Відсутній',
                'spec_mechanism_ru': 'Отсутствует',
                'spec_textile_uk': 'На вибір покупця з асортименту понад 1000 видів текстилю',
                'spec_textile_ru': 'На выбор покупателя из ассортимента более 1000 видов текстиля',
                'spec_storage_uk': 'Відсутні',
                'spec_storage_ru': 'Отсутствуют',
            }
            for field, value in specs.items():
                setattr(product, field, value)
            if item.get('color_model'):
                replace_file(product.default_image, item['image'])
            else:
                attach(product.default_image, item['image'])
            product.save()
            # Приблизні ціни по категоріях тканини 1–7 (CMS: ProductFabricPrice)
            approx_extra = {
                'cat-1': 0,
                'cat-2': 2500,
                'cat-3': 4800,
                'cat-4': 7200,
                'cat-5': 10500,
                'cat-6': 14200,
                'cat-7': 18500,
            }
            for slug, fabric in fabrics.items():
                price = product.base_price + approx_extra.get(slug, 0)
                fp, _ = ProductFabricPrice.objects.get_or_create(
                    product=product,
                    fabric=fabric,
                    defaults={
                        'price': price,
                        'sku': f'{product.sku}-{fabric.slug[-1].upper()}',
                    },
                )
                fp.price = price
                fp.sku = f'{product.sku}-{fabric.slug[-1].upper()}'
                fp.save(update_fields=['price', 'sku'])
            color = color_models.get(item.get('color_model'))
            for shade in Shade.objects.filter(is_active=True):
                variant = color['map'].get(shade.slug) if color else None
                img = ProductShadeImage.objects.filter(product=product, shade=shade).order_by('sort', 'id').first()
                if not img:
                    img = ProductShadeImage(product=product, shade=shade, sort=0)
                if variant:
                    img.sort = variant['sort']
                    img.hex_override = variant['hex']
                    replace_file(
                        img.image,
                        variant['image'],
                        dest_name=f'{product.slug}-{shade.slug}.webp',
                    )
                else:
                    img.hex_override = ''
                    if not img.image:
                        attach(
                            img.image,
                            f'slots/{item["slot"]}',
                            dest_name=f'{product.slug}-{shade.slug}.webp',
                        )
                    elif color:
                        # інші категорії тканини — те саме основне фото моделі
                        replace_file(
                            img.image,
                            color['primary'],
                            dest_name=f'{product.slug}-{shade.slug}.webp',
                        )
                img.save()
