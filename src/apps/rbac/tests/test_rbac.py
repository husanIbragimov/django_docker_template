from io import StringIO

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.management import call_command
from django.test import override_settings
from rest_framework.test import APITestCase

from apps.rbac.models import ApiEndpoint, Module, Role
from apps.rbac.services import get_user_access, user_can

User = get_user_model()


def sync():
    call_command("rbac_sync", stdout=StringIO())


@override_settings(ROOT_URLCONF="apps.rbac.tests.demo_urls")
class Base(APITestCase):
    def setUp(self):
        cache.clear()
        sync()
        self.user = User.objects.create_user("cashier", password="x")
        self.role = Role.objects.create(code="cashier", name="Kassir")
        self.role.users.add(self.user)
        self.client.force_authenticate(self.user)

    def grant(self, *keys):
        self.role.endpoints.add(*ApiEndpoint.objects.filter(key__in=keys))

    def ep(self, key):
        return ApiEndpoint.objects.get(key=key)


class SyncTests(Base):
    def test_keys_discovered(self):
        keys = set(ApiEndpoint.objects.values_list("key", flat=True))
        self.assertTrue(
            {
                "finance:student-payment-create",
                "finance:statistics",
                "finance:employee-salary#GET",
                "finance:employee-salary#POST",
                "crm:lead.list",
                "crm:lead.create",
                "crm:lead.convert",
                "reports.debtors",
                "rbac:role.set_access",
            }
            <= keys
        )
        # public va gateway view'lar katalogga kirmaydi
        self.assertFalse(any(k.startswith("health") or k == "gateway" or "token" in k for k in keys))
        self.assertEqual(self.ep("crm:lead.convert").path, "/api/crm/leads/{pk}/convert/")
        self.assertEqual(self.ep("reports.debtors").name, "Qarzdorlar hisoboti")
        self.assertEqual(self.ep("reports.debtors").group, "report")

    def test_stale_marked_inactive_and_idempotent(self):
        ApiEndpoint.objects.create(key="old:removed", name="old")
        sync()
        self.assertFalse(self.ep("old:removed").is_active)
        count = ApiEndpoint.objects.count()
        sync()
        self.assertEqual(ApiEndpoint.objects.count(), count)

    def test_sync_keeps_admin_edited_name(self):
        ApiEndpoint.objects.filter(key="finance:statistics").update(name="Statistika (custom)")
        sync()
        self.assertEqual(self.ep("finance:statistics").name, "Statistika (custom)")


