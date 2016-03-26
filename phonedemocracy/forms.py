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

