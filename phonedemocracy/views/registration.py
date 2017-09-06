from django.views.generic.edit import FormView
from django.conf import settings

from phonedemocracy.forms import VoterCreation, VoterRecord
from phonedemocracy.models import Voter, VoterUnique, InvalidToken


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
        voter_data = form.cleaned_data.copy()
        # TODO/ASSUMPTION: this is a proxy to the voter as unique.  It should be a hash of
        # unchangeable variables to the voter. name_birthday, maybe better?
        name_address_hash = voter_data.pop('name_address_hash')
        new_phone = voter_data.pop('new_phone')
        phone_pw_hash_inner = voter_data.pop('phone_pw_hash_inner', None)
        phone_pw_hash_outer = Voter.hash_phone_pw_outer(new_phone,
                                                        phone_pw_hash_inner)
        voter_data['phone_pw_hash'] = phone_pw_hash_outer

        invalidation_token = VoterUnique.generate_invalidation_token()
        voter_data['invalidation_token'] = invalidation_token
        invalidation_token_hash = InvalidToken.generate_invalidation_token_hash(
            invalidation_token, new_phone, voter_data['phone_pw_hash'])
        # TODO: success url/experience (for voter to verify number)
        v = Voter(**voter_data)
        v.save()
        vu = VoterUnique.objects.filter(name_address_hash=name_address_hash).first()
        if vu:
            #invalidate old token
            InvalidToken.objects.create(invalidation_token_hash=vu.invalidation_token_hash)
            vu.invalidation_token_hash = invalidation_token_hash
            vu.save()
        else:
            VoterUnique.objects.create(name_address_hash=name_address_hash,
                                       invalidation_token_hash=invalidation_token_hash)
        return super(RegisterVoter, self).form_valid(form)
