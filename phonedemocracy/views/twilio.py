from django.shortcuts import render

from django_twilio.decorators import twilio_view
from twilio import twiml

@twilio_view
def receive_sms_vote(request):
    # * validate voter
    # * validate vote text:
    #      1. if 1 or 0 
    #      2. if a coded vote, figure out which option it was
    # * store vote
    # * sms back the user with some verification code?
    #   if they chose #1 let them know they can do so more anonymously if
    #     they also have access to the web
    print (request.POST)
    r = twiml.Response()
    
    if '6467' in request.POST.get('From',''):
        r.message("Hello XXXX")
    else:
        r.message('Thanks for the SMS message! -sky')
    return r
    
"""
sample data
<QueryDict: {'NumSegments': ['1'], 'Body': ['Test555555'], 'FromCity': ['NEW YORK'], 'FromCountry': ['US'], 'SmsMessageSid': ['SM146dasdfasdf'], 'FromZip': ['10010'], 'SmsSid': ['SM146d3asdfasdfa'], 'ToZip': ['11222'], 'ToCountry': ['US'], 'From': ['+16461231234'], 'NumMedia': ['0'], 'AccountSid': ['asdfasdf'], 'ToState': ['NY'], 'ToCity': ['BROOKLYN'], 'To': ['+13471231234'], 'ApiVersion': ['2010-04-01'], 'MessageSid': ['SM146d3d'], 'FromState': ['NY'], 'SmsStatus': ['received']}>
"""
    

def receive_phone_vote(request):
    pass
