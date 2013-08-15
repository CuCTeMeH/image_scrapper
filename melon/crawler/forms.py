from django import forms
from crawler.models import site_url, site_image
from django.http import HttpResponse

class UrlForm(forms.Form):
    url = forms.URLField()