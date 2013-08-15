from django.conf.urls import patterns, include, url

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('melon.views',
	url(r'^$', 'register', name='home'),
	url(r'^accounts/login/$', 'login'),
	url(r'^accounts/logout/$', 'logout'),
	url(r'^my_account/', include('crawler.urls'))

    # Examples:
    # url(r'^$', 'melon.views.home', name='home'),
    # url(r'^melon/', include('melon.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # url(r'^admin/', include(admin.site.urls)),
)
