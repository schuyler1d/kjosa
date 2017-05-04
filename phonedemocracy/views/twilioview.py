import hashlib
import re

from django.shortcuts import render

from django_twilio.decorators import twilio_view
from twilio import twiml

from phonedemocracy.models import FailedAttemptLog, Issue, IssueVote, Voter


VOTE_PARSE_CMDS = {
    'x': 'issue_unencrypted',
    'v': 'vote_unencrypted',
    'p': 'password',
    'c': 'encrypted',
}
CMD_CHARS = ''.join(VOTE_PARSE_CMDS.keys())
for c in VOTE_PARSE_CMDS.keys():
    assert(c not in Voter.base25)

def parse_vote_body(text):
    """
    This is a forgiving parsing that depends on these options
    not being included in their values.
    See base25 in models.py which excludes them
    """
    rv = {}
    exclude = CMD_CHARS
    for k,v in VOTE_PARSE_CMDS.items():
        val = re.search(r'%s\W*([^%s\W]+)' % (v, exclude), text, re.I)
        if not val:
            val = re.search(r'%s\W*([^%s\W]+)' % (k, exclude), text, re.I)
        if val:
            rv[v] = re.sub(r'\W', '', val.groups()[0])
    return rv

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
    r = twiml.Response()
    phone_num = request.POST.get('From','')
    body = parse_vote_body(request.POST.get('Body', ''))

    message = "We received your sms voting message."
    ### TODO:
    ### 1. avoid timing attacks -- maybe just do hash + vote and encrypt for a queue
    if phone_num \
       and (set(['encrypted', 'password']).issubset(body.keys())):
        voter_hash = Voter.hash_phone_pw(phone_num, body['password'])
        ## TODO: Here, maybe just encrypt voter_hash + encrypted  and send to queue
        ## The rest below here would be in the queue processing code
        voter = Voter.objects.filter(phone_pw_hash=voter_hash).values('webpw_hash').first()
        if not voter:
            FailedAttemptLog.log(phone_num, FailedAttemptLog.BAD_PHONEPW)
        else:
            if 'encrypted' in body:
                webkey = Voter.inner_webhash_to_key(voter['webpw_hash'] , usebase64=True)
                try:
                    issue_id, vote = Voter.decode_encrypted_vote(webkey, code=body['encrypted'])
                    body['issue'] = issue_id
                    body['vote'] = vote
                except AssertionError:
                    #bad (possibly imposter) message
                    # TODO: should we still send message?
                    # If we do, then real voter is alerted to imposter
                    #    but then voter that gave (under durress) a fake webpasswd
                    FailedAttemptLog.log(phone_num, FailedAttemptLog.BAD_IV)
            if 'issue' in body:
                iss = Issue.objects.filter(pk=body['issue']).first()
                if not iss:
                    FailedAttemptLog.log(phone_num, FailedAttemptLog.BAD_ISSUE)
                else:
                    existing_vote = IssueVote.objects.filter(issue=iss,
                                                             voter_hash=voter_hash)
                    if existing_vote:
                        existing_vote.update(procon=int(body['vote']))
                    else:
                        IssueVote.objects.create(
                            issue=iss,
                            voter_hash=voter_hash,
                            procon=int(body['vote']),
                            shouldvote = 0,
                            validation_code='x')
    r.message(message)
    return r
"""
sample data
<QueryDict: {'NumSegments': ['1'], 'Body': ['Test555555'], 'FromCity': ['NEW YORK'], 'FromCountry': ['US'], 'SmsMessageSid': ['SM146dasdfasdf'], 'FromZip': ['10010'], 'SmsSid': ['SM146d3asdfasdfa'], 'ToZip': ['11222'], 'ToCountry': ['US'], 'From': ['+16461231234'], 'NumMedia': ['0'], 'AccountSid': ['asdfasdf'], 'ToState': ['NY'], 'ToCity': ['BROOKLYN'], 'To': ['+13471231234'], 'ApiVersion': ['2010-04-01'], 'MessageSid': ['SM146d3d'], 'FromState': ['NY'], 'SmsStatus': ['received']}>
"""


def receive_phone_vote(request):
    pass
