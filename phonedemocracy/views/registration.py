from django.views.generic.edit import FormView

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
        })
        return ctx

    def form_valid(self, form):
        #make sure doesn't match VoterUnique
        #otherwise
        # 1. save voter unique <- TODO
        # 2. save voter
        voter_data = form.cleaned_data.copy()
        voter_data.pop('name_address_hash', '')
        v = Voter(**voter_data)
        v.save()
        return super(RegisterVoter, self).form_valid(form)

