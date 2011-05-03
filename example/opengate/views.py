import datetime

from django.views.decorators.csrf import csrf_exempt

from tropo_webapi.views import TropoView

from .models import CallBox

ENTRY_CODE_GREETING = 'Please enter the entry code or press star to call residents.'
ENTRY_CODE_INVALID = 'Invalid entry code.'
CALL_TRANSFER = 'Calling residents.'
GATE_OPEN_MESSAGE = 'Someone just entered through your gate.'

class IncomingCallView(TropoView):
    def post(self, request, *args, **kwargs):
        self.call_box = CallBox.objects.get(id=self.session['to']['id'])
        return super(IncomingCallView, self).post(request, *args, **kwargs)

    def answer(self, request, *args, **kwargs):
        if self.call_box.auto_open:
            return self.open_gate(request)
        if self.call_box.entry_code:
            return self.ask_entry_code(request)
        return self.call_residents(request)

    def ask_entry_code(self, request, *args, **kwargs):
        self.ask('[4 DIGITS], call(*, star, call, call residents)', name='entry_code', say=ENTRY_CODE_GREETING, timeout=5, attempts=2)
        self.on('continue', callback=self.check_entry_code)
        self.on('incomplete', callback=self.call_residents)
        self.on('error', callback=self.call_residents)
        self.on('hangup', callback=self.hangup)
        return self.render_to_response()

    def check_entry_code(self, request, entry_code, *args, **kwargs):
        if str(entry_code['value']) == 'call':
            return self.call_residents(request)
        if int(entry_code['value']) == int(self.call_box.entry_code):
            return self.open_gate(request)
        self.say(ENTRY_CODE_INVALID)
        return self.ask_entry_code(request)

    def call_residents(self, request, *args, **kwargs):
        call_residents = self.call_box.residents.filter(active=True, by_sms=False).values_list('phone_number', flat=True)
        if call_residents:
            self.say(CALL_TRANSFER)
            self.transfer(to=map(str, call_residents), **{
                'from': self.call_box.id,
            })
        return self.render_to_response()

    def open_gate(self, request, *args, **kwargs):
        self.say(self.call_box.open_key_wav)
        for resident in self.call_box.residents.filter(active=True, entry_sms_alert=True):
            self.message(GATE_OPEN_MESSAGE, resident.phone_number, channel='TEXT')
        self.call_box.date_last_opened = datetime.datetime.now()
        return self.hangup(request)

    def hangup(self, request, *args, **kwargs):
        self.session.delete()
        super(IncomingCallView, self).hangup()
        return self.render_to_response()

call_incoming = csrf_exempt(IncomingCallView.as_view())
