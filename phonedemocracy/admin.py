from django.contrib import admin

from phonedemocracy.models import Voter, VoterUnique, Issue, IssueVote, District

# Register your models here.
admin.site.register(District)
admin.site.register(Voter)
admin.site.register(VoterUnique)
admin.site.register(Issue)
admin.site.register(IssueVote)

