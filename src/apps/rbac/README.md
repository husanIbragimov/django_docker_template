# django-api-rbac — API darajasidagi RBAC

Ruxsat **model CRUD'i** (Django'ning `add_/change_/delete_/view_` permission'lari) bo'yicha emas,
**API** bo'yicha beriladi. Bitta API = bitta ruxsat kaliti. API bir nechta modelga tegishi,
umuman modelga bog'liq bo'lmasligi yoki boshqa servisga proxy bo'lishi mumkin.

`my_days`dagi tizim faqat UI'ni cheklaydi (`RoleModule` + `UserRoleModuleAccess.has_access`).
Backend esa `IsAuthenticated`dan boshqa narsani tekshirmaydi, ya'ni Postman orqali har qanday
API'ni chaqirish mumkin. Bu app UI modullar g'oyasini saqlab qoladi va unga backend'dagi majburiy
tekshiruvni qo'shadi.

```
Role ──< modules >── Module (UI daraxt: menyu, sahifa, tugma)
  │                     │
  │                     └──< endpoints >──┐   (UI element ishlashi uchun kerakli API'lar)
  └──────< endpoints >────────────────────┴── ApiEndpoint (key, kind=internal|gateway)
  └──────< users >── User
```

**Foydalanuvchining ruxsatli API'lari** = rollariga to'g'ridan-to'g'ri berilgan API'lar ∪ rollaridagi
UI modullarga bog'langan API'lar (`MODULE_GRANTS_ENDPOINTS`). Admin odatda faqat UI daraxtida belgi
qo'yadi, backend ruxsatlari esa shundan avtomatik kelib chiqadi. Kerak bo'lsa, alohida API'ni qo'lda
ham qo'shish mumkin.

---

## 1. O'rnatish

Bu loyihada app `src/apps/rbac/` da turadi va quyidagicha ulangan:

```python
# config/settings/apps.py
LOCAL_APPS = [..., "apps.rbac"]

# config/settings/rest_framework.py
REST_FRAMEWORK = {
    ...
    "DEFAULT_PERMISSION_CLASSES": ("apps.rbac.permissions.HasApiAccess",),
}

# config/settings/rbac.py
RBAC = {
    "ALLOW_UNREGISTERED": env.bool("RBAC_ALLOW_UNREGISTERED", False),  # sync qilinmagan API -> 403
    "MODULE_GRANTS_ENDPOINTS": True,  # UI modul berilsa, uning API'lari ham beriladi
    "CACHE_ALIAS": "default",         # Redis
}
```

```python
# apps/v1.py
path("rbac/", include(("apps.rbac.urls", "rbac"), namespace="rbac")),  # -> /api/v1/rbac/
```

```bash
python manage.py migrate rbac
python manage.py rbac_sync --audit     # API katalogini to'ldiradi + himoyasiz view'larni ko'rsatadi
```

`rbac_sync`ni deploy'da `migrate`dan keyin har safar ishga tushiring. U idempotent: yangi API'larni
qo'shadi, path/method'larni yangilaydi, koddan yo'qolganlarini `is_active=False` qiladi. Admin
o'zgartirgan nom va tavsiflarga tegmaydi.

## 2. API kaliti qanday aniqlanadi

| View turi | Kalit | Misol |
|---|---|---|
| `APIView` / generic view | URL `view_name` | `finance:student-payment-create` |
| `ViewSet` (router) | `<ns>:<basename>.<action>` | `crm:lead.list`, `crm:lead.convert` |
| `rbac_key = "..."` | aynan shu | `reports.debtors` |
| `rbac_per_method = True` | `<key>#<METHOD>` | `finance:employee-salary#POST` |
| `rbac_gateway = True` | gateway regex orqali | `billing.invoices.read` |

URL `name` kalitning asosi, shuning uchun nomlarni barqaror saqlang. Agar nomni o'zgartirsangiz,
sync yangi kalit yaratadi, eskisi esa nofaol bo'ladi va rollarni qayta bog'lashga to'g'ri keladi.
Uzoq muddat yashaydigan API'lar uchun `rbac_key` qo'yish ishonchliroq.

```python
class StudentPaymentCreateView(APIView):
    """O'quvchidan to'lov qabul qilish"""       # birinchi qator -> ApiEndpoint.name
    rbac_key = "finance.student_payment.create"  # ixtiyoriy
    rbac_group = "finance"                       # ixtiyoriy (sukut: apps.<bu_qism>.…)

class EmployeeSalaryView(APIView):
    rbac_per_method = True    # GET (ko'rish) va POST (to'lash) alohida ruxsat

class LeadViewSet(ModelViewSet):
    rbac_key = {"list": "crm.leads.read", "retrieve": "crm.leads.read"}  # action'larni birlashtirish

class LoginView(APIView):
    rbac_public = True        # RBAC tekshirmaydi (login, refresh, health …)
    permission_classes = []

@rbac(key="reports.debtors", name="Qarzdorlar hisoboti")   # funksiya view'lar uchun
@api_view(["GET"])
def debtors(request): ...
```

