import base64

from django.contrib.auth.models import User
from django.test import Client, TestCase, override_settings
from speck import SpeckCipher

from phonedemocracy.models import Voter, IssueVote
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
    """
    postdata returns:
{'webpw_hash': [180, 137, 129, 20, 181, 113, 147, 135], 'name_address_hash': [119, 176, 13, 160, 104, 66, 81, 104], 'phone_pw_hash': [102, 91, 9, 24, 164, 107, 159, 221], 'new_phone': '+10005551234', 'phone_name_pw_hash': [70, 247, 50, 139, 149, 89, 155, 93]}
    """


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
        self.admin_client.login(username='admintest', password=self.admin_password)
        self.admin_client.post('/official/newvoter', v1.postdata())

        key = Voter.webpassword_to_symmetric_key(v1.webpassword)
        code = Voter.encode_encrypted_vote(key=key,
                                           issue_id=1, choice_id=2)
        res = self.c.post('/twilio/receive_text', {
            'From': v1.phone,
            'Body': 'c{} p{}'.format(code, v1.phonepassword)
        })
        self.assertEqual(IssueVote.objects.count(), 1)

    def test_badphonepw(self):
        v1 = self.v1
        badkey = Voter.webpassword_to_symmetric_key('junkjunk')
        code = Voter.encode_encrypted_vote(key=badkey,
                                           issue_id=2, choice_id=1)
        res = self.c.post('/twilio/receive_text', {
            'From': v1.phone,
            'Body': 'c{} p{}'.format(code, v1.phonepassword)
        })

    def test_badwebpw(self):
        v1 = self.v1
        key = Voter.webpassword_to_symmetric_key(v1.webpassword)
        code = Voter.encode_encrypted_vote(key=key,
                                           issue_id=2, choice_id=1)
        assert(v1.phonepassword != '6666')
        res = self.c.post('/twilio/receive_text', {
            'From': v1.phone,
            'Body': 'c{} p{}'.format(code, '6666')
        })

    def test_changevote(self):
        v1 = self.v1
        key = Voter.webpassword_to_symmetric_key(v1.webpassword)
        code = Voter.encode_encrypted_vote(key=key,
                                           issue_id=1, choice_id=1)
        res = self.c.post('/twilio/receive_text', {
            'From': v1.phone,
            'Body': 'c{} p{}'.format(code, v1.phonepassword)
        })


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
