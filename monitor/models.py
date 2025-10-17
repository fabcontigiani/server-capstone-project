from django.db import models

# Create your models here.
class MyImage(models.Model):
    # title = models.CharField(max_length=100)
    image = models.ImageField(upload_to='images/')
    created_at = models.DateTimeField(auto_now_add=True)

    processed_image = models.ImageField(upload_to='processed_images/', null=True, blank=True)
    metadata = models.JSONField(null=True, blank=True)

    class Meta:
        ordering = ['created_at']

    # def __str__(self):
    #     return self.title