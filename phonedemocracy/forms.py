import re

from django import forms

class VoterCreation(forms.Form):

    #election official enters:
    full_name = forms.CharField()
    address = forms.CharField()

    #voter enters:
    phone = forms.CharField()
    phone_password = forms.CharField()

    #system generates:
    web_password = forms.CharField()

class VoterRecord(forms.Form):

    ###
    # Voter fields
    ###
    ##slowhash > 1seconds
    phone_name_pw_hash = forms.CharField(max_length=1024) 

    ##slowhash > 1seconds
    # for getting info that Phone Co. should not know (e.g. anon vote value)
    webpw_hash = forms.CharField(max_length=1024)

    ##fasthash (because server is doing it)
    #for verifying a phone vote
    phone_pw_hash_inner = forms.CharField(max_length=1024)

    ###
    # VoterChangeLog fields
    ###
    # Staff machine should send the phone number in plain text because:
    # 1. We can store the phone hash in VoterUnique and verify that staff are not
    # creating fake phone number-name pairs
    # 2. Server already exposed to phone numbers incoming from twilio -- just doesn't let them stay 'at rest'
    # 3. However server shouldn't receive it with identity information
    #will be slowhash'd on server
    new_phone = forms.CharField(max_length=12)

    #old_phone = forms.CharField(max_length=12, required=False)
    #old_index = forms.IntegerField(required=False)

    ###
    # VoterUnique fields
    ###
    name_address_hash = forms.CharField()

    def clean_new_phone(self, val=None):
        phone = val or self.cleaned_data.get('new_phone')
        if not phone:
            return phone
        phone = re.sub(r'[^\d+]', '', phone)
        if len(phone) != 12:
            raise ValidationError("Please include a 10-digit phone number prefixed by +1")
        return phone

    def xclean(self):
        old_phone = self.cleaned_data.get('old_phone')
        old_index = self.cleaned_data.get('old_index')
        if old_phone or old_index \
           and not (old_phone and old_index):
            raise ValidationError("Either both old phone and old index are required or neither")
        return self.cleaned_data
