from django.conf import settings
from django.conf.urls import url
#from phonedemocracy.views.twilio import receive_sms_vote

urlpatterns = [
    #twilio setup
    url(r'^twilio/receive_text', 'phonedemocracy.views.twilio.receive_sms_vote'),

    #issues
    url(r'^issues/(?P<district>\d+)', 'phonedemocracy.views.issues.list_issues'),
]