Kod ichida qo'lda tekshirish uchun: `from apps.rbac.services import user_can; user_can(request.user, "reports.debtors")`.

## 3. Gateway / proxy API'lar

Django'da view'i yo'q API'lar `ApiEndpoint(kind="gateway")` sifatida qo'lda kiritiladi
(`POST /api/v1/rbac/endpoints/` yoki admin orqali). `path` — to'liq yo'lga `fullmatch` qilinadigan regex,
`methods` — `[]` bo'lsa barcha metodlar. Bir nechta pattern mos kelsa, eng uzuni (aniqrog'i) tanlanadi.

```json
{"key": "billing.invoices.read", "kind": "gateway", "path": "/gw/billing/invoices(/.*)?", "methods": ["GET"]}
```

**A) Django ichidagi proxy view** — `rbac_gateway = True` (namuna: `tests/demo_views.py: BillingGatewayProxyView`).

**B) nginx `proxy_pass`** — so'rov Django'ga umuman kelmaydi, shuning uchun `auth_request` ishlatiladi:

```nginx
location /gw/ {
    auth_request /_rbac_auth;
    proxy_pass http://billing_service/;
}
location = /_rbac_auth {
    internal;
    proxy_pass http://django/api/v1/rbac/authz/;
    proxy_pass_request_body off;
    proxy_set_header Content-Length "";
    proxy_set_header X-Original-URI    $request_uri;
    proxy_set_header X-Original-Method $request_method;
    proxy_set_header Authorization     $http_authorization;
}
```

