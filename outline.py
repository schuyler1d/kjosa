"""
pseudocode
"""


######
# twilio interactions
######

def receive_sms_vote(request):
    pass


######
# web public user
######

def change_phone(request):
    #needs javascript/client proof-of-work
    # (name +oldphone + pw) + new phone + POW
    #  texts oldphone
    #  texts newphone
    pass

def get_vote_options(request, model, obj_id):
    #for a particular issue, how do you send a message
    # with symmetric encrypt
    # also needs javascript proof-of-work
    # http://www.bennolan.com/2011/04/28/proof-of-work-in-js.html
    pass

## Issue pages
def list_issues(request):
    #also order-by/show vote count
    pass

def issue_detail(request):
    pass

#####
# admin polling location
#####

def setup_voter(request):
    # protect against same voter multi-registration
    # push phone
    # send sms confirmation to user

    #1. staff enteres: (full name + district + staff pw)
    #2. user enters phone #
    #3. system -> password (which was auto-random-generated)
    pass


def create_issue(request):
    pass


"""
data model notes (not sure if good):

2way(
  hmac( name + phone, state_secret )
  +index
  + (phone + pw)
)

how do we stop folks from creating multiple registrations?
  -- is this an issue?
  hash(name + district + phone) 
    indexes to something that decrypts with password
    
"""
