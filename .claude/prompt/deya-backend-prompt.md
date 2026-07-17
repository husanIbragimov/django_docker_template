# PROMPT — Deya sayti backend (mavjud Django template ustida)

## Kontekst

Deya konditer fabrikasi (deya.uz) korporativ sayti uchun backend yoz.
Sayt kontentli korporativ sayt — **e-commerce emas**: narx, savat, buyurtma yo'q.
Foydalanuvchi mahsulotni ko'radi va **lead** (ariza) qoldiradi. Tillar: RU (default) + EN.

Ish **mavjud template repozitoriyda** boradi. Boshlashdan oldin `CLAUDE.md` ni o'qi va
uning konvensiyalarini buzma. Yangi infra (docker, JWT, logger, celery, swagger) yaratma —
hammasi tayyor, faqat foydalan.

## Template konvensiyalari (majburiy)

- Kod `src/` ostida, yangi applar → `src/apps/<name>/`.
- Har bir yangi app `LOCAL_APPS` ga (`config/settings/apps.py`) qo'shiladi; `migrations/{dev,prod}/`
  avtomatik yaratiladi — migration'ni to'g'ri `PRODUCTION` qiymati bilan generatsiya qil.
- Barcha domen modellari `apps.common.models.BaseModel` dan meros (audit maydonlari uchun).
- View'lar `apps.common.base_api.BaseGenericAPI` ustida — `serializer.is_valid()` chaqirma,
  `self.validate_data` dan foydalan.
- Xatolik → `apps.common.response.ExceptionResponse` + `ResponseCode` enum'iga yangi a'zolar qo'sh.
- Foydalanuvchiga ko'rinadigan matnlar (`verbose_name`, xato matnlari) →
  `apps/common/locale/local_language.py::TranslatableText` enum + `_(T.xxx)`. Inline `gettext_lazy` yozma.
- URL'lar `apps/v1.py` ga namespace bilan qo'shiladi (`config/urls.py` ga tegma).
- Schema/docs uchun `apps/common/schema/` helperlaridan foydalan, ad-hoc `extend_schema` yozma.
- App ichida: bitta narsadan ko'p bo'lsa `models/`, `serializers/`, `views/`, `urls/` — package;
  sodda app'da flat fayl (`upload` app'i kabi). Bir app ichida ikkalasini aralashtirma.
- Fayl/rasm yuklash uchun avval `apps/upload` ni ko'r — mavjud mexanizmni takrorlama.
- Lint: black/flake8/isort/mypy, line length 120.
- Test: `python src/manage.py test --parallel --exclude-tag=dev-mode` (pre-commit hook, o'tishi shart).

## Yangi qo'shiladigan narsa

- `django-modeltranslation` → `requirements/base.txt` + `config/settings/apps.py` + `locale.py`.
  Kontent maydonlari (title, description, ...) shu bilan tarjima qilinadi; `Accept-Language` header
  orqali til tanlanadi. (`TranslatableText` — statik label'lar uchun, modeltranslation — DB kontenti uchun.
  Ikkisi turli maqsad, ikkalasi ham kerak.)

## Kod sifati

- KISS: ortiqcha abstraksiya yo'q. Repository pattern kerak emas — Django ORM manager yetarli.
- SOLID: biznes-logika `services.py`, o'qish query'lari `selectors.py`, view faqat orkestratsiya.
- Type hints majburiy, funksiya 20 qatordan oshmasin.
- Har bir list selector'da `select_related`/`prefetch_related` (N+1 yo'q).

---

## Modellar

Yangi applar: `catalog`, `blog`, `about`, `careers`, `partners`, `pages`, `leads`.
`(tr)` = modeltranslation bilan tarjima qilinadigan maydon. Barchasi `BaseModel` dan meros.
Umumiy maydonlar: `sort_order` (PositiveSmallIntegerField, db_index), `is_active` (bool, db_index).

### catalog

**Category** — Круассаны / Вафли / Конфеты / Конфеты вафельные / Печенье
`name` (tr), `slug` unique, `image`, `sort_order`, `is_active`

**Flavor** — Шоколад, Персик, Малина, Варёная сгущёнка, Ванильно-клубничный, Ванильно-пломбирный
`name` (tr), `slug` unique, `sort_order`

**Weight** — 42 г, 252 г
`value` (Decimal), `unit` (choices: g/kg), `unique_together(value, unit)`

**ProductFamily** — mahsulot liniyasi (Ketler, Taggis, Apachi, Quadro)
`name`, `slug` unique

**Product**
- `category` FK(PROTECT, related_name="products"), `family` FK(SET_NULL, null), `flavor` FK(SET_NULL, null)
- `name` (tr), `slug` unique db_index, `description` (tr)
- `code` unique ("B-083"), `box_weight` Decimal(kg), `shelf_life_months` PositiveSmallInteger
- `weights` M2M(Weight)
- `badge` choices: `""` / `new` (НОВИНКА) / `bestseller` (ХИТ ПРОДАЖ)
- `is_featured` (bosh sahifadagi 4 ta blok)
- `related_products` M2M(self, symmetrical=False, blank) — "Мы также рекомендуем";
  bo'sh bo'lsa selector kategoriya bo'yicha fallback qiladi
- Index: `(category, is_active, sort_order)`, `(badge,)`, `(is_featured,)`

**ProductImage** — `product` FK(CASCADE, related_name="images"), `image`, `alt` (tr), `is_main`, `sort_order`

> Muhim: katalogda har bir vkus — **alohida Product** (dizaynda "Ketler с шоколадной начинкой" va
> "Ketler с малиновой начинкой" alohida kartochka). Variant jadval yaratma:
> kartochkadagi "ВКУС" tag'lari = `Product.objects.filter(family=..., is_active=True)`.

