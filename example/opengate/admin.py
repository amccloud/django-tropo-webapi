from django.contrib import admin

from .models import CallBox, Resident, CallBoxEvent

admin.site.register([CallBox, Resident, CallBoxEvent])
