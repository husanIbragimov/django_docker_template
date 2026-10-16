import uuid

from django.db import models


class FilePath(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    path_name = models.CharField(max_length=128, blank=True, null=True)
    file = models.FileField(upload_to="uploads/")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "file_paths"

    def __str__(self):
        if not self.file:
            return f"{self.id}"
        return f"{self.file.name}"
