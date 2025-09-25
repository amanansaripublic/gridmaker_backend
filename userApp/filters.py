


from customCalsses.BaseFilterSet import BaseFilterSet

from .models import UserDetailsModel

class UserDetailsModelFilterSet(BaseFilterSet):
    class Meta:
        model = UserDetailsModel
        fields = "__all__"