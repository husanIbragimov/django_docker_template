from enum import Enum

from django.utils.translation import gettext_lazy as _


class TranslatableText(Enum):
    # roles
    admin = _("Admin")
    user = _("User")

    # status
    in_progress = _("In progress")

    not_passed = _("Not passed")
    passed = _("Passed")

    username = _("username")
    first_name = _("first name")
    last_name = _("last name")
    birth_date = _("birth date")
    phone_number = _("phone number")
    email = _("email")
    user_type = _("user type")
    photo = _("photo")
    is_staff = _("staff status")
    is_superuser = _("superuser status")
    date_joined = _("date joined")
    active = _("active")

    gender = _("gender")
    male = _("male")
    female = _("female")

    # validation errors
    user_with_is_staff_help_text = _("Designates whether the _auth can log into this admin site.")
    user_with_is_active_help_text = _(
        "Designates whether this _auth should be treated as active. " "Unselect this instead of deleting _auth."
    )
    user_with_phone_exists = _("The user with this phone number already exists.")
    user_with_email_exists = _("The user with this email address already exists.")
