import urllib2, re
import logging
import os, glob
from urllib2 import urlparse
from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect, HttpResponse
from django.contrib import auth
from django.core.context_processors import csrf
from crawler.models import site_url, site_image
from django.contrib.auth.decorators import login_required
from crawler.forms import UrlForm
from bs4 import BeautifulSoup
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.core.files import File
from django.core.files.temp import NamedTemporaryFile

logger = logging.getLogger('crawler')

#render my account page
@login_required
def my_account(request):
	args = {}
	args.update(csrf(request))
	images = site_image.objects.filter(url__user=request.user.id).prefetch_related()
	paginator = Paginator(images, 10)
	user = request.user

	page = request.GET.get('page')
	try:
	    site_images = paginator.page(page)
	except PageNotAnInteger:
	    site_images = paginator.page(1)
	except EmptyPage:
	    site_images = paginator.page(paginator.num_pages)
	
	args['images'] = site_images
	args['form'] = UrlForm()
	args['user'] = request.user
	return render_to_response('my_account.html', args)

#crawl the images. Maybe best is to separate this function in two or three but for now ...
@login_required
def crawl(request):
	if request.method == 'POST':
		form = UrlForm(request.POST)
		if form.is_valid():
			post_url = request.POST.get('url', '')
			domain = urlparse.urlsplit(post_url)
			domain_url = domain.scheme + '://' + domain.netloc +  '/'
			
			try:
				source = urllib2.urlopen(post_url)
			except:
				logger.exception('URLopen can`t open the url')
				return HttpResponseRedirect('/my_account')

			logger.debug('Fetching images from url: %s', post_url)
			
			soup = BeautifulSoup(source)
			page_title_fb = soup.find("meta",
				{"property":"og:title"}
			)
			page_title_tw = soup.find("meta",
				{"name":"twitter:title"}
			)

			if page_title_fb and not page_title_tw:
				page_title = page_title_fb['content']
			elif page_title_tw and not page_title_fb:
				page_title = page_title_tw['content']
			else:
				page_title = soup.title.string
			
			page_title = page_title.encode('utf-8')

			try:
				site = site_url.objects.get(
					user=request.user,
					url=post_url
				)

				if site:
					delete_side_by_id(site.id)
					site.user = request.user
					site.title = page_title
					site.url = post_url
					try:
						site.save()
					except Exception, e:
						logger.exception('Site url problem')
						return HttpResponseRedirect('/my_account')
			except Exception, e:
				site = site_url(
					user=request.user, 
					title=page_title, 
					url=post_url
				)
				try:
					site.save()
				except Exception, e:
					logger.exception('Site url problem')
					return HttpResponseRedirect('/my_account')

			allowed_exts = ('png', 'jpg', 'gif', 'bmp')
			images_fb = soup.findAll("meta",
				{"property":"og:image"})
			meta_images_urls = []
			if images_fb:
				for img in images_fb:
					if img.get('content') is not None:
						if img.get('content').rsplit('.')[-1] in allowed_exts:
							db_img = site_image(
								url=site
							)

							try:
								img_filename = img.get('content').split('/')[-1]

								img_temp = NamedTemporaryFile(
									dir='/media/D/virtual_env/bin/melon/melon/static/',
									delete=True
								)

								img_temp.write(urllib2.urlopen(urlparse.urljoin(
									domain_url, 
									img.get('content')
								)).read())

								img_temp.flush()

								db_img.image_url.save(img_filename, File(img_temp))

								db_img.save()
							except Exception, e:
								logger.exception('Saving images from facebook')
								continue

							meta_images_urls.append(
								img.get('content')
							)

			images_tw = soup.find("meta",
				{"name":"twitter:image"}
			)
			if images_tw:
				for img in images_tw:
					if meta_images_urls and img.get('content'):
						if any(img.get('content') in s for s in meta_images_urls):
							continue

					if img.get('content') is not None:
						if img.get('content').rsplit('.')[-1] in allowed_exts:
							db_img = site_image(
								url=site
							)

							try:
								img_filename = img.get('content').split('/')[-1]

								img_temp = NamedTemporaryFile(delete=True)

								img_temp.write(urllib2.urlopen(urlparse.urljoin(
									domain_url, 
									img.get('content')
								)).read())

								img_temp.flush()

								db_img.image_url.save(img_filename, File(img_temp))

								db_img.save()
							except Exception, e:
								logger.exception('Saving images from twitter')
								continue

							meta_images_urls.append(
								img.get('content')
							)
				
			page_imgs = soup.findAll('img')
			if page_imgs:
				for img in page_imgs:
					if meta_images_urls and img.get('src'):
						if any(img.get('src') in s for s in meta_images_urls):
							continue
					if img.get('src') is not None:
						if img.get('src').rsplit('.')[-1] in allowed_exts:
							db_img = site_image(
								url=site
							)

							try:
								img_filename = img.get('src').split('/')[-1]
								
								img_temp = NamedTemporaryFile(delete=True)
								
								img_temp.write(urllib2.urlopen(urlparse.urljoin(
									domain_url, 
									img.get('src')
								)).read())
								
								img_temp.flush()
								db_img.image_url.save(img_filename,
									File(img_temp),
									save=True
								)
								db_img.save()
							except Exception, e:
								logger.exception('Saving images after the images from tw and fb')
								pass

	return HttpResponseRedirect('/my_account')

