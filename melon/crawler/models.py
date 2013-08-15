from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class site_url(models.Model):
	user = models.ForeignKey(
		User,
		on_delete=models.CASCADE
	)
	title = models.CharField(max_length=255)
	url = models.TextField()

def __unicode__(self):
	return self.url

class site_image(models.Model):
    url = models.ForeignKey(
    	site_url, 
    	on_delete=models.CASCADE
    )
    title = models.CharField(max_length=255)
    image_url = models.ImageField(upload_to='images',
    	max_length=255
    )

def __unicode__(self):
	return self.link