`/api/v1/rbac/authz/` qaytaradigan javoblar: `204` — ruxsat bor, `401` — token yo'q yoki yaroqsiz, `403` — ruxsat yo'q.
Bu endpoint keshdan ishlaydi (iliq keshda DB so'rovi 0 ta), shuning uchun har bir proxy so'rovida
chaqirilishi muammo emas.

## 4. Boshqaruv API'lari (UI uchun)

Bu API'larning o'zi ham RBAC bilan himoyalangan (`rbac:role.list` va hokazo). Superuser yoki
`is_super` rol hamma narsaga kira oladi.

| Metod | URL | Vazifasi |
|---|---|---|
| GET | `/api/v1/rbac/me/` | Joriy user: `is_super`, `modules` (daraxt + `has_access`), `endpoints` (kalitlar) |
| GET/POST | `/api/v1/rbac/roles/` | Rollar |
| GET/PUT/PATCH/DELETE | `/api/v1/rbac/roles/{id}/` | |
| GET | `/api/v1/rbac/roles/{id}/access/` | Rol tahrirlash ekrani: modul daraxti + guruhlangan API'lar (`granted`, `via_modules`) |
| PUT | `/api/v1/rbac/roles/{id}/access/` | `{"modules":[..], "endpoints":[..]}` — to'liq almashtiradi |
| PUT | `/api/v1/rbac/roles/{id}/users/` | `{"users":[..]}` |
| GET/PUT | `/api/v1/rbac/users/{id}/roles/` | Foydalanuvchi rollari, `{"roles":[..]}` |
| GET | `/api/v1/rbac/endpoints/?kind=&group=&is_active=` | API katalogi |
| GET | `/api/v1/rbac/endpoints/groups/` | Guruhlangan katalog |
| POST | `/api/v1/rbac/endpoints/` | Faqat gateway API yaratish |
| PATCH | `/api/v1/rbac/endpoints/{id}/` | Ichki API'da faqat `name`, `description`, `group`, `is_public` |
| GET/POST/… | `/api/v1/rbac/modules/`, `/api/v1/rbac/modules/tree/` | UI modullar (`endpoints` — bog'langan API id'lari) |
| GET | `/api/v1/rbac/authz/` | nginx `auth_request` |

### Frontend (Vue + TS) namunasi

```ts
// stores/access.ts
const me = await api.get<{ is_super: boolean; modules: Node[]; endpoints: string[] }>("/rbac/me/");
const moduleSet = new Set<string>();
const walk = (ns: Node[]) => ns.forEach(n => { if (n.has_access) moduleSet.add(n.code); walk(n.children); });
walk(me.modules);
const apiSet = new Set(me.endpoints);

export const canSee = (code: string) => me.is_super || moduleSet.has(code);   // menyu / sahifa / tugma
export const canCall = (key: string) => me.is_super || apiSet.has(key);       // "To'lash" tugmasi va h.k.
```

```vue
<button v-if="canCall('finance:student-payment-create')">To'lov qabul qilish</button>
<RouterLink v-if="canSee('finance.reports')" to="/finance/reports">Hisobotlar</RouterLink>
```

UI'da yashirish faqat qulaylik uchun. Haqiqiy himoyani backend beradi: yashirin tugmaning API'sini
to'g'ridan-to'g'ri chaqirsa ham `403` qaytadi.

## 5. Kesh va unumdorlik

- Foydalanuvchi ruxsatlari (`frozenset` kalitlar) keshda saqlanadi, bitta so'rov ichida esa `request`ga
  ham yoziladi. Iliq keshda tekshiruv **0 ta DB so'rovi** bilan ishlaydi (testda tekshirilgan).
- Invalidatsiya global versiya raqami orqali amalga oshadi. Rol, modul, endpoint yoki ularning
  bog'lanishi o'zgarsa, signal versiyani oshiradi va eski kesh o'z-o'zidan eskiradi.
- ⚠️ `QuerySet.update()` va `bulk_*` signal yubormaydi. Ulardan keyin `apps.rbac.services.invalidate()`ni
  qo'lda chaqiring.
- `user.is_active` va `is_superuser` keshga yozilmaydi, ular har so'rovda user obyektining o'zidan o'qiladi.
- Ko'p worker/pod bo'lsa, `CACHE_ALIAS` Redis bo'lishi shart. LocMem cache'da invalidatsiya boshqa
  process'larga yetib bormaydi.

## 6. my_days'dan ko'chirish

my_days'da ~100 ta view `permission_classes = [IsAuthenticated]`ni o'zi belgilaydi. Bu esa
`DEFAULT_PERMISSION_CLASSES`ni bekor qiladi. Ko'chirish tartibi:

1. `rbac` app'ni qo'shing, migrate qiling, keyin `RBAC["ALLOW_UNREGISTERED"] = True` bilan ishga tushiring
   (o'tish davri).
2. `[IsAuthenticated]` → `[HasApiAccess]` (HasApiAccess autentifikatsiyani ham tekshiradi):
   ```bash
   grep -rl "permission_classes = \[IsAuthenticated\]" apps | xargs sed -i \
     's/permission_classes = \[IsAuthenticated\]/permission_classes = [HasApiAccess]/'
   ```
   So'ng import'larni to'g'rilang va `python manage.py rbac_sync --audit` bilan qolganlarini toping.
3. Eski modullarni ko'chiring: `python manage.py rbac_modules load staticfiles/modules.json`
   (my_days formati qo'llanadi, `code` = `slugify(name)`).
4. Eski rollarni ko'chirish (bir martalik skript, `manage.py shell`):
   ```python
   from apps.account.models import UserRole, UserRoleModuleAccess, User
   from django.utils.text import slugify
   from apps.rbac.models import Role, Module
   for old in UserRole.objects.all():
       role, _ = Role.objects.get_or_create(code=slugify(old.name) or f"role-{old.pk}", defaults={"name": old.name})
       codes = [slugify(a.module.name) for a in UserRoleModuleAccess.objects.filter(role=old, has_access=True)]
       role.modules.set(Module.objects.filter(code__in=codes))
       role.users.set(User.objects.filter(role=old))
   ```
5. Har bir UI modulga uning API'larini bog'lang (admin, `PUT /modules/{id}/` yoki JSON'dagi `"endpoints"`).
   Eng ko'p mehnat shu bosqichda ketadi: qaysi ekran qaysi API'larni chaqirishini frontend'dan bilib olasiz.
6. Hamma narsa bog'langach, `ALLOW_UNREGISTERED = False` qiling.

## 7. Testlar

```bash
python src/manage.py test apps.rbac      # 27 ta test
```

Testlar quyidagilarni qamraydi: sync (kalit topish, idempotentlik, nofaol qilish), to'g'ridan-to'g'ri
va modul orqali berilgan ruxsat, ViewSet action'lari, per-method ruxsat, funksiya view, public view,
superuser va super-rol, kesh invalidatsiyasi va 0 ta DB so'rovi, sync qilinmagan API, in-process
gateway va nginx `authz`, boshqaruv API'lari, modul daraxtida sikl va JSON yuklash.

## Fayllar

```
rbac/
  models.py        Module, ApiEndpoint, Role
  keys.py          kalitni aniqlash (runtime + sync uchun bitta qoida), URL discovery
  services.py      ruxsatlarni hisoblash, kesh, gateway regex matching, user_can()
  permissions.py   HasApiAccess (DRF), HasModule
  decorators.py    @rbac(...) — funksiya view'lar uchun
  signals.py       kesh invalidatsiyasi
  views.py/urls.py boshqaruv API, /me, /authz
  management/commands/rbac_sync.py, rbac_modules.py
  tests/demo_urls.py, demo_views.py  testlar uchun namuna API'lar (ROOT_URLCONF override)
```
