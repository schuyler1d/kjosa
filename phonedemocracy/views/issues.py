import re

from django.shortcuts import render, get_object_or_404
from django.conf import settings

from phonedemocracy.models import Issue, District, Voter

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
    assert(settings.VOTING_PUBLIC_SALT)
    assert(settings.VOTING_PUBLIC_SALT != settings.VOTING_TEMP_PUBLIC_SALT)

    return render(request, 'phonedemocracy/issuelist.html', {
        'district': get_object_or_404(District, id=int(district)),
        'issues': Issue.objects.filter(district__id=int(district)).order_by('-status'),
        'sms_uri': sms_uri(request),
        'sms_number': settings.TWILIO_PHONENUMBER,
        'sms_number_friendly': settings.TWILIO_PHONENUMBER_FRIENDLY,
        'settings': {
            'VOTING_PUBLIC_SALT': settings.VOTING_PUBLIC_SALT,
            'VOTING_TEMP_PUBLIC_SALT': settings.VOTING_TEMP_PUBLIC_SALT,
            'BASE25': Voter.base25,
            },
    })

def issue_detail(request):
    pass
