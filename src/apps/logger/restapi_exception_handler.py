import traceback
from datetime import datetime

from _auth.models import ScientistUser
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.http import Http404
from logger import errorRequestLogger
from rest_framework import exceptions
from rest_framework.exceptions import APIException
from rest_framework.views import exception_handler


def restapi_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if isinstance(exc, Http404):
        exc = exceptions.NotFound(*exc.args)
    elif isinstance(exc, PermissionDenied):
        exc = exceptions.PermissionDenied(*exc.args)

    if isinstance(exc, APIException):
        if response and response.status_code >= 500:
            _log(context["request"], exc)

    else:
        _log(context["request"], exc)

    return response


def _log(request, exception):
    try:
        error_traceback = "".join(traceback.format_exception(None, exception, exception.__traceback__))
        message = (
            f"\n-----\n"
            f"Exception occurred at {request.path} | "
            f"Method: {request.method} | "
            f"User: {_get_user_info(request)} | "
            f"Time: {_get_current_time()} | "
            f"Error: {str(exception)} | "
            f"Traceback: {error_traceback}"
            f"-----\n"
        )

        errorRequestLogger.error(message)
    except Exception:
        errorRequestLogger.error(f"Error while logging error: {str(exception)}")


def _get_current_time():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _get_user_info(request):
    if request.user is None:
        return "AnonymousUser"
    if isinstance(request.user, User) and request.user.is_authenticated:
        return f"{request.user.username} (ID: {request.user.id})"
    elif isinstance(request.user, ScientistUser):
        return f"Scientist (ID: {request.user.id} Name: {request.user.full_name})"
