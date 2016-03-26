from django.views.generic.edit import FormView

from phonedemocracy.forms import VoterCreation, VoterRecord

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
        # 1. save voter unique
        # 2. save voter

        form.send_email()
        return super(ChangePhone, self).form_valid(form)


