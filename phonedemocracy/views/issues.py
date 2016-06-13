import re

from django.shortcuts import render
from django.conf import settings

from phonedemocracy.models import Issue

def sms_uri(request):
    user_agent = request.META['HTTP_USER_AGENT']
    delim = '?'
    if re.search(r'iPhone OS', user_agent):
        delim = '&'
        if re.search(r'iPhone OS [234567]', user_agent):
            delim = ';'
    return 'sms:%s%sbody=' % (settings.TWILIO_PHONENUMBER, delim)

## Issue pages
def list_issues(request, district):
    #also order-by/show vote count
    return render(request, 'phonedemocracy/issuelist.html', {
        'issues': Issue.objects.filter(district__id=int(district)).order_by('-status'),
        'sms_uri': sms_uri(request),
        'sms_number': settings.TWILIO_PHONENUMBER,
        'sms_number_friendly': settings.TWILIO_PHONENUMBER_FRIENDLY,
        'settings': {
            'VOTING_PUBLIC_SALT': settings.VOTING_PUBLIC_SALT,
            },
    })

def issue_detail(request):
    pass
