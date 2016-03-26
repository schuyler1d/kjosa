from django.shortcuts import render
from django.conf import settings

from phonedemocracy.models import Issue


## Issue pages
def list_issues(request, district):
    #also order-by/show vote count
    return render(request, 'phonedemocracy/issuelist.html', {
        'issues': Issue.objects.filter(district__id=int(district)).order_by('-status'),
        'sms_number': settings.TWILIO_PHONENUMBER,
        'sms_number_friendly': settings.TWILIO_PHONENUMBER_FRIENDLY,
    })

def issue_detail(request):
    pass
