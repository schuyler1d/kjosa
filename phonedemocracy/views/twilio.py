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
    print request
    r = twiml.Response()
    r.message('Thanks for the SMS message!')
    return r
    

    

def receive_phone_vote(request):
    pass
