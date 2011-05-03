from django.conf.urls.defaults import patterns, url

urlpatterns = patterns('opengate.views',
    url(r'call/$', 'call_incoming', name='call_incoming'),
)