### blog

**Post** — `title` (tr), `slug` unique, `excerpt` (tr), `cover`, `published_at` (db_index), `is_published`
Index: `(is_published, -published_at)`

**PostBlock** — `post` FK(CASCADE, related_name="blocks"), `type` (heading/text/image), `text` (tr, blank), `image` (blank), `sort_order`

### about

**HomeSlide** — hero slayder (2 slayd): `title` (tr), `subtitle` (tr), `image`, `cta_label` (tr), `cta_url`
**Stat** — 32+ / 25 / 60 / 90: `value` (CharField "32+"), `label` (tr)
**TimelineEvent** — 1994…2026: `year` unique, `title` (tr), `description` (tr), `image`
**ExportRegion** — Центральная Азия, Закавказье, Восточная Азия, Америка, Ближний Восток, Южная Азия:
`name` (tr), `position_x`/`position_y` (Decimal — SVG koordinatasi)

### careers

**Company** — Iruskon, Bonu Shirinliklar, Вкусная булка, Sami by Deya:
`name`, `slug` unique, `description` (tr), `image`, `vacancies_url`
**CareerValue** — 4 ta blok: `title` (tr), `text` (tr), `image` (blank)

### partners

**Partner** — `name`, `logo`, `website` (blank)
**Certificate** — `title` (tr), `image`, `file` (PDF, blank)

### pages

**StaticPage** — privacy-policy, consent: `slug` unique, `title` (tr), `body` (tr)
**SiteSettings** (singleton, pk=1) — `phone`, `hotline`, `email`, `address` (tr), `work_hours` (tr),
`yandex_map_url`, `instagram_url`, `telegram_url`, `catalog_file` (PDF), `cookie_notice_text` (tr)

### leads

**Lead** — uchala forma (partner / "Связаться с отделом продаж" / kontakt) bitta jadvalda:
- `type` choices: `partner`/`sales`/`contact` (db_index)
- `name`, `email`, `phone`, `message` (blank)
- `product` FK(SET_NULL, null, blank) — sales formasi tovar kartochkasidan kelsa
- `consent_personal_data` (bool, serializer'da True bo'lishi validatsiya qilinadi)
- `consent_marketing` (bool, default False)
- `status` choices: `new`/`in_progress`/`done` (db_index)
- `source_url`, `ip_address`, `user_agent`
- Index: `(type, status, -created_at)`

**NewsletterSubscription** — `email` unique, `is_active`, `unsubscribe_token` (UUID)

---

## API

`apps/v1.py` ga namespace bilan ulanadi (`/api/v1/...`). Til — `Accept-Language: ru|en`.

### Public (AllowAny, read-only)

| Method | Endpoint | Izoh |
|---|---|---|
| GET | `/settings/` | SiteSettings singleton |
| GET | `/home/` | Aggregated: slides, stats, categories, featured_products, export_regions, latest_posts(4) |
| GET | `/categories/` | |
| GET | `/products/` | Filter: `category`, `badge`, `family`, `search` + pagination |
| GET | `/products/{slug}/` | images, weights, family bo'yicha vkus-variantlar, xarakteristikalar |
| GET | `/products/{slug}/related/` | M2M, bo'sh bo'lsa kategoriya fallback |
| GET | `/posts/` , `/posts/{slug}/` | detalda: blocks + other_posts |
| GET | `/timeline/`, `/companies/`, `/career-values/`, `/partners/`, `/certificates/` | |
| GET | `/pages/{slug}/` | privacy-policy, consent |
| POST | `/leads/` | throttle `5/hour` |
| POST | `/subscriptions/` | throttle `3/hour` |
| GET | `/subscriptions/unsubscribe/{token}/` | |

### Admin CRUD (`IsAdminUser`, mavjud SimpleJWT bilan)

Yuqoridagi barcha modellar uchun to'liq CRUD. `Lead` — faqat list/retrieve/status-update/destroy,
`NewsletterSubscription` — list/destroy. Public va admin serializer'lar **alohida**
(`ProductSerializer` vs `ProductAdminSerializer`).

### Services

- `leads.services.create_lead(dto) -> Lead` — saqlaydi + adminga xabar yuboradi.
  Xabar yuborish **Celery task** orqali (`apps/logger/tasks/notify_admin_task.py` va
  `handlers/send_bot_message.py` naqshini kuzat) — request'ni bloklamasin.
  Notifier interfeys orqali ulanadi (DIP).
- `leads.services.subscribe(email)` — idempotent.

### Caching

`/home/`, `/settings/`, `/categories/` — 5 daqiqa (mavjud Redis), model `post_save` da invalidate.

---

## Qo'shimcha

- Django Admin: barcha modellar registratsiya, `ProductImage` va `PostBlock` — inline.
- `seed` management command: demo kontent (kategoriyalar, ~10 mahsulot, 4 yangilik, timeline).
- Testlar: model constraint'lar, `create_lead` service, har bir public endpoint smoke-test,
  filter/pagination. Har bir app o'z naqshiga mos joyda (`tests.py` yoki `tests/`).

## Ish tartibi

Bosqichma-bosqich bajar, har bosqichdan keyin to'xtab natijani ko'rsat:

1. `catalog` app: model → migration → admin → serializer/selector → view → url → test
2. `blog`, `about`
3. `careers`, `partners`, `pages`
4. `leads` + Celery notifikatsiya + throttling
5. Admin CRUD endpointlar
6. Caching + seed command

Talab noaniq bo'lsa — taxmin qilma, savol ber.
