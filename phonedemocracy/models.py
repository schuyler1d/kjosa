from django.db import models
"""

Potential Attackers/Spies:

1. Phone Company:
   * will know:
       * password
       * phone number
       * identity (name and address) of phone owner
       * voting pattern (timing, how often)
   * could:
       * voter FRAUD
       * if voter uses insecure protocol, then, knows vote values
   * guards:
       * must be illegal (publicly exposed company)
       * some password is only for the website
       * possible vote validation
       * should not know server keys

2. System maintainers:
    * will know:
       * at vote-time: password, phonenumber, votevalue

    * guards:
       * should not know identity
       * must be illegal to store non-at-rest info (logs, etc)

3. Polling registration official
    * will know:
       * ?web password (printed out)
       * voter identity -- name
       * voter address
    * guards:
       * ?should not know phone number
         (user texts password in? -- what are we guarding here?)

4. Voters
    * will NOT know:
       * server private keys
    * guards:
       * registration/coordination in-person and with phone available
       * must be illegal to allow another to control/send vote for them
       * must be illegal to register 'twice'
       * unique VoterUnique address hash
"""

class District(models.Model):
    title = models.TextField()


class Voter(models.Model):
    #should district somehow be built in to the Voter hash?

    ##slowhash > 1seconds
    phone_name_pw_hash = models.CharField(max_length=1024, db_index=True) 

    ##slowhash > 1seconds
    webpw_phone_hash = models.CharField(max_length=1024, db_index=True) 

    # When people change their phones online, we increment this
    index = models.IntegerField() 

    ##fasthash (because server is doing it)
    phone_pw_hash = models.CharField(max_length=1024, db_index=True)


class VoterChangeLog(models.Model):
    #store history of previous phone-hashes
    #  maybe just enough to detect some kind of fraud/suspicious activity?
    created_at = models.DateTimeField(auto_now_add=True)
    ##fasthash: how do we avoid at-rest vulnerability here?
    phone_hash = models.CharField(max_length=1024, db_index=True)


class FailedAttemptLog(models.Model):
    #store history of failed phone logins (wrong passwords, bad vote codes)
    created_at = models.DateTimeField(auto_now_add=True)
    ##fasthash: how do we avoid at-rest vulnerability here?
    phone_hash = models.CharField(max_length=1024, db_index=True)
    failure_code = models.SmallPositiveInteger(choices=(
        (1, 'bad phone/password match'),
        (2, 'bad vote code'),
    ))


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
    status = models.SmallIntegerField()
    district = models.ManyToManyField(District, db_index=True)


class IssueVote(models.Model):
    voter_hash = models.CharField(max_length=1024, db_index=True)
    #TODO: can we anonymize this somehow? -- maybe the hash of the voter hash+issue id
    #   but that would be computationally easy to test with the at-rest data
    #   maybe along with the secret or a different mix: 
    #   we also don't want to give the voter 'extra votes' just by changing phone#'s
    #   at strategic moments
    #  non-changing vals: voter_id+issue+????
    #  if it's a slowhash, maybe this is a worthy expense to the system, since
    #   it's a legitimate vote
    procon = models.SmallIntegerField() #integer:could be weighted, etc
    shouldvote = models.SmallIntegerField() #boolean
    issue = models.ForeignKey(Issue, db_index=True)

    #eventually, this should include some cool homomorphic stuff
    # maybe it can even belay the pro/con and shouldvote values
    validation_code = models.TextField()