class PermissionTests(Base):
    def test_denied_without_grant(self):
        self.assertEqual(self.client.post("/api/finance/student-payment/").status_code, 403)

    def test_direct_grant(self):
        self.grant("finance:student-payment-create")
        self.assertEqual(self.client.post("/api/finance/student-payment/").status_code, 201)
        self.assertEqual(self.client.get("/api/finance/statistics/").status_code, 403)

    def test_unauthenticated(self):
        self.client.force_authenticate(None)
        self.assertIn(self.client.get("/api/finance/statistics/").status_code, (401, 403))

    def test_public_view_and_public_flag(self):
        self.client.force_authenticate(None)
        self.assertEqual(self.client.get("/api/health/").status_code, 200)
        self.client.force_authenticate(self.user)
        ApiEndpoint.objects.filter(key="finance:statistics").update(is_public=True)
        from apps.rbac.services import invalidate

        invalidate()  # .update() signal yubormaydi
        self.assertEqual(self.client.get("/api/finance/statistics/").status_code, 200)

    def test_per_method(self):
        self.grant("finance:employee-salary#GET")
        self.assertEqual(self.client.get("/api/finance/employee/1/salary/").status_code, 200)
        self.assertEqual(self.client.post("/api/finance/employee/1/salary/").status_code, 403)

    def test_viewset_actions_are_separate(self):
        self.grant("crm:lead.list")
        self.assertEqual(self.client.get("/api/crm/leads/").status_code, 200)
        self.assertEqual(self.client.post("/api/crm/leads/").status_code, 403)
        self.assertEqual(self.client.post("/api/crm/leads/5/convert/").status_code, 403)
        self.grant("crm:lead.convert")
        self.assertEqual(self.client.post("/api/crm/leads/5/convert/").status_code, 200)

    def test_function_view_custom_key(self):
        self.assertEqual(self.client.get("/api/reports/debtors/").status_code, 403)
        self.grant("reports.debtors")
        self.assertEqual(self.client.get("/api/reports/debtors/").status_code, 200)

    def test_module_grants_endpoints(self):
        module = Module.objects.create(code="finance", name="Moliya")
        module.endpoints.add(self.ep("finance:statistics"))
        self.assertEqual(self.client.get("/api/finance/statistics/").status_code, 403)
        self.role.modules.add(module)
        self.assertEqual(self.client.get("/api/finance/statistics/").status_code, 200)

    @override_settings(RBAC={"MODULE_GRANTS_ENDPOINTS": False})
    def test_module_grants_disabled(self):
        module = Module.objects.create(code="finance", name="Moliya")
        module.endpoints.add(self.ep("finance:statistics"))
        self.role.modules.add(module)
        self.assertEqual(self.client.get("/api/finance/statistics/").status_code, 403)

    def test_inactive_role(self):
        self.grant("finance:statistics")
        self.role.is_active = False
        self.role.save()
        self.assertEqual(self.client.get("/api/finance/statistics/").status_code, 403)

    def test_super_role_and_superuser(self):
        Role.objects.create(code="boss", name="Boss", is_super=True).users.add(self.user)
        self.assertEqual(self.client.get("/api/finance/statistics/").status_code, 200)
        admin = User.objects.create_superuser("root", password="x")
        self.client.force_authenticate(admin)
        self.assertEqual(self.client.post("/api/crm/leads/").status_code, 201)

    def test_revoke_invalidates_cache(self):
        self.grant("finance:statistics")
        self.assertEqual(self.client.get("/api/finance/statistics/").status_code, 200)
        self.role.endpoints.clear()
        self.assertEqual(self.client.get("/api/finance/statistics/").status_code, 403)
        self.role.endpoints.add(self.ep("finance:statistics"))
        self.role.users.remove(self.user)
        self.assertEqual(self.client.get("/api/finance/statistics/").status_code, 403)

    def test_unregistered_denied_by_default(self):
        ApiEndpoint.objects.filter(key="finance:statistics").delete()
        self.assertEqual(self.client.get("/api/finance/statistics/").status_code, 403)
        with override_settings(RBAC={"ALLOW_UNREGISTERED": True}):
            self.assertEqual(self.client.get("/api/finance/statistics/").status_code, 200)

    def test_user_can_helper(self):
        self.grant("reports.debtors")
        self.assertTrue(user_can(self.user, "reports.debtors"))
        self.assertFalse(user_can(self.user, "finance:statistics"))

    def test_query_count_cached(self):
        self.grant("finance:statistics")
        self.client.get("/api/finance/statistics/")  # warm cache
        with self.assertNumQueries(0):
            self.client.get("/api/finance/statistics/")


class GatewayTests(Base):
    def setUp(self):
        super().setUp()
        self.invoices = ApiEndpoint.objects.create(
            key="billing.invoices.read", kind="gateway", path=r"/gw/billing/invoices(/.*)?", methods=["GET"]
        )
        self.pay = ApiEndpoint.objects.create(
            key="billing.invoices.pay", kind="gateway", path=r"/gw/billing/invoices/\d+/pay/", methods=["POST"]
        )

    def test_inprocess_proxy(self):
        self.assertEqual(self.client.get("/gw/billing/invoices/").status_code, 403)
        self.role.endpoints.add(self.invoices)
        r = self.client.get("/gw/billing/invoices/12/")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data["rbac_key"], "billing.invoices.read")
        self.assertEqual(self.client.post("/gw/billing/invoices/12/pay/").status_code, 403)
        self.role.endpoints.add(self.pay)
        self.assertEqual(self.client.post("/gw/billing/invoices/12/pay/").status_code, 200)

    def test_unknown_gateway_path_denied(self):
        self.role.endpoints.add(self.invoices)
        self.assertEqual(self.client.get("/gw/hr/salaries/").status_code, 403)

    def test_nginx_authz(self):
        hdr = {"HTTP_X_ORIGINAL_URI": "/gw/billing/invoices/?page=2", "HTTP_X_ORIGINAL_METHOD": "GET"}
        self.assertEqual(self.client.get("/api/rbac/authz/", **hdr).status_code, 403)
        self.role.endpoints.add(self.invoices)
        r = self.client.get("/api/rbac/authz/", **hdr)
        self.assertEqual(r.status_code, 204)
        self.assertEqual(r["X-RBAC-Key"], "billing.invoices.read")
        self.client.force_authenticate(None)
        self.assertEqual(self.client.get("/api/rbac/authz/", **hdr).status_code, 401)

    def test_gateway_validation(self):
        self.client.force_authenticate(User.objects.create_superuser("root", password="x"))
        bad = self.client.post("/api/rbac/endpoints/", {"key": "x", "kind": "gateway", "path": "(("}, format="json")
        self.assertEqual(bad.status_code, 400)
        internal = self.client.post("/api/rbac/endpoints/", {"key": "y", "kind": "internal"}, format="json")
        self.assertEqual(internal.status_code, 400)
        ok = self.client.post(
            "/api/rbac/endpoints/",
            {"key": "hr.read", "kind": "gateway", "path": r"/gw/hr/.*", "methods": ["get"]},
            format="json",
        )
        self.assertEqual(ok.status_code, 201, ok.data)
        self.assertEqual(ok.data["methods"], ["GET"])
        stats = self.ep("finance:statistics")
        r = self.client.patch(f"/api/rbac/endpoints/{stats.pk}/", {"path": "/hack/"}, format="json")
        self.assertEqual(r.status_code, 400)
        r = self.client.patch(f"/api/rbac/endpoints/{stats.pk}/", {"name": "Statistika"}, format="json")
        self.assertEqual(r.status_code, 200)


