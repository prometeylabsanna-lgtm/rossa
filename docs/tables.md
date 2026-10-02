# ROSSA — схема БД (Variant B-admin)

APPS_VARIANT = B-admin
FACET_STACK = C (без фасетів атрибутів; лише дерево категорій + sort + наявність)

Межа CMS ↔ DB:
- CMS: SiteSettings, HomePage, ValueProp, AboutPage, CollabPage, LegalPage
- DB catalog: Category, Characteristic, Fabric, Shade, Product, ProductFabricPrice, ProductColorOption, ProductColor, ProductCharacteristic
- DB leads: OrderRequest, PartnershipLead, ContactLead

## core

| Таблиця | Призначення |
|---|---|
| SiteSettings pk=1 | телефон, email, адреса, Telegram, логотип, години |
| HomePage pk=1 | секції, craft, about-band, SEO UA/RU |
| ValueProp | переваги головної (n, title, body, sort) |
| AboutPage pk=1 | історія, craft/logo/evolution JSON, milestones |
| CollabPage pk=1 | вступ, benefits JSON |
| LegalPage | slug: otrymannya / oferta / privacy |
| HeroSlide | слайди банера головної (image, alt, sort) |

## catalog

| Таблиця | Призначення |
|---|---|
| Category | дерево: Дивани → Модульні/Кутові/Прямі; Ліжка; Пуфи |
| Characteristic | типи характеристик (каркас, наповнення…) |
| Fabric | довідник тканин, surcharge |
| Shade | відтінок тканини, hex / swatch |
| Product | модель, категорія, бейдж, SEO, base_price |
| ProductFabricPrice | ціна моделі × тканина |
| ProductColorOption | стандартні кольори кружечків (беж/зелений/коричневий…) |
| ProductColor | колір товару + фото моделі цього кольору |
| ProductCharacteristic | значення характеристики на товарі (тип + UK/RU) |

## leads

| Таблиця | Призначення |
|---|---|
| OrderRequest | заявка «Замовити»: snapshot моделі/тканини/відтінку/ціни |
| PartnershipLead | джерело «Співпраця» |
| ContactLead | джерело «Контакти» |
