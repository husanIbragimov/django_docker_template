# RBAC — API darajasidagi ruxsatlar

Ruxsat model CRUD'i bo'yicha emas, **API bo'yicha** beriladi: **bitta API = bitta ruxsat kaliti**.
UI'da tugmani yashirish faqat qulaylik uchun. Haqiqiy himoyani backend beradi: ruxsati yo'q
foydalanuvchi API'ni Postman orqali chaqirsa ham `403` oladi.

```
User >──< Role >──< Module (UI daraxti: menyu, sahifa, tugma)
            │          └──< endpoints
            └──< endpoints ──────────┴── ApiEndpoint (key)
```

**Userning ruxsatlari** = rolga to'g'ridan-to'g'ri berilgan API'lar **+** roldagi UI modullarga
bog'langan API'lar. Odatda admin faqat modul daraxtida belgi qo'yadi, API ruxsatlari esa shundan
avtomatik kelib chiqadi.

---

## 1. Tez start

App allaqachon ulangan: `config/settings/apps.py`, `config/settings/rbac.py`,
`config/settings/rest_framework.py` (`DEFAULT_PERMISSION_CLASSES = HasApiAccess`) va
`apps/v1.py` (`/api/v1/rbac/`).

```bash
make migrate
make rbac-seed                                        # rbac_sync + assets/ui_template.json ni yuklash
bash scripts/compose.sh dev run --rm web python manage.py rbac_demo   # ixtiyoriy: demo rollar va userlar (parol: 123)
```

Host'da (`make local`) bo'lsa:

```bash
python src/manage.py migrate
python src/manage.py rbac_seed
python src/manage.py rbac_demo
```

`rbac_demo` quyidagi userlarni yaratadi:

| Username | Rol | Nima qila oladi |
|---|---|---|
| `rbac_admin` | `rbac-admin` | Rollar, modullar va API'larni to'liq boshqaradi |
| `manager` | `manager` | Rollarni ko'radi, userga rol beradi, fayl yuklaydi |
| `auditor` | `auditor` | RBAC'ni faqat ko'radi |
| `operator` | `operator` | Faqat profil va fayl yuklash |

## 2. Buyruqlar

| Buyruq | Vazifasi |
|---|---|
| `rbac_sync` | URLconf'dagi barcha API'larni `ApiEndpoint` jadvaliga yozadi |
| `rbac_sync --dry-run` | Faqat nima o'zgarishini ko'rsatadi |
| `rbac_sync --audit` | `HasApiAccess` ishlatmayotgan (himoyasiz) view'larni ko'rsatadi |
| `rbac_sync --prune` | Koddan o'chgan API'larni bazadan o'chiradi (sukut: faqat `is_active=False`) |
| `rbac_modules load <file>` / `dump <file>` | UI modul daraxtini JSON'dan yuklash / JSON'ga chiqarish |
| `rbac_seed` | `rbac_sync` + `rbac_modules load assets/ui_template.json` |
| `rbac_demo` | Demo rollar va userlar |

`rbac_sync` idempotent: admin o'zgartirgan nom va tavsiflarga tegmaydi. Har deploy'da
`migrate`dan keyin ishga tushiring.

## 3. API kaliti qanday hosil bo'ladi

| View | Kalit | Shu loyihadan misol |
|---|---|---|
| `APIView` / generic | `<namespace>:<url name>` | `upload:upload-file`, `user:user_me_view` |
| `ViewSet` (router) | `<namespace>:<basename>.<action>` | `rbac:role.list`, `rbac:role.set_access` |
| `rbac_key = "..."` | aynan shu | `reports.debtors` |
| `rbac_per_method = True` | `<kalit>#<METHOD>` | `upload:upload-file#POST` |

URL `name` kalitning asosi. Nomni o'zgartirsangiz, yangi kalit paydo bo'ladi va rollarni qayta
bog'lash kerak bo'ladi — uzoq yashaydigan API'larga `rbac_key` qo'ygan ma'qul.

## 4. Yangi API qo'shish (misol)

