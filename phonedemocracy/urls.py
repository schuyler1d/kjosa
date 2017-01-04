from django.conf import settings
from django.conf.urls import url
from django.contrib.admin.views.decorators import staff_member_required

from phonedemocracy.views.registration import RegisterVoter
from phonedemocracy.views.issues import list_issues
from phonedemocracy.views.twilioview import receive_sms_vote

urlpatterns = [
    #twilio setup
    url(r'^twilio/receive_text', receive_sms_vote),
    #public issues page
    url(r'^issues/(?P<district>\d+)', list_issues),
    #admin registration
    url(r'^official/newvoter', staff_member_required(RegisterVoter.as_view())),
]
