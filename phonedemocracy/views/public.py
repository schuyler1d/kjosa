from django.shortcuts import render
from django.views.generic.edit import FormView


class ChangePhone(FormView):
    template_name = 'change_phone.html'
    form_class = None #TheForm
    success_url = '/thanks/'

    def form_valid(self, form):
        #called when valid form data has bee posted

        #needs javascript/client proof-of-work
        # (name +oldphone + pw) + new phone + POW
        #  texts oldphone
        #  texts newphone

        form.send_email()
        return super(ChangePhone, self).form_valid(form)


def get_vote_options(request, model, obj_id):
    #for a particular issue, how do you send a message
    # with 'symmetric encrypt' -- or something just hard to guess
    # also needs javascript proof-of-work
    # http://www.bennolan.com/2011/04/28/proof-of-work-in-js.html
    pass


def print_out_at_votinglocation(request):
    #gives the web password and instructions to user
    #
    pass