```python
# apps/blog/views.py
class PostCreateView(BaseGenericAPI):
    """Post yaratish"""                 # birinchi qator -> ApiEndpoint.name
    serializer_class = PostSerializer
    # permission_classes ni YOZMANG — sukut bo'yicha HasApiAccess ishlaydi

# apps/blog/urls.py
path("posts/", PostCreateView.as_view(), name="post-create")   # kalit: blog:post-create
```

```jsonc
// assets/ui_template.json — tugmani modulga bog'lash
{"code": "blog-posts-create", "name": "Post qo'shish", "endpoints": ["blog:post-create"]}
```

```bash
python src/manage.py rbac_seed     # API katalogga tushadi, modulga bog'lanadi
```

So'ng admin rolga `blog-posts-create` modulini beradi — tamom.

### Boshqa variantlar

```python
class SalaryView(APIView):
    rbac_per_method = True            # GET (ko'rish) va POST (to'lash) — alohida ruxsat

class LeadViewSet(ModelViewSet):
    rbac_key = {"list": "crm.leads.read", "retrieve": "crm.leads.read"}   # action'larni birlashtirish

class HealthView(APIView):
    rbac_public = True                # RBAC tekshirmaydi (login, refresh, health)
    permission_classes = []

@rbac(key="reports.debtors", name="Qarzdorlar hisoboti")   # funksiya view
@api_view(["GET"])
def debtors(request): ...
```

Kod ichida tekshirish:

```python
from apps.rbac.services import user_can

if user_can(request.user, "reports.debtors"):
    ...
```

> ⚠️ `permission_classes = [IsAuthenticated]` yozilsa, `HasApiAccess` **o'chib qoladi**.
> RBAC kerak bo'lsa `[HasApiAccess]` yozing yoki atributni umuman qo'ymang.
> Tekshirish: `python src/manage.py rbac_sync --audit`.

## 5. Boshqaruv API'lari

Hammasi `/api/v1/rbac/` ostida va o'zi ham RBAC bilan himoyalangan. Superuser yoki `is_super=True`
rol hamma narsaga kiradi.

| Metod | URL | Vazifasi |
|---|---|---|
| GET | `me/` | Joriy user: `is_super`, `modules` (daraxt + `has_access`), `endpoints` |
| GET, POST | `roles/` | Rollar |
| GET, PUT, PATCH, DELETE | `roles/{id}/` | |
| GET / PUT | `roles/{id}/access/` | Rol ruxsatlari ekrani / `{"modules": [..], "endpoints": [..]}` |
| PUT | `roles/{id}/users/` | `{"users": [..]}` |
| GET, PUT | `users/{id}/roles/` | `{"roles": [..]}` |
| GET | `endpoints/?kind=&group=&is_active=` | API katalogi |
| GET | `endpoints/groups/` | Guruhlangan katalog |
| POST | `endpoints/` | Faqat gateway API yaratish |
| CRUD | `modules/`, GET `modules/tree/` | UI modullar |
| GET | `authz/` | nginx `auth_request` uchun |

### Misol: rolga ruxsat berish

```bash
TOKEN=$(curl -s -X POST localhost:8000/api/v1/auth/login/ \
  -H 'Content-Type: application/json' -d '{"username":"rbac_admin","password":"123"}' | jq -r .data.access)

# rol yaratish
curl -X POST localhost:8000/api/v1/rbac/roles/ -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' -d '{"code":"editor","name":"Muharrir"}'

# rolga modullar berish (to'liq almashtiradi)
curl -X PUT localhost:8000/api/v1/rbac/roles/5/access/ -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' -d '{"modules":[1,2],"endpoints":[]}'

# userga rol biriktirish
curl -X PUT localhost:8000/api/v1/rbac/users/7/roles/ -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' -d '{"roles":[5]}'
```

> Login javobining aniq tuzilishini Swagger'da (`/api/docs/`) tekshiring.

### Frontend

