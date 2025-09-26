from django.db import models

# Create your models here.
class MyImage(models.Model):
    # title = models.CharField(max_length=100)
    image = models.ImageField(upload_to='images/')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    # def __str__(self):
    #     return self.title