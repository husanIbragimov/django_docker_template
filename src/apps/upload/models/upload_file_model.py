from django.db import models


class UploadFile(models.Model):
    path_name = models.CharField(max_length=128, blank=True, null=True)
    file = models.FileField(upload_to="uploads/")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        if not self.file:
            return f"{self.id}"
        return f"{self.file.name}"
