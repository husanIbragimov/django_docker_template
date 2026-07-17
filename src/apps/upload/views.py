from drf_spectacular.utils import extend_schema
from rest_framework.generics import CreateAPIView
from rest_framework.parsers import FormParser, MultiPartParser

from apps.upload.models import UploadFile
from apps.upload.serializers import UploadFileSerializer


@extend_schema(tags=["Upload"])
class UploadFileAPIView(CreateAPIView):
    queryset = UploadFile.objects.all()
    serializer_class = UploadFileSerializer
    parser_classes = (MultiPartParser, FormParser)
