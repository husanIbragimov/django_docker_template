from django.urls import path

from apps.upload.views import UploadFileAPIView

urlpatterns = [
    path("file/", UploadFileAPIView.as_view(), name="upload-file"),
]
