from django.conf import settings
from django.conf.urls import url
#from phonedemocracy.views.twilio import receive_sms_vote

urlpatterns = [
    url(r'^twilio/receive_text', 'phonedemocracy.views.twilio.receive_sms_vote'),
]