```ts
const me = await api.get("/rbac/me/");
const modules = new Set<string>();
const walk = (ns) => ns.forEach(n => { if (n.has_access) modules.add(n.code); walk(n.children); });
walk(me.modules);
const apis = new Set(me.endpoints);

export const canSee  = (code: string) => me.is_super || modules.has(code);  // menyu, sahifa, tugma
export const canCall = (key: string)  => me.is_super || apis.has(key);
```

```vue
<button v-if="canSee('upload')">Fayl yuklash</button>
<RouterLink v-if="canSee('rbac-roles')" to="/rbac/roles">Rollar</RouterLink>
```

## 6. Gateway / proxy API'lar

Django'da view'i yo'q API'lar qo'lda kiritiladi (`POST /api/v1/rbac/endpoints/` yoki admin).
`path` — to'liq mos keladigan regex, `methods: []` — barcha metodlar. Bir nechtasi mos kelsa,
eng uzun pattern tanlanadi.

```json
{"key": "billing.invoices.read", "kind": "gateway", "path": "/gw/billing/invoices(/.*)?", "methods": ["GET"]}
```

- **Django ichidagi proxy view** — `rbac_gateway = True` qo'ying (namuna: `tests/demo_views.py`).
- **nginx `proxy_pass`** — `auth_request` orqali:

```nginx
location /gw/ {
    auth_request /_rbac_auth;
    proxy_pass http://billing_service/;
}
location = /_rbac_auth {
    internal;
    proxy_pass http://web:8000/api/v1/rbac/authz/;
    proxy_pass_request_body off;
    proxy_set_header Content-Length "";
    proxy_set_header X-Original-URI    $request_uri;
    proxy_set_header X-Original-Method $request_method;
    proxy_set_header Authorization     $http_authorization;
}
```

`authz/` javoblari: `204` — ruxsat bor, `401` — token yo'q/yaroqsiz, `403` — ruxsat yo'q.

## 7. Sozlamalar (`config/settings/rbac.py`)

| Kalit | Sukut | Ma'nosi |
|---|---|---|
| `ALLOW_UNREGISTERED` | `False` (`RBAC_ALLOW_UNREGISTERED` env) | Sync qilinmagan API'ga ruxsat. Production'da `False` |
| `MODULE_GRANTS_ENDPOINTS` | `True` | Modul berilsa, uning API'lari ham beriladi |
| `SUPERUSER_BYPASS` | `True` | `is_superuser` hamma narsaga kiradi |
| `CACHE_ALIAS` / `CACHE_TIMEOUT` | `default` / 1 soat | Kesh (Redis, DB 1) |
| `EXCLUDE_NAMESPACES`, `EXCLUDE_KEY_PATTERNS` | `admin`, `schema`/`swagger`/... | Sync'da e'tiborsiz qoldiriladi |

## 8. Kesh

- Ruxsatlar Redis'da keshlanadi — iliq keshda tekshiruv **0 ta DB so'rovi**.
- Rol, modul, endpoint yoki ularning bog'lanishi o'zgarsa, signal kesh versiyasini oshiradi.
- ⚠️ `QuerySet.update()` va `bulk_*` signal yubormaydi — keyin `apps.rbac.services.invalidate()` chaqiring.
- `is_active` va `is_superuser` keshlanmaydi, har so'rovda user'dan o'qiladi.

## 9. Testlar

```bash
python src/manage.py test apps.rbac
```

Sync, modul orqali ruxsat, ViewSet action'lari, per-method, public view, super-rol, kesh
invalidatsiyasi, gateway va `authz`, boshqaruv API'lari qamrab olingan.

## Fayllar

```
rbac/
  models.py         Module, ApiEndpoint, Role
  keys.py           API kalitini aniqlash + URL discovery
  services.py       ruxsatlarni hisoblash, kesh, user_can(), invalidate()
  permissions.py    HasApiAccess, HasModule
  decorators.py     @rbac(...)
  signals.py        kesh invalidatsiyasi
  conf.py           sukut sozlamalar
  views.py, urls.py boshqaruv API, me/, authz/
  management/commands/  rbac_sync, rbac_modules, rbac_seed, rbac_demo
  tests/            testlar + demo view'lar
```
