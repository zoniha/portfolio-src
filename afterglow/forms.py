from django import forms
from django.http import HttpResponse
from django.core.mail import EmailMessage, send_mail, BadHeaderError
from django.conf import settings


class PhotoForm(forms.Form):
    image = forms.ImageField(widget=forms.FileInput(attrs={'class':'custom-file-input'}))