class ManagementApiTests(Base):
    def test_me(self):
        root = Module.objects.create(code="finance", name="Moliya")
        child = Module.objects.create(code="finance.stats", name="Statistika", parent=root)
        child.endpoints.add(self.ep("finance:statistics"))
        self.role.modules.add(root, child)
        self.grant("reports.debtors")
        data = self.client.get("/api/rbac/me/").data
        self.assertFalse(data["is_super"])
        self.assertEqual(data["modules"][0]["code"], "finance")
        self.assertTrue(data["modules"][0]["children"][0]["has_access"])
        self.assertEqual(set(data["endpoints"]), {"finance:statistics", "reports.debtors"})

    def test_role_management_requires_permission(self):
        self.assertEqual(self.client.get("/api/rbac/roles/").status_code, 403)
        self.grant("rbac:role.list")
        self.assertEqual(self.client.get("/api/rbac/roles/").status_code, 200)

    def test_set_access_flow(self):
        self.client.force_authenticate(User.objects.create_superuser("root", password="x"))
        module = Module.objects.create(code="crm", name="CRM")
        module.endpoints.add(self.ep("crm:lead.list"))
        stats = self.ep("finance:statistics")
        r = self.client.put(
            f"/api/rbac/roles/{self.role.pk}/access/", {"modules": [module.pk], "endpoints": [stats.pk]}, format="json"
        )
        self.assertEqual(r.status_code, 200, r.data)
        flat = {e["key"]: e for g in r.data["endpoints"] for e in g["endpoints"]}
        self.assertTrue(flat["finance:statistics"]["granted"])
        self.assertEqual(flat["crm:lead.list"]["via_modules"], ["crm"])
        self.assertTrue(r.data["modules"][0]["has_access"])

        access = get_user_access(self.user)
        self.assertEqual(access.endpoints, {"finance:statistics", "crm:lead.list"})

        r = self.client.put(f"/api/rbac/users/{self.user.pk}/roles/", {"roles": []}, format="json")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(get_user_access(self.user).endpoints, frozenset())

    def test_module_cycle_rejected(self):
        self.client.force_authenticate(User.objects.create_superuser("root", password="x"))
        a = Module.objects.create(code="a", name="A")
        b = Module.objects.create(code="b", name="B", parent=a)
        r = self.client.patch(f"/api/rbac/modules/{a.pk}/", {"parent": b.pk}, format="json")
        self.assertEqual(r.status_code, 400)


class ModulesCommandTests(Base):
    def test_load_my_days_format(self):
        import json
        import tempfile

        data = [
            {
                "id": 1,
                "name": "Dashboard",
                "description": "string",
                "endpoints": ["finance:statistics"],
                "children": [{"id": 2, "name": "Main", "description": "", "children": []}],
            }
        ]
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as fh:
            json.dump(data, fh)
        call_command("rbac_modules", "load", fh.name, stdout=StringIO(), stderr=StringIO())
        root = Module.objects.get(code="dashboard")
        self.assertEqual(root.children.get().code, "main")
        self.assertEqual(list(root.endpoints.values_list("key", flat=True)), ["finance:statistics"])
