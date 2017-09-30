import base64

from django.contrib.auth.models import User
from django.test import Client, TestCase, override_settings
from speck import SpeckCipher

from phonedemocracy.models import FailedAttemptLog, IssueVote, Voter
from phonedemocracy.views.twilioview import parse_vote_body

TEST_SETTINGS = {
    'VOTING_PUBLIC_SALT': 'public salt forever',
    'VOTING_TEMP_PUBLIC_SALT': 'a public salt today',
    'VOTING_PRIVATE_SALT': 'private salt',
    'DJANGO_TWILIO_FORGERY_PROTECTION': False
}

class VoterInfo:
    def __init__(self, **kwargs):
        for k,v in kwargs.items():
            setattr(self, k, v)

    def postdata(self):
        from django.conf import settings
        def b64(ary):
            return base64.encodestring(bytes(ary)).strip().decode('ascii')

        rv = {
            'phone_name_pw_hash': b64(Voter.pbkdf2_cycle(''.join([
                self.phone, self.name, self.webpassword
            ]), settings.VOTING_PUBLIC_SALT, 5000)),
            'webpw_hash': b64(Voter.pbkdf2_cycle(
                self.webpassword,
                settings.VOTING_PUBLIC_SALT, 4000)),
            'phone_pw_hash_inner': b64(Voter.pbkdf2_cycle(''.join([
                self.phone, self.phonepassword
            ]), settings.VOTING_PUBLIC_SALT, 1)),
            'new_phone': self.phone,
            'name_address_hash': b64(Voter.pbkdf2_cycle(''.join([
                self.phone, self.name, self.address
            ]), settings.VOTING_PUBLIC_SALT, 5000)),
        }
        return rv


@override_settings(**TEST_SETTINGS)
class EncryptionTestCase(TestCase):

    def test_speck_cipher(self):
        """symmetric encryption for texted votes"""
        enc = Voter.encode_encrypted_vote(key=50,
                                          issue_id=23, choice_id=3)
        dec = Voter.decode_encrypted_vote(key=50, code=enc)
        self.assertEqual(dec[0], 23)
        self.assertEqual(dec[1], 3)

    def test_cipher_encrypt(self):
        def sixteenbit2int(ary):
            return sum([a*(2**(16*(3-i))) for i,a in enumerate(ary)])
        key = [0,0,0,50]
        x = SpeckCipher(50, **Voter.speckparams).encrypt(0)
        self.assertEqual(x % 65536, 26980)
        self.assertEqual(int(x / 65536), 4565)
        key2 = [50, 0, 0, 50]
        x = SpeckCipher(sixteenbit2int(key2), **Voter.speckparams).encrypt(0)
        self.assertEqual(x % 65536, 11425)
        self.assertEqual(int(x / 65536), 6628)


