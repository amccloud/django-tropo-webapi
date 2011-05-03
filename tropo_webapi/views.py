import tropo

from django.http import HttpResponse
from django.views.generic import View
from django.utils.importlib import import_module
from django.conf import settings

class TropoJSONResponse(HttpResponse):
    def __init__(self, tropo):
        self.tropo = tropo
        super(TropoJSONResponse, self).__init__(tropo.RenderJson(), mimetype='application/json')

class TropoResponseMixin(tropo.Tropo):
    response_class = TropoJSONResponse

    def render_to_response(self):
        return self.response_class(tropo=self)

class TropoView(TropoResponseMixin, View):
    result = None

    def dispatch(self, request, *args, **kwargs):
        try:
            session_engine = import_module(settings.SESSION_ENGINE)
            tropo_session = tropo.Session(request.raw_post_data).dict
            session_key = tropo_session.get('id', None)
            if session_key:
                self.session = session_engine.SessionStore(session_key)
                self.session.save(must_create=True)
                self.session.update(tropo_session)
                self.session.set_expiry(60 * 5)
                self.session.save()
        except:
            try:
                self.result = tropo.Result(request.raw_post_data)
                session_engine = import_module(settings.SESSION_ENGINE)
                actions = getattr(self.result, '_actions', [])
                if (type(actions) is dict):
                    actions = [actions]
                for action in actions:
                    kwargs[str(action['name'])] = action
                self.session = session_engine.SessionStore(self.result._sessionId)
            except:
                pass
        return super(TropoView, self).dispatch(request, *args, **kwargs)

    def on(self, event, callback=None, **options):
        next = '%s?__action__=%s' % (settings.TROPO_CALL_URL, callback.__name__)
        return super(TropoView, self).on(event, next=next, **options)

    def post(self, request, *args, **kwargs):
        action = request.GET.get('__action__', 'answer')
        handler = getattr(self, action, self.http_method_not_allowed)
        return handler(request, *args, **kwargs)

    def answer(self, request, *args, **kwargs):
        raise NotImplementedError
