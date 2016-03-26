from django.conf import settings
from django.conf.urls import url
from django.contrib.admin.views.decorators import staff_member_required

from phonedemocracy.views.registration import RegisterVoter

urlpatterns = [
    #twilio setup
    url(r'^twilio/receive_text', 'phonedemocracy.views.twilio.receive_sms_vote'),

    #issues
    url(r'^issues/(?P<district>\d+)', 'phonedemocracy.views.issues.list_issues'),

    url(r'^official/newvoter', staff_member_required(RegisterVoter.as_view())),
]
