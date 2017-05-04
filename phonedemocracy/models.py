import base64
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
    * use cases:
       * changes number (uses web form with all their info to change it)
       * forgets password(s) -- TODO!!!!!
         (needs to keep guard against multiple registration)
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

    ##slowhash
    #BLOB
    phone_name_pw_hash = models.CharField(max_length=1024, db_index=True)

    ##slowhash
    # for getting info that Phone Co. should not know (e.g. anon vote value)
    # https://stackoverflow.com/questions/4915397/django-blob-model-field
    #BLOB
    webpw_hash = models.CharField(max_length=1024, db_index=True)

    # When people change their phones online, we increment this
    index = models.IntegerField(default=0)

    ##fasthash (because server is doing it)
    #for verifying a phone vote
    #BLOB
    phone_pw_hash = models.CharField(max_length=1024, db_index=True)

    @classmethod
    def b64(self, ary):
        return base64.encodestring(bytes(ary)).strip().decode('ascii')

    @classmethod
    def hash_phone_pw(cls, phone, pw):
        # use the public salt because it will be potentially exposed
        # at the registration terminals, but private salt will be used to wrap inner
        inner = cls.b64(cls.pbkdf2_cycle(
            ''.join([phone, pw]),
            settings.VOTING_PUBLIC_SALT, 1))
        return cls.hash_phone_pw_outer(phone, inner)

    @classmethod
    def hash_phone_pw_outer(cls, phone, inner_hash):
        myhmac = hmac.new(bytes(settings.VOTING_PRIVATE_SALT, 'utf-8'))
        myhmac.update(bytes(phone, 'utf-8'))
        myhmac.update(bytes(inner_hash, 'utf-8'))
        return myhmac.hexdigest()

    @classmethod
    def hash_registered_phonepwd(cls, webpasswd_halfhash):
        #TODO: remove this -- i don't think private salt can work for webpasswd hash
        # after all the client is going to encrypt it all client-side, so decryption
        # will need to be with that key (not the one on the server
        # it should be possible with the phone pw, though
        cls.pbkdf2_cycle(webpasswd_halfhash.encode('utf8'), settings.VOTING_PRIVATE_SALT)

    @classmethod
    def webpassword_to_symmetric_key(cls, webpass):
        """
        Not meant to be used on the server, but useful for testing.
        See templates/phonedemocracy/jslib.html webPasswordToSymmetricKey()
        """
        inner = cls.pbkdf2_cycle(webpass.encode('utf8'), settings.VOTING_PUBLIC_SALT, 4000)
        return cls.inner_webhash_to_key(bytes(inner), usebase64=False)

    @classmethod
    def inner_webhash_to_key(cls, webpw_hash, usebase64=True):
        webpw_inner_bytes = base64.decodestring(webpw_hash.encode('utf-8')) if usebase64 else webpw_hash
        outer = cls.pbkdf2_cycle(webpw_inner_bytes, settings.VOTING_TEMP_PUBLIC_SALT, 1000)
        return sum([a*(2**(8*(7-i))) for i,a in enumerate(outer)])

    @classmethod
    def pbkdf2_cycle(cls, password, salt, count):
        ## password should be encoded (e.g. .encode('utf8')) first
        if isinstance(password, str):
            password = password.encode('utf8')
        dk = hashlib.pbkdf2_hmac('sha256', password,
                                 salt.encode('utf8'), count)
        return [dk[i] for i in range(8)]

    # math.log(2**32, 25) < 7 characters
    # remove confusing chars: 1li, o0, s5
    # along with operation chars for message: x,v,p,c
    base25 = 'abdefghjkmnqrtuwyz2346789'
    assert(len(base25) == 25)

    speckparams = dict(key_size=64, block_size=32)
    @classmethod
    def decode_vote_code(cls, code):
        """
        code is 7char speck encrypted value
        with 32-bit encoding of the letters below (avoiding mistake values)
        """
        assert(len(code) == 7)
        code_checked = code.lower()
        int25s = [cls.base25.index(c) for c in code]
        codable_int = 0
        for i in range(len(code)):
            codable_int = codable_int + (25**i)*int25s[i]
        return codable_int

    @classmethod
    def decode_vote_int(cls, codable_int):
        iv = codable_int >> 24
        assert(iv == 0)
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
        iv = 0 #random.randint(0,255)
        codable_int = ((iv << 24) + (issue_id << 8) + choice_id)
        return codable_int

    @classmethod
    def encode_vote_int(cls, codable_int):
        char25s = []
        for i in range(7):
            char25s.append(cls.base25[codable_int % 25])
            codable_int = codable_int // 25
        return ''.join(char25s)

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
    ##slowhash
    ## at rest: state (and hackers) may see what phones are registered
    ## but should not be able to connect to votes
    #BLOB
    phone_hash = models.CharField(max_length=1024, db_index=True)


#class DeleteCode(models.Model):
#    """
#    Needed Protocol:
#    1. Voter lost phone(number) or web password or phone password
#       and goes 'back' to the DMV
#    2. How does system make sure the voter's original record is deleted/invalidated
#       so they can't vote twice by lying?
#    """
#    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

class FailedAttemptLog(models.Model):

    BAD_PHONEPW = 1
    BAD_IV = 2
    BAD_ISSUE = 3

    #store history of failed phone logins (wrong passwords, bad vote codes)
    created_at = models.DateTimeField(auto_now_add=True)
    ##fasthash: how do we avoid at-rest vulnerability here?
    #BLOB
    phone_hash = models.CharField(max_length=1024, db_index=True)
    failure = models.PositiveSmallIntegerField(choices=(
        (BAD_PHONEPW, 'bad phone/password match'),
        (BAD_IV, 'bad vote decode (bad iv or other assertion error)'),
        (BAD_ISSUE, 'bad vote code (no issue)'),
    ))

    @classmethod
    def hashphone(cls, phonenum):
        """
        if this kept the whole hash, then it would be laughably vulnerable
        Instead what we allow is a statistical analysis by the data collectors
        without identification. 1billion phone numbers (roughly) should have
        statistical equanimity from 2^20 ~ (16^5), but we should test this
        also, against aberations related to area codes like 646, etc
        """
        h = hashlib.sha256(phonenum.encode('utf8'))
        h.update(settings.VOTING_PRIVATE_SALT.encode('utf8'))
        return h.hexdigest()[:5]

    @classmethod
    def log(cls, phonenum, failure):
        return cls.objects.create(failure=failure,
                                  phone_hash=cls.hashphone(phonenum))


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
            (0, 'no preference'),
            (1, 'pro: force a vote'),
            (2, 'con: vote no'),
            (3, "don't vote on this"),
        )




class IssueVote(models.Model):
    #BLOB
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
