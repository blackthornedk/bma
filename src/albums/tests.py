"""Tests for the Album API."""
from django.urls import reverse
from oauth2_provider.models import get_access_token_model
from oauth2_provider.models import get_application_model
from oauth2_provider.models import get_grant_model
from utils.tests import ApiTestBase

Application = get_application_model()
AccessToken = get_access_token_model()
Grant = get_grant_model()


class TestAlbumsApi(ApiTestBase):
    """Test for API endpoints in the albums API."""

    def test_album_create(
        self,
        title: str = "album title here",
        description: str = "album description here",
        files: list[str] | None = None,
    ) -> None:
        """Test creating an album."""
        response = self.client.post(
            reverse("api-v1-json:album_create"),
            {
                "title": title,
                "description": description,
                "files": files if files else [],
            },
            headers={"authorization": self.curator6.auth},
            content_type="application/json",
        )
        assert response.status_code == 201
        self.album_uuid = response.json()["bma_response"]["uuid"]

    def test_album_create_with_files(
        self,
        title: str = "album title here",
        description: str = "album description here",
    ) -> None:
        """Test creating an album with files."""
        self.files = []
        for _ in range(10):
            self.files.append(self.file_upload())
        self.test_album_create(title=title, description=description, files=self.files)

    def test_album_update(self) -> None:
        """First replace then update."""
        self.test_album_create_with_files()
        # try with the wrong user
        response = self.client.put(
            reverse("api-v1-json:album_get", kwargs={"album_uuid": self.album_uuid}),
            {
                "title": "new title",
                "description": "description here",
                "files": self.files[0:2],
            },
            headers={"authorization": self.user0.auth},
            content_type="application/json",
        )
        assert response.status_code == 403

        # then with the correct user, check mode
        response = self.client.put(
            reverse("api-v1-json:album_get", kwargs={"album_uuid": self.album_uuid}) + "?check=true",
            {
                "title": "new title",
                "description": "description here",
                "files": self.files[0:2],
            },
            headers={"authorization": self.curator6.auth},
            content_type="application/json",
        )
        assert response.status_code == 202

        # then with the correct user
        response = self.client.put(
            reverse("api-v1-json:album_get", kwargs={"album_uuid": self.album_uuid}),
            {
                "title": "new title",
                "description": "description here",
                "files": self.files[0:2],
            },
            headers={"authorization": self.curator6.auth},
            content_type="application/json",
        )
        assert response.status_code == 200
        assert len(response.json()["bma_response"]["files"]) == 2
        assert response.json()["bma_response"]["title"] == "new title"
        assert response.json()["bma_response"]["description"] == "description here"

        # update the album with more files
        response = self.client.patch(
            reverse("api-v1-json:album_get", kwargs={"album_uuid": self.album_uuid}),
            {"files": self.files},
            headers={"authorization": self.curator6.auth},
            content_type="application/json",
        )
        assert response.status_code == 200
        assert len(response.json()["bma_response"]["files"]) == 10

        # update to remove all files
        response = self.client.patch(
            reverse("api-v1-json:album_get", kwargs={"album_uuid": self.album_uuid}),
            {"files": []},
            headers={"authorization": self.curator6.auth},
            content_type="application/json",
        )
        assert response.status_code == 200
        assert len(response.json()["bma_response"]["files"]) == 0

    def test_album_delete(self) -> None:
        """Test deleting an album."""
        self.test_album_create_with_files()

        # test with no auth
        response = self.client.delete(
            reverse("api-v1-json:album_get", kwargs={"album_uuid": self.album_uuid}),
        )
        assert response.status_code == 403

        # test with wrong auth
        response = self.client.delete(
            reverse("api-v1-json:album_get", kwargs={"album_uuid": self.album_uuid}),
            headers={"authorization": self.user0.auth},
        )
        assert response.status_code == 403

        # delete the album, check mode
        response = self.client.delete(
            reverse("api-v1-json:album_get", kwargs={"album_uuid": self.album_uuid}) + "?check=true",
            headers={"authorization": self.curator6.auth},
        )
        assert response.status_code == 202

        # delete the album
        response = self.client.delete(
            reverse("api-v1-json:album_get", kwargs={"album_uuid": self.album_uuid}),
            headers={"authorization": self.curator6.auth},
        )
        assert response.status_code == 204

    def test_album_get(self) -> None:
        """Get album metadata from the API."""
        self.test_album_create_with_files()
        response = self.client.get(
            reverse("api-v1-json:album_get", kwargs={"album_uuid": self.album_uuid}),
            headers={"authorization": self.curator6.auth},
        )
        assert response.status_code == 200

    def test_album_list(self) -> None:
        """Get album list from the API."""
        for i in range(10):
            self.test_album_create_with_files(title=f"album{i}")
        response = self.client.get(reverse("api-v1-json:album_list"), headers={"authorization": self.curator6.auth})
        assert response.status_code == 200
        assert len(response.json()["bma_response"]) == 10

        # test the file filter with files in different albums
        response = self.client.get(
            reverse("api-v1-json:album_list"),
            data={"files": [self.files[0], response.json()["bma_response"][1]["files"][0]]},
            headers={"authorization": self.curator6.auth},
        )
        assert response.status_code == 200
        assert len(response.json()["bma_response"]) == 0

        # test with files in the same album
        response = self.client.get(
            reverse("api-v1-json:album_list"),
            data={"files": [self.files[0], self.files[1]]},
            headers={"authorization": self.curator6.auth},
        )
        assert response.status_code == 200
        assert len(response.json()["bma_response"]) == 1

        # test search
        response = self.client.get(
            reverse("api-v1-json:album_list"), data={"search": "album4"}, headers={"authorization": self.curator6.auth}
        )
        assert response.status_code == 200
        assert len(response.json()["bma_response"]) == 1

        # test sorting
        response = self.client.get(
            reverse("api-v1-json:album_list"),
            data={"sorting": "created_desc"},
            headers={"authorization": self.curator6.auth},
        )
        assert response.status_code == 200
        assert len(response.json()["bma_response"]) == 10
        assert response.json()["bma_response"][0]["title"] == "album9"

        # test offset
        response = self.client.get(
            reverse("api-v1-json:album_list"),
            data={"sorting": "title_asc", "offset": 5},
            headers={"authorization": self.curator6.auth},
        )
        assert response.status_code == 200
        assert len(response.json()["bma_response"]) == 5
        assert response.json()["bma_response"][0]["title"] == "album5"
