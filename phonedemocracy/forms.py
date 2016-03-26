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
    phone_name_pw_hash = forms.CharField(max_length=1024) 

    ##slowhash > 1seconds
    # for getting info that Phone Co. should not know (e.g. anon vote value)
    webpw_hash = forms.CharField(max_length=1024)

    ##fasthash (because server is doing it)
    #for verifying a phone vote
    phone_pw_hash = forms.CharField(max_length=1024)
    

    ###
    # VoterUnique fields
    ###
    name_address_hash = forms.CharField()
