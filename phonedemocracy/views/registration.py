from django.views.generic.edit import FormView
from django.conf import settings

from phonedemocracy.forms import VoterCreation, VoterRecord
from phonedemocracy.models import Voter, VoterUnique


class RegisterVoter(FormView):
    template_name = 'phonedemocracy/staff/registervoter.html'
    form_class = VoterRecord
    success_url = '/thanks/'

    def get_context_data(self, **kwargs):
        ctx = super(RegisterVoter, self).get_context_data(**kwargs)
        ctx.update({
            'datainputform': VoterCreation(),
            'settings': {
                'VOTING_PUBLIC_SALT': settings.VOTING_PUBLIC_SALT,
            },
        })
        return ctx

    def form_valid(self, form):
        #make sure doesn't match VoterUnique
        #make sure ?doesn't match VoterChangeLog (or figure out how to cancel previous reverse)
        #otherwise
        # 1. save voter unique <- TODO
        # 2. save voter
        voter_data = form.cleaned_data.copy()
        name_address_hash = voter_data.pop('name_address_hash')
        new_phone = voter_data.pop('new_phone')
        old_phone = voter_data.pop('old_phone', None)
        old_index = voter_data.pop('old_index', None)
        phone_pw_hash_inner = voter_data.pop('phone_pw_hash_inner', None)
        voter_data['phone_pw_hash'] = Voter.hash_phone_pw_outer(new_phone,
                                                                phone_pw_hash_inner)
        ##TODO:
        ## 1. add VOTING_PRIVATE_SALT to phone password
        ## 2. success url/experience (for voter to verify number)
        ## 3. old phone
        v = Voter(**voter_data)
        v.save()
        return super(RegisterVoter, self).form_valid(form)

