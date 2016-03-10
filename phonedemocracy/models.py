from django.db import models


class Voter(models.Model):
    ##slowhash > 1seconds
    phone_name_pw_hash = models.CharField(max_length=1024, db_index=True) 

    # When people change their phones online, we increment this
    index = models.IntegerField() 

    ##fasthash (because server is doing it)
    phone_pw_hash = models.CharField(max_length=1024, db_index=True)


class VoterUnique(models.Model):
    """
    Canonical verified voter, but this needs to be
    encrypted a bunch of times by a bunch of trusted people's
    private keys that are unlikely to conspire
    """
    name_address_hash = models.TextField()


class Issue(models.Model):
    url = models.URLField()
    title = models.TextField()    

class IssueVote(models.Model):
    voter = models.ForeignKey(Voter)
    procon = models.IntegerField() #integer
    shouldvote = models.IntegerField() #boolean
    issue = models.ForeignKey(Issue, db_index=True)
