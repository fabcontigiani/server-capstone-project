from django.db import models

# Create your models here.
class MyImage(models.Model):
    mac_address = models.CharField(max_length=17)
    image = models.ImageField(upload_to='images/')
    created_at = models.DateTimeField(auto_now_add=True)

    processed_image = models.ImageField(upload_to='processed_images/', null=True, blank=True)
    metadata = models.JSONField(null=True, blank=True)

    class Meta:
        ordering = ['created_at']

class MacTelegramRelation(models.Model):
    mac_address = models.CharField(max_length=17, unique=True)
    telegram_chat_id = models.BigIntegerField()

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']