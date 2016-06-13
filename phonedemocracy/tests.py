from django.test import TestCase
from phonedemocracy.models import Voter

class EncryptionTestCase(TestCase):
    #def setUp(self):
    #    Animal.objects.create(name="lion", sound="roar")
    #    Animal.objects.create(name="cat", sound="meow")

    def test_speck_cipher(self):
        """symmetric encryption for texted votes"""
        
        enc = Voter.encode_encrypted_vote(key=50,
                                          issue_id=23, choice_id=3)
        dec = Voter.decode_encrypted_vote(key=50, code=enc)
        self.assertEqual(dec[0], 23)
        self.assertEqual(dec[1], 3)
