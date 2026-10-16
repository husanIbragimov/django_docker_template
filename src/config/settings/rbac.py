from .env import env

RBAC = {
    # Unregistered (not yet rbac_sync'ed) APIs -> 403. Keep False in production.
    "ALLOW_UNREGISTERED": env.bool("RBAC_ALLOW_UNREGISTERED", False),
    "MODULE_GRANTS_ENDPOINTS": True,
    "CACHE_ALIAS": "default",
    "EXCLUDE_KEY_PATTERNS": [r"schema", r"swagger", r"redoc", r"^djdt", r"^api-docs$"],
}