#delete a site by id not by request.
def delete_side_by_id(site_id):
	site_entry = site_url.objects.get(
		id=site_id
	)

	image_entries = site_image.objects.filter(
		url_id=site_entry
	)

	for image_entry in image_entries:
		delete_image_files(image_entry)

	try:
		site_entry.delete()
	except e:
		logger.exception('Deleting site entry')
	return True

#delete a whole site with the images.
@login_required
def delete_site(request):
	if request.method == 'GET':
		site_id = request.GET.get('id', '')
		site_entry = site_url.objects.get(
			id=site_id
		)

		image_entries = site_image.objects.filter(
			url_id=site_entry
		)

		for image_entry in image_entries:
			delete_image_files(image_entry)

		try:
			site_entry.delete()
		except e:
			logger.exception('Deleting site entry')
		return HttpResponseRedirect('/my_account')

# Take care of the files that are resized from image tag.
def delete_image_files(entry):
	for filename in glob.glob(
		"/media/D/virtual_env/bin/melon/melon/static/images/resized/" 
		+ entry.image_url.url.split('/')[-1].split('.')[0] 
		+ '*'
	):
		os.remove(filename)
	return 1

#delete a single image.
@login_required
def delete_image(request):
	if request.method == 'GET':
		url_id = request.GET.get('id', '')
		image_entry = site_image.objects.get(
			id=url_id
		)

		try:
			delete_image_files(image_entry)
			image_entry.delete()
		except Exception, e:
			logger.exception('Deleting site entry ')
		return HttpResponseRedirect('/my_account')

#render the gallery page with pagination
@login_required
def gallery(request):
	site_list = site_url.objects.filter(user=request.user)
	paginator = Paginator(site_list, 10)
	user = request.user

	page = request.GET.get('page')
	try:
	    site_urls = paginator.page(page)
	except PageNotAnInteger:
	    site_urls = paginator.page(1)
	except EmptyPage:
	    site_urls = paginator.page(paginator.num_pages)

	return render_to_response('gallery.html', {
		"site_urls": site_urls,
		"user": user
		}
	)

#render the inner gallery with modal popups
@login_required
def gallery_inner(request):
	if request.method == 'GET':
		url_id = request.GET.get('id', '')
		user = request.user
		images_lists = site_image.objects.filter(url=url_id)
		return render_to_response('gallery_inner.html', {
			"images_lists": images_lists,
			"user": user
			}
		)