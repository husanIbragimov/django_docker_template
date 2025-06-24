from django.urls import path

from apps.user.views import UserMeView

urlpatterns = [
    path("me/", view=UserMeView.as_view(), name="user_me_view"),
]
