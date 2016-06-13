import hashlib
import hmac
import random
import uuid

from django.db import models
from django.conf import settings

from speck import SpeckCipher
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

    def __str__(self):
        return self.title


class Voter(models.Model):
    #to avoid sequential analysis
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    #should district be obscured further inside one of the hashes?
    #district = models.ForeignKey(District)

    ##slowhash > 1seconds
    phone_name_pw_hash = models.CharField(max_length=1024, db_index=True) 

    ##slowhash > 1seconds
    # for getting info that Phone Co. should not know (e.g. anon vote value)
    webpw_hash = models.CharField(max_length=1024, db_index=True)

    # When people change their phones online, we increment this
    index = models.IntegerField(default=0)

    ##fasthash (because server is doing it)
    #for verifying a phone vote
    #currently sha256 (but no seed, and not hmac)
    #TODO: add those.
    phone_pw_hash = models.CharField(max_length=1024, db_index=True)

    @classmethod
    def hash_phone_pw2(cls, phone, pw):
        myhmac = hmac.new(bytes(settings.VOTING_PUBLIC_SALT, 'utf-8'))
        myhmac.update(bytes(phone, 'utf-8'))
        myhmac.update(bytes(pw, 'utf-8'))
        return myhmac.hexdigest()

    @classmethod
    def hash_phone_pw(cls, phone, pw):
        return hashlib.sha256(bytes('%s%s' % (phone, pw), 'utf-8')).hexdigest()


    base31 = 'abcdefghjkmnpqrstuvwxyz23456789'
    speckparams = dict(key_size=64, block_size=32)
    @classmethod
    def decode_vote_code(cls, code):
        """
        code is 7char speck encrypted value
        with 32-bit encoding of the letters below (avoiding mistake values)
        """
        assert(len(code) == 7)
        code_checked = code.lower()
        int31s = [cls.base31.index(c) for c in code]
        codable_int = 0
        for i in range(7):
            codable_int = codable_int + (31**i)*int31s[i]
        return codable_int

    @classmethod
    def decode_vote_int(cls, codable_int):
        iv = codable_int >> 24
        codable_int = codable_int - (iv << 24)
        issue_id = codable_int >> 8
        choice_id = codable_int - (issue_id << 8)
        return (issue_id, choice_id)

    @classmethod
    def encode_vote_code(cls, issue_id, choice_id):
        """
        issue_id: 16-bit positive integer
        choice_id: 8-bit positive integer
        preserve remaining 8 bits for 'IV' or other goals
        """
        assert(issue_id < 65536)
        assert(choice_id < 256)
        iv = random.randint(0,255)
        codable_int = ((iv << 24) + (issue_id << 8) + choice_id)
        return codable_int

    @classmethod
    def encode_vote_int(cls, codable_int):
        char31s = []
        for i in range(7):
            char31s.append(cls.base31[codable_int % 31])
            codable_int = codable_int // 31
        return ''.join(char31s)

    @classmethod
    def decode_encrypted_vote(cls, key, code):
        """
        key is 64bit (converted from webpasswd)
        """
        cipher = SpeckCipher(key, **cls.speckparams)
        encrypted_int = cls.decode_vote_code(code)
        vote_int = cipher.decrypt(encrypted_int)
        return cls.decode_vote_int(vote_int)

    @classmethod
    def encode_encrypted_vote(cls, key, issue_id, choice_id):
        """
        In practice, this will be implemented in Javascript
        but this is the inverse of decode_encrypted_vote()
        """
        cipher = SpeckCipher(key, **cls.speckparams)
        codable_int = cls.encode_vote_code(issue_id, choice_id)
        encrypted_int = cipher.encrypt(codable_int)
        return cls.encode_vote_int(encrypted_int)

                      
class VoterUnique(models.Model):
    """
    Canonical verified voter, but this needs to be
    encrypted a bunch of times by a bunch of trusted people's
    private keys that are unlikely to conspire
    """
    #to avoid sequential analysis
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name_address_hash = models.TextField()


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
    failure_code = models.PositiveSmallIntegerField(choices=(
        (1, 'bad phone/password match'),
        (2, 'bad vote code'),
    ))


class Issue(models.Model):
    url = models.URLField()
    title = models.TextField()
    shortcode= models.CharField(max_length=10)
    status = models.SmallIntegerField(default=0)
    district = models.ManyToManyField(District, db_index=True)

    def __str__(self):
        return '%s (%s)' % (self.title, self.shortcode)

    def choices(self):
        return (
            (0, 'null (no preference)'),
            (1, 'pro: force a vote'),
            (2, 'con: vote no'),
            (3, "don't vote on this"),
        )




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
