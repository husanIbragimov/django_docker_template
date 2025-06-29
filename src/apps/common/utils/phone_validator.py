import re

from django.core.validators import RegexValidator

regex_pattern = r"^\+998([0-9]{2})[0-9]{7}$"

phone_validator = RegexValidator(regex=regex_pattern, message="Phone number is not correct. Example: '+998901234567'")


def is_phone_number_valid(phone_number) -> bool:
    pattern = regex_pattern
    return bool(re.match(pattern, phone_number))
