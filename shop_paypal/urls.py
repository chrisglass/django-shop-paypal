#-*- coding: utf-8 -*-
''' A normal URLs file, like you would do for any Django application. '''
from django.conf.urls.defaults import patterns, url

ulrpatterns = patterns('',
    url(r'^$', my_view),
)