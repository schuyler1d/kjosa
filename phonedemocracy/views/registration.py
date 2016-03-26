from django.contrib.admin.views.decorators import staff_member_required

from django.views.generic.edit import FormView


class RegisterVoter(FormView):
    template_name = 'phonedemocracy/staff/register.html'
    form_class = None #TheForm
    success_url = '/thanks/'

    def form_valid(self, form):
        #make sure doesn't match VoterUnique
        #otherwise
        # 1. save voter unique
        # 2. save voter

        form.send_email()
        return super(ChangePhone, self).form_valid(form)


