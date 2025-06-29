from .env import BASE_DIR
import os

STATIC_URL = 'static/'

# if LOCAL:
#     STATICFILES_DIRS = [
#         os.path.join(BASE_DIR, 'static')
#     ]
# else:
STATIC_ROOT = os.path.join(BASE_DIR.parent, 'static/')

MEDIA_URL = 'media/'
MEDIA_ROOT = os.path.join(BASE_DIR.parent, 'media')
