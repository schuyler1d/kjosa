from django.test import Client, TestCase, override_settings
from phonedemocracy.models import Voter
from django.contrib.auth.models import User

TEST_SETTINGS = {
    
}

@override_settings(**TEST_SETTINGS)
class EncryptionTestCase(TestCase):
    #def setUp(self):
    #    Animal.objects.create(name="lion", sound="roar")
    #    Animal.objects.create(name="cat", sound="meow")

    def setUp(self):
        self.c = Client()
        import os,binascii
        self.admin = User.objects.create(username='admintest', is_staff=True)
        self.admin_password = binascii.b2a_hex(os.urandom(15))
        self.admin.set_password(self.admin_password)
        self.admin.save()

    def test_speck_cipher(self):
        """symmetric encryption for texted votes"""
        
        enc = Voter.encode_encrypted_vote(key=50,
                                          issue_id=23, choice_id=3)
        dec = Voter.decode_encrypted_vote(key=50, code=enc)
        self.assertEqual(dec[0], 23)
        self.assertEqual(dec[1], 3)


    def test_register_voter(self):
        """
        This should replicate the logic in the client and submit a valid record
        """
        self.c.login(username='admintest', password=self.admin_password)

        from django.conf import settings

        name = 'John Doe'
        address = '123 Main Street, New York, NY 10025'
        phone = '+10005551234'
        webpassword = 'abc123'
        phonepassword = '1234'

        postdata = {
            'phone_name_pw_hash': Voter.pbkdf2_cycle(''.join([
                phone, name, webpassword
            ]), settings.VOTING_PUBLIC_SALT, 5000),
            'webpw_hash': Voter.pbkdf2_cycle(
                webpassword,
                settings.VOTING_PUBLIC_SALT, 4000),
            'phone_pw_hash': Voter.pbkdf2_cycle(''.join([
                phone, phonepassword
            ]), settings.VOTING_PUBLIC_SALT, 1),
            'new_phone': phone,
            'name_address_hash': Voter.pbkdf2_cycle(''.join([
                phone, name, address
            ]), settings.VOTING_PUBLIC_SALT, 5000),
        }
        result = self.c.post('/official/newvoter', postdata)

        self.assertEqual(result.status_code, 302)
        self.assertEqual(result.get('location'), '/thanks/')
        
