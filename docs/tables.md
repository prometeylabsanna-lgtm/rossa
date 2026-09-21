# ROSSA — схема БД (Variant B-admin)

APPS_VARIANT = B-admin
FACET_STACK = C (без фасетів атрибутів; лише дерево категорій + sort + наявність)

Межа CMS ↔ DB:
- CMS: SiteSettings, HomePage, ValueProp, AboutPage, CollabPage, LegalPage
- DB catalog: Category, Fabric, Shade, Product, ProductFabricPrice, ProductShadeImage
- DB leads: OrderRequest, PartnershipLead, ContactLead

## core

| Таблиця | Призначення |
|---|---|
| SiteSettings pk=1 | телефон, email, адреса, Telegram, логотип, години |
| HomePage pk=1 | hero, craft, CTA-тексти UA/RU, відео/постер |
| ValueProp | переваги головної (n, title, body, sort) |
| AboutPage pk=1 | історія, фото, milestones JSON, values JSON |
| CollabPage pk=1 | вступ, benefits JSON |
| LegalPage | slug: otrymannya / oferta / privacy |

## catalog

| Таблиця | Призначення |
|---|---|
| Category | дерево: Дивани → Модульні/Кутові/Прямі; Ліжка; Пуфи |
| Fabric | довідник тканин, surcharge |
| Shade | відтінок тканини, hex / swatch |
| Product | модель, категорія, бейдж, SEO, base_price |
| ProductFabricPrice | ціна моделі × тканина |
| ProductShadeImage | фото моделі на відтінок (+ gallery_order) |

## leads

| Таблиця | Призначення |
|---|---|
| OrderRequest | заявка «Замовити»: snapshot моделі/тканини/відтінку/ціни |
| PartnershipLead | джерело «Співпраця» |
| ContactLead | джерело «Контакти» |
