"""The BornHackSocialAccountAdapter takes care of populating fields in the BMA User model from the BornHack profile."""

from allauth.account.utils import user_field
from allauth.account.utils import user_username
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.socialaccount.models import SocialLogin
from django.conf import settings
from django.contrib.auth.models import Group
from django.forms import Form
from django.http import HttpRequest
from users.models import User


class BornHackSocialAccountAdapter(DefaultSocialAccountAdapter):
    """The allauth SocialAccountAdapter for BornHack populates the BMA User with data from the BornHack profile."""

    def is_open_for_signup(self, request: HttpRequest, sociallogin: SocialLogin) -> bool:
        """Always open for business."""
        return True

    def populate_user(self, request: HttpRequest, sociallogin: SocialLogin, data: dict[str, str]):  # type: ignore[no-untyped-def] # noqa: ANN201
        """Custom populate_user method to save our extra fields from the BornHack profile."""
        # set username on the user object
        user_username(sociallogin.user, data.get("username"))

        # set public_credit_name on the user object
        user_field(sociallogin.user, "public_credit_name", data.get("public_credit_name"))

        # set description on the user object
        user_field(sociallogin.user, "description", data.get("description"))

        return sociallogin.user

    def save_user(self, request: HttpRequest, sociallogin: SocialLogin, form: Form | None = None) -> User:
        """Called on first login with a BornHack socialaccount."""
        user = super().save_user(request, sociallogin, form)
        # add to curators group
        curators, created = Group.objects.get_or_create(name=settings.BMA_CURATOR_GROUP_NAME)
        curators.user_set.add(user)
        return user  # type: ignore[no-any-return]