@override_settings(**TEST_SETTINGS)
class VotingTestCase(TestCase):

    fixtures = ['test_fixture_district']

    def setUp(self):
        self.admin_client = Client()
        self.c = Client()
        import os,binascii
        self.admin = User.objects.create(username='admintest', is_staff=True)
        self.admin_password = binascii.b2a_hex(os.urandom(15))
        self.admin.set_password(self.admin_password)
        self.admin.save()
        self.v1 = VoterInfo(name='John Doe',
                            address='123 Main Street, New York, NY 10025',
                            phone='+10005551234',
                            webpassword='abc123',
                            phonepassword='1234')

    def test_register_voter(self):
        """
        This should replicate the logic in the client and submit a valid record
        """
        self.admin_client.login(username='admintest', password=self.admin_password)

        result = self.admin_client.post('/official/newvoter', self.v1.postdata())
        self.assertEqual(result.status_code, 302)
        self.assertEqual(result.get('location'), '/thanks/')
        
    def test_voting_voter(self):
        v1 = self.v1
        pre = IssueVote.objects.count()
        self.test_register_voter()
        key = Voter.webpassword_to_symmetric_key(v1.webpassword)
        code = Voter.encode_encrypted_vote(key=key,
                                           issue_id=1, choice_id=2)
        res = self.c.post('/twilio/receive_text', {
            'From': v1.phone,
            'Body': 'c{} p{}'.format(code, v1.phonepassword)
        })
        self.assertEqual(IssueVote.objects.count(), pre+1)

    def test_badwebpw(self):
        v1 = self.v1
        pre = IssueVote.objects.count()
        self.test_register_voter()
        badkey = Voter.webpassword_to_symmetric_key('xjunkjunk')
        code = Voter.encode_encrypted_vote(key=badkey,
                                           issue_id=2, choice_id=1)
        res = self.c.post('/twilio/receive_text', {
            'From': v1.phone,
            'Body': 'c{} p{}'.format(code, v1.phonepassword)
        })

        # We don't want BAD_IVs to fail anymore since then the same message is distinguishable
        #self.assertEqual(FailedAttemptLog.objects.filter(failure=FailedAttemptLog.BAD_IV).count(), 1)
        # no additional vote should be registered
        self.assertEqual(IssueVote.objects.count(), pre)

    def test_luckybadwebpw(self):
        """This tests when the symmetric key luckily yields an iv=0 (1/16 chance)"""
        v1 = self.v1
        pre = IssueVote.objects.count()
        self.test_register_voter()
        badkey = Voter.webpassword_to_symmetric_key('junkjunk')
        code = Voter.encode_encrypted_vote(key=badkey,
                                           issue_id=2, choice_id=1)
        res = self.c.post('/twilio/receive_text', {
            'From': v1.phone,
            'Body': 'c{} p{}'.format(code, v1.phonepassword)
        })
        self.assertEqual(FailedAttemptLog.objects.filter(failure=FailedAttemptLog.BAD_ISSUE).count(),
                         1)
        self.assertEqual(IssueVote.objects.count(), pre)

    def test_badphonepw(self):
        v1 = self.v1
        pre = IssueVote.objects.count()
        self.test_register_voter()
        key = Voter.webpassword_to_symmetric_key(v1.webpassword)
        code = Voter.encode_encrypted_vote(key=key,
                                           issue_id=2, choice_id=1)
        assert(v1.phonepassword != '6666')
        res = self.c.post('/twilio/receive_text', {
            'From': v1.phone,
            'Body': 'c{} p{}'.format(code, '6666')
        })
        self.assertEqual(FailedAttemptLog.objects.filter(failure=FailedAttemptLog.BAD_PHONEPW).count(),
                         1)
        self.assertEqual(IssueVote.objects.count(), pre)

    def test_changevote(self):
        v1 = self.v1
        pre = IssueVote.objects.count()
        self.test_register_voter()
        key = Voter.webpassword_to_symmetric_key(v1.webpassword)
        code1 = Voter.encode_encrypted_vote(key=key,
                                            issue_id=1, choice_id=1)
        code2 = Voter.encode_encrypted_vote(key=key,
                                            issue_id=1, choice_id=2)
        res = self.c.post('/twilio/receive_text', {
            'From': v1.phone,
            'Body': 'c{} p{}'.format(code1, v1.phonepassword)
        })
        res2 = self.c.post('/twilio/receive_text', {
            'From': v1.phone,
            'Body': 'c{} p{}'.format(code2, v1.phonepassword)
        })
        self.assertEqual(IssueVote.objects.count(), pre+1)
        self.assertEqual(IssueVote.objects.first().procon, 2)


@override_settings(**TEST_SETTINGS)
class SMSParsingTestCase(TestCase):

    def test_parsing(self):
        messages = [
            'c4567 p1234',
            'c:4567 p1234',
            'c 4567 p 1234',
            'c 4567 password 1234',
            'c4567 password:1234',
        ]
        for m in messages:
            x = parse_vote_body(m)
            self.assertEqual(x['password'], '1234')
            self.assertEqual(x['encrypted'], '4567')
