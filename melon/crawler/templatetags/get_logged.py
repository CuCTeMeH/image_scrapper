from django.contrib.auth.models import User
from django.contrib.sessions.models import Session
from datetime import datetime
from django import template
from crawler.models import site_url, site_image
register = template.Library()

def get_all_logged_in_users():
    # Query all non-expired sessions
    sessions = Session.objects.filter(expire_date__gte=datetime.now())
    uid_list = []

    # Build a list of user ids from that query
    for session in sessions:
        data = session.get_decoded()
        uid_list.append(data.get('_auth_user_id', None))

    # Query all logged in users based on id list
    return User.objects.filter(id__in=uid_list)

def url_image_count(user):
	urls_count = site_url.objects.filter(user=user.id).count()
	return urls_count

def percentage_count(user):
	user_images_count = site_image.objects.filter(url__user=user.id).count()
	all_images_count = site_image.objects.all().count()
	all_users_count = User.objects.all().count()
	users = User.objects.all()
	if all_images_count == 0:
		return 0
	current_user_percentage = (100 * (float(user_images_count)/float(all_images_count)))
	counter = 0

	for u in users:
		user_images_count = site_image.objects.filter(url__user=u.id).count()
		user_percentage = (100 * (float(user_images_count)/float(all_images_count)))

		if user_percentage <= current_user_percentage:
			counter += 1

	percentage = (100 * (float(counter)/float(all_users_count)))
	return percentage

@register.inclusion_tag('logged_in_user_list.html')
def render_logged_in_user_list(user):
    return { 'logged_users': get_all_logged_in_users(),
    		 'urls_count': url_image_count(user),
    		 'percentage': percentage_count(user)
    		}