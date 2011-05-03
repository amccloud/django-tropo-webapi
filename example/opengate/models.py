import datetime

from django.db import models
from django.contrib.auth.models import User

OPEN_KEY_CHOICES = tuple((str(n), str(n)) for n in range(10)) + (('p', '#'), ('s', '*'))
OPEN_KEY_CHOICES_DEFAULT = '9'

class Resident(models.Model):
    name = models.CharField(max_length=128, blank=True, null=True)
    phone_number = models.CharField(max_length=10)
    by_sms = models.BooleanField(default=False, help_text='Get gate request only by SMS.')
    entry_sms_alert = models.BooleanField(default=True, help_text='Get alerted by SMS when the gate is opened.')
    active = models.BooleanField(default=True)

    def __unicode__(self):
        if self.name:
            return self.name
        return self.phone_number

class CallBox(models.Model):
    id = models.CharField(max_length=10, primary_key=True, db_index=True, verbose_name='Phone number')
    open_key = models.CharField(max_length=1, choices=OPEN_KEY_CHOICES, default=OPEN_KEY_CHOICES_DEFAULT, help_text='Touch tone key assigned to open gate.')
    auto_open = models.BooleanField(default=False, help_text='Automtically open gate when called.')
    entry_code = models.CharField(max_length=4, blank=True, null=True, help_text='4 digit code given to expected guest to open gate.')
    residents = models.ManyToManyField(Resident, related_name='call_boxes', blank=True, null=True)
    user = models.OneToOneField(User, related_name='call_box')
    date_created = models.DateTimeField(default=datetime.datetime.now)
    date_last_opened = models.DateTimeField(blank=True, null=True)
    date_last_missed = models.DateTimeField(blank=True, null=True)

    @property
    def phone_number(self):
        pn = str(self.id)
        return '(%s) %s-%s' % (pn[:3], pn[3:6], pn[6:10])

    @property
    def open_key_wav(self):
        return 'http://www.dialabc.com/i/cache/dtmfgen/wavpcm8.300/%s.wav' % (self.open_key,)

    def __unicode__(self):
        return self.id

class CallBoxEvent(models.Model):
    call_box = models.ForeignKey(CallBox, related_name='events')
    resident = models.ForeignKey(Resident, related_name='call_box_events', blank=True, null=True)
    event_type = models.CharField(max_length=128)
    date_created = models.DateTimeField(default=datetime.datetime.now)
