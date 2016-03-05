from django.db import models


class Voter(models.Model):
    phone_name_pw_hash = None ##slowhash=1seconds
    index = None
    phone_pw_hash = None #fasthash (because server is doing it)
    
    pass


class VoterUnique(models.Model):
    name_address_hash = None #slowhash=5seconds


class IssueVote(models.Model):
    voter = None
    procon = None #integer
    shouldvote = None #boolean
    pass

class Issue(models.Model):
    url = None
    
