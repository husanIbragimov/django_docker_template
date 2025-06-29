from rest_framework import serializers

from apps.upload.models import UploadFile


class UploadFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UploadFile
        fields = ("id", "file")
        read_only_fields = ("id",)
