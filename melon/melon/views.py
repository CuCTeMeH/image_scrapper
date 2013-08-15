from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect
from django.contrib import auth
from django.views.generic import ListView
from django.core.context_processors import csrf
from django.contrib.auth.forms import UserCreationForm
import logging
logger = logging.getLogger('crawler')

def login(request):
	if request.method == 'POST':
		username = request.POST.get('username', '')
		password = request.POST.get('password', '')
		user = auth.authenticate(
			username=username,
			password=password
		)

		if user is not None:
			auth.login(request, user)
			logger.debug('User login: %s', user, extra={'user': user})
			return HttpResponseRedirect('/my_account')
		else:
			logger.debug('User not logged: %s', request.POST, extra={'user': request.POST})
			return HttpResponseRedirect('/')
	return HttpResponseRedirect('/')

def logout(request):
	logger.debug('User logout: %s', request.user, extra={'user': request.user})
	auth.logout(request)
	return HttpResponseRedirect('/')

def register(request):
	args = {}
	if request.user.is_authenticated():
		return HttpResponseRedirect('/my_account')
	if request.method == 'POST':
		form = UserCreationForm(request.POST)
		if form.is_valid():
			form.save()
			logger.debug('User registrated: %s', request.POST, extra={'user': request.POST})
			args['registered'] = request.POST.get('username', '')
		else:
			args['error'] = form.errors
		
	args.update(csrf(request))
	args['current_path'] = request.get_full_path()
	args['form'] = UserCreationForm()
	return render_to_response('register.html', args)