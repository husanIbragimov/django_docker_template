import re

# def is_pbkdf2_sha256_hash(s):
#     return s.startswith('pbkdf2_sha256$')


def is_password_hash(s):
    # PBKDF2-SHA256 hashing formatini tekshirish uchun regex
    pattern = r"^pbkdf2_sha256\$\d+\$[a-zA-Z0-9]+\$[a-zA-Z0-9+/=]+$"
    return bool(re.match(pattern, s))
