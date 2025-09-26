from django import forms
from .models import MyImage

class MyImageForm(forms.ModelForm):
    class Meta:
        model = MyImage
        # fields = ['title', 'image']
        fields = ['image']