"""Unit tests base class."""
import base64
import hashlib
import json
import logging
import secrets
import string
from pathlib import Path
from urllib.parse import parse_qs
from urllib.parse import urlsplit

from django.conf import settings
from django.contrib.auth.models import Group
from django.test import Client
from django.test import TestCase
from django.urls import reverse
from oauth2_provider.models import get_access_token_model
from oauth2_provider.models import get_application_model
from oauth2_provider.models import get_grant_model
from users.factories import UserFactory

Application = get_application_model()
AccessToken = get_access_token_model()
Grant = get_grant_model()


class ApiTestBase(TestCase):
    """The base class used by all api tests."""

    @classmethod
    def setUpTestData(cls) -> None:
        """Test setup."""
        # disable logging
        logging.disable(logging.CRITICAL)
        cls.client = Client(enforce_csrf_checks=True)

        # create 2 regular users, 2 creators, 2 moderators, 2 curators, and 1 superuser
        for i in range(9):
            kwargs = {}
            if i in [0, 1]:
                kwargs["username"] = f"user{i}"
            elif i in [2, 3]:
                kwargs["username"] = f"creator{i}"
            elif i in [4, 5]:
                kwargs["username"] = f"moderator{i}"
            elif i in [6, 7]:
                kwargs["username"] = f"curator{i}"
            elif i == 8:
                kwargs["username"] = "superuser"
                kwargs["is_superuser"] = True
                kwargs["is_staff"] = True
            user = UserFactory.create(**kwargs)
            user.set_password("secret")
            user.save()
            setattr(cls, user.username, user)
            # create oauth application
            cls.application = Application.objects.create(
                name="Test Application",
                redirect_uris="https://example.com/noexist/callback/",
                user=user,
                client_type=Application.CLIENT_PUBLIC,
                authorization_grant_type=Application.GRANT_AUTHORIZATION_CODE,
                client_id=f"client_id_{user.username}",
                client_secret="client_secret",
                skip_authorization=True,
            )
            user.auth = cls.get_access_token(user)
            user.save()
            cls.client.logout()

        # create groups and add users
        creators = Group.objects.create(name=settings.BMA_CREATOR_GROUP_NAME)
        creators.user_set.add(cls.creator2, cls.creator3)
        moderators = Group.objects.create(name=settings.BMA_MODERATOR_GROUP_NAME)
        moderators.user_set.add(cls.moderator4, cls.moderator5)
        curators = Group.objects.create(name=settings.BMA_CURATOR_GROUP_NAME)
        curators.user_set.add(cls.curator6, cls.curator7)

    @classmethod
    def get_access_token(cls, user) -> str:  # noqa: ANN001
        """Test the full oauth2 public client authorization code pkce token flow."""
        # generate a verifier string from 43-128 chars
        alphabet = string.ascii_uppercase + string.digits
        code_verifier = "".join(secrets.choice(alphabet) for i in range(43 + secrets.randbelow(86)))
        code_verifier_base64 = base64.urlsafe_b64encode(code_verifier.encode("utf-8"))
        code_challenge = hashlib.sha256(code_verifier_base64).digest()
        code_challenge_base64 = base64.urlsafe_b64encode(code_challenge).decode("utf-8").replace("=", "")

        # this requires login
        cls.client.force_login(user)

        # get the authorization code
        data = {
            "client_id": f"client_id_{user.username}",
            "state": "something",
            "redirect_uri": "https://example.com/noexist/callback/",
            "response_type": "code",
            "allow": True,
            "code_challenge": code_challenge_base64,
            "code_challenge_method": "S256",
        }
        response = cls.client.get("/o/authorize/", data=data)
        assert response.status_code == 302
        assert "Location" in response.headers
        result = urlsplit(response.headers["Location"])
        qs = parse_qs(result.query)
        assert "code" in qs

        # the rest doesn't require login
        cls.client.logout()

        # get the access token
        response = cls.client.post(
            "/o/token/",
            {
                "grant_type": "authorization_code",
                "code": qs["code"],
                "redirect_uri": "https://example.com/noexist/callback/",
                "client_id": f"client_id_{user.username}",
                "code_verifier": code_verifier_base64.decode("utf-8"),
            },
        )
        assert response.status_code == 200
        user.tokeninfo = json.loads(response.content)
        return f"Bearer {user.tokeninfo['access_token']}"

    def file_upload(  # noqa: PLR0913
        self,
        *,
        uploader: str = "creator2",
        filepath: str = settings.BASE_DIR / "static_src/images/logo_wide_black_500_RGB.png",
        title: str = "some title",
        file_license: str = "CC_ZERO_1_0",
        attribution: str = "fotoarne",
        original_source: str = "https://example.com/something.png",
        thumbnail_url: str = "",
        return_full: bool = False,
        expect_status_code: int = 201,
    ) -> str | dict[str, str]:
        """The upload method used by many tests."""
        metadata = {
            "title": title,
            "license": file_license,
            "attribution": attribution,
            "original_source": original_source,
        }
        if thumbnail_url:
            metadata["thumbnail_url"] = thumbnail_url
        with Path(filepath).open("rb") as f:
            response = self.client.post(
                reverse("api-v1-json:upload"),
                {
                    "f": f,
                    "metadata": json.dumps(metadata),
                },
                headers={"authorization": getattr(self, uploader).auth},
            )
        assert response.status_code == expect_status_code
        if expect_status_code == 422:
            return None
        data = response.json()["bma_response"]
        assert "uuid" in data
        if not title:
            title = Path(filepath).name
        assert data["title"] == title
        assert data["attribution"] == attribution
        assert data["license"] == file_license
        assert data["source"] == original_source
        self.file_uuid = data["uuid"]
        if return_full:
            return data
        return data["uuid"]
