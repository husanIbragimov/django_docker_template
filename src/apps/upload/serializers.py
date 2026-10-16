from rest_framework import serializers

from apps.upload.models import FilePath


class UploadFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = FilePath
        fields = ("id", "file")
        read_only_fields = ("id",)
