"""Tests for the files API."""
from pathlib import Path

from django.urls import reverse
from oauth2_provider.models import get_access_token_model
from oauth2_provider.models import get_application_model
from oauth2_provider.models import get_grant_model
from utils.tests import ApiTestBase

from .models import BaseFile

Application = get_application_model()
AccessToken = get_access_token_model()
Grant = get_grant_model()


class TestFilesApi(ApiTestBase):
    """Test for methods in the files API."""

    def test_api_auth_bearer_token(self) -> None:
        """Test getting a token."""
        response = self.client.get("/o/authorized_tokens/", headers={"authorization": self.user1.auth})
        assert response.status_code == 200
        assert "revoke" in response.content.decode("utf-8")

    def test_api_auth_get_refresh_token(self) -> None:
        """Test getting a refresh token."""
        response = self.client.post(
            "/o/token/",
            {
                "grant_type": "refresh_token",
                "client_id": f"client_id_{self.user1.username}",
                "refresh_token": self.user1.tokeninfo["refresh_token"],
            },
        )
        assert response.status_code == 200
        assert "refresh_token" in response.json()

    def test_api_auth_django_session(self) -> None:
        """Test getting authorised tokens."""
        self.client.force_login(self.user1)
        response = self.client.get("/o/authorized_tokens/")
        assert response.status_code == 200
        assert "revoke" in response.content.decode("utf-8")

    def test_file_upload(self) -> None:
        """Test file upload cornercases."""
        data = self.file_upload(title="", return_full=True)
        assert data["title"] == data["original_filename"]
        self.file_upload(file_license="notalicense", expect_status_code=422)
        self.file_upload(thumbnail_url="/foo/wrong.tar", expect_status_code=422)

    def test_file_list(self) -> None:  # noqa: PLR0915
        """Test the file_list endpoint."""
        files = [self.file_upload(title=f"title{i}") for i in range(15)]
        response = self.client.get(reverse("api-v1-json:file_list"), headers={"authorization": self.user1.auth})
        assert response.status_code == 200
        assert len(response.json()["bma_response"]) == 15

        # test sorting
        response = self.client.get(
            reverse("api-v1-json:file_list"),
            data={"limit": 5, "sorting": "title_asc"},
            headers={"authorization": self.user1.auth},
        )
        assert len(response.json()["bma_response"]) == 5
        assert response.json()["bma_response"][0]["title"] == "title0"
        assert response.json()["bma_response"][1]["title"] == "title1"
        assert response.json()["bma_response"][2]["title"] == "title10"
        assert response.json()["bma_response"][4]["title"] == "title12"
        response = self.client.get(
            reverse("api-v1-json:file_list"),
            data={"limit": 1, "sorting": "created_desc"},
            headers={"authorization": self.user1.auth},
        )
        assert response.json()["bma_response"][0]["title"] == "title14"

        # test offset
        response = self.client.get(
            reverse("api-v1-json:file_list"),
            data={"offset": 5, "sorting": "created_asc"},
            headers={"authorization": self.user1.auth},
        )
        assert response.json()["bma_response"][0]["title"] == "title5"
        assert response.json()["bma_response"][4]["title"] == "title9"

        # test owner filter
        response = self.client.get(
            reverse("api-v1-json:file_list"),
            data={"owners": [self.user1.uuid, self.user2.uuid]},
            headers={"authorization": self.user1.auth},
        )
        assert len(response.json()["bma_response"]) == 15
        response = self.client.get(
            reverse("api-v1-json:file_list"),
            data={"owners": [self.user2.uuid]},
            headers={"authorization": self.user1.auth},
        )
        assert len(response.json()["bma_response"]) == 0

        # test search
        response = self.client.get(
            reverse("api-v1-json:file_list"), data={"search": "title7"}, headers={"authorization": self.user1.auth}
        )
        assert len(response.json()["bma_response"]) == 1
        assert response.json()["bma_response"][0]["title"] == "title7"

        # create an album with some files
        response = self.client.post(
            reverse("api-v1-json:album_create"),
            {
                "title": "album title here",
                "files": files[3:6],
            },
            headers={"authorization": self.user1.auth},
            content_type="application/json",
        )
        assert response.status_code == 201
        self.album_uuid = response.json()["bma_response"]["uuid"]

        # test album filter
        response = self.client.get(
            reverse("api-v1-json:file_list"),
            data={"albums": [self.album_uuid]},
            headers={"authorization": self.user1.auth},
        )
        assert len(response.json()["bma_response"]) == 3

        # create another empty album
        response = self.client.post(
            reverse("api-v1-json:album_create"),
            {
                "title": "another album title here",
            },
            headers={"authorization": self.user1.auth},
            content_type="application/json",
        )
        assert response.status_code == 201
        uuid = response.json()["bma_response"]["uuid"]

        # test filtering for multiple albums
        response = self.client.get(
            reverse("api-v1-json:file_list"),
            data={"albums": [self.album_uuid, uuid]},
            headers={"authorization": self.user1.auth},
        )
        assert len(response.json()["bma_response"]) == 3

        # test file size filter
        response = self.client.get(
            reverse("api-v1-json:file_list"), data={"size": 9478}, headers={"authorization": self.user1.auth}
        )
        assert len(response.json()["bma_response"]) == 15

        # test file size_lt filter
        response = self.client.get(
            reverse("api-v1-json:file_list"), data={"size_lt": 10000}, headers={"authorization": self.user1.auth}
        )
        assert len(response.json()["bma_response"]) == 15
        response = self.client.get(
            reverse("api-v1-json:file_list"), data={"size_lt": 1000}, headers={"authorization": self.user1.auth}
        )
        assert len(response.json()["bma_response"]) == 0

        # test file size_gt filter
        response = self.client.get(
            reverse("api-v1-json:file_list"), data={"size_gt": 10000}, headers={"authorization": self.user1.auth}
        )
        assert len(response.json()["bma_response"]) == 0
        response = self.client.get(
            reverse("api-v1-json:file_list"), data={"size_gt": 1000}, headers={"authorization": self.user1.auth}
        )
        assert len(response.json()["bma_response"]) == 15

        # test file type filter
        response = self.client.get(
            reverse("api-v1-json:file_list"),
            data={"filetypes": ["picture"]},
            headers={"authorization": self.user1.auth},
        )
        assert len(response.json()["bma_response"]) == 15
        response = self.client.get(
            reverse("api-v1-json:file_list"),
            data={"filetypes": ["audio", "video", "document"]},
            headers={"authorization": self.user1.auth},
        )
        assert len(response.json()["bma_response"]) == 0

        # test file license filter
        response = self.client.get(
            reverse("api-v1-json:file_list"),
            data={"licenses": ["CC_ZERO_1_0"]},
            headers={"authorization": self.user1.auth},
        )
        assert len(response.json()["bma_response"]) == 15
        response = self.client.get(
            reverse("api-v1-json:file_list"),
            data={"licenses": ["CC_BY_4_0", "CC_BY_SA_4_0"]},
            headers={"authorization": self.user1.auth},
        )
        assert len(response.json()["bma_response"]) == 0

    def test_file_list_permissions(self) -> None:
        """Test various permissions stuff for the file_list endpoint."""
        files = [self.file_upload(title=f"title{i}") for i in range(15)]

        # no files should be visible
        response = self.client.get(reverse("api-v1-json:file_list"), headers={"authorization": self.user2.auth})
        assert response.status_code == 200
        assert len(response.json()["bma_response"]) == 0

        # the superuser can see all files
        response = self.client.get(reverse("api-v1-json:file_list"), headers={"authorization": self.superuser.auth})
        assert response.status_code == 200
        assert len(response.json()["bma_response"]) == 15

        # attempt to publish a file before approval
        response = self.client.patch(
            reverse("api-v1-json:publish_file", kwargs={"file_uuid": files[0]}),
            headers={"authorization": self.user1.auth},
        )
        assert response.status_code == 403

        # approve the file without permission
        response = self.client.patch(
            reverse("api-v1-json:approve_file", kwargs={"file_uuid": files[0]}),
            headers={"authorization": self.user1.auth},
        )
        assert response.status_code == 403

        # approve the file, check mode
        response = self.client.patch(
            reverse("api-v1-json:approve_file", kwargs={"file_uuid": files[0]}) + "?check=true",
            headers={"authorization": self.superuser.auth},
        )
        assert response.status_code == 202

        # really approve the file
        response = self.client.patch(
            reverse("api-v1-json:approve_file", kwargs={"file_uuid": files[0]}),
            headers={"authorization": self.superuser.auth},
        )
        assert response.status_code == 200

        # try again with wrong status
        response = self.client.patch(
            reverse("api-v1-json:approve_file", kwargs={"file_uuid": files[0]}),
            headers={"authorization": self.superuser.auth},
        )
        assert response.status_code == 403

        # now list UNPUBLISHED files
        response = self.client.get(
            reverse("api-v1-json:file_list"),
            data={"statuses": ["UNPUBLISHED"]},
            headers={"authorization": self.user1.auth},
        )
        assert len(response.json()["bma_response"]) == 1

        # publish a file, check mode
        response = self.client.patch(
            reverse("api-v1-json:publish_file", kwargs={"file_uuid": files[0]}) + "?check=true",
            headers={"authorization": self.user1.auth},
        )
        assert response.status_code == 202

        # publish the file
        response = self.client.patch(
            reverse("api-v1-json:publish_file", kwargs={"file_uuid": files[0]}),
            headers={"authorization": self.user1.auth},
        )
        assert response.status_code == 200

        # make sure someone else can see it
        response = self.client.get(reverse("api-v1-json:file_list"), headers={"authorization": self.user2.auth})
        assert response.status_code == 200
        assert len(response.json()["bma_response"]) == 1

        # make sure anonymous can see it
        response = self.client.get(
            reverse("api-v1-json:file_list"),
        )
        assert response.status_code == 200
        assert len(response.json()["bma_response"]) == 1

        # unpublish the file without permission
        response = self.client.patch(
            reverse("api-v1-json:unpublish_file", kwargs={"file_uuid": files[0]}),
            headers={"authorization": self.user2.auth},
        )
        assert response.status_code == 403

        # unpublish the file, check mode
        response = self.client.patch(
            reverse("api-v1-json:unpublish_file", kwargs={"file_uuid": files[0]}) + "?check=true",
            headers={"authorization": self.user1.auth},
        )
        assert response.status_code == 202

        # unpublish the file
        response = self.client.patch(
            reverse("api-v1-json:unpublish_file", kwargs={"file_uuid": files[0]}),
            headers={"authorization": self.user1.auth},
        )
        assert response.status_code == 200

        # make sure it is not visible anymore
        response = self.client.get(reverse("api-v1-json:file_list"), headers={"authorization": self.user2.auth})
        assert response.status_code == 200
        assert len(response.json()["bma_response"]) == 0

        # make sure it is not visible anymore to anonymous
        response = self.client.get(
            reverse("api-v1-json:file_list"),
        )
        assert response.status_code == 200
        assert len(response.json()["bma_response"]) == 0

    def test_metadata_get(self) -> None:
        """Get file metadata from the API."""
        self.file_upload()
        response = self.client.get(
            reverse("api-v1-json:file_get", kwargs={"file_uuid": self.file_uuid}),
            headers={"authorization": self.user1.auth},
        )
        assert response.status_code == 200
        assert "uuid" in response.json()["bma_response"]
        assert response.json()["bma_response"]["uuid"] == self.file_uuid

    def test_file_download(self) -> None:
        """Test downloading a file after uploading it."""
        self.file_upload()
        metadata = self.client.get(reverse("api-v1-json:file_list"), headers={"authorization": self.user1.auth}).json()[
            "bma_response"
        ][0]
        url = metadata["links"]["downloads"]["original"]
        # try download of unpublished file without auth
        response = self.client.get(url)
        assert response.status_code == 403
        # try again with auth
        self.client.force_login(self.user1)
        response = self.client.get(url)
        assert response.status_code == 200
        assert response["content-type"] == "image/png"
        with Path("static_src/images/logo_wide_black_500_RGB.png").open("rb") as f:
            assert f.read() == response.getvalue()

    def test_file_metadata_update(self) -> None:
        """Replace and then update file metadata."""
        self.file_upload()
        response = self.client.get(
            reverse("api-v1-json:file_get", kwargs={"file_uuid": self.file_uuid}),
            headers={"authorization": self.user1.auth},
        )
        assert response.status_code == 200
        original_metadata = response.json()["bma_response"]
        updates = {
            "title": "some title",
            "description": "some description",
            "license": "CC_ZERO_1_0",
            "attribution": "some attribution",
            "thumbnail_url": "/media/foo/bar.png",
        }

        # update with no auth
        response = self.client.put(
            reverse("api-v1-json:file_get", kwargs={"file_uuid": self.file_uuid}),
            updates,
            content_type="application/json",
        )
        assert response.status_code == 403

        # update with wrong user
        response = self.client.put(
            reverse("api-v1-json:file_get", kwargs={"file_uuid": self.file_uuid}),
            updates,
            headers={"authorization": f"Bearer {self.user2.tokeninfo['access_token']}"},
            content_type="application/json",
        )
        assert response.status_code == 403

        # update the file, check mode
        response = self.client.put(
            reverse("api-v1-json:file_get", kwargs={"file_uuid": self.file_uuid}) + "?check=true",
            updates,
            headers={"authorization": self.user1.auth},
            content_type="application/json",
        )
        assert response.status_code == 202

        # replace the file metadata
        response = self.client.put(
            reverse("api-v1-json:file_get", kwargs={"file_uuid": self.file_uuid}),
            updates,
            headers={"authorization": self.user1.auth},
            content_type="application/json",
        )
        assert response.status_code == 200
        original_metadata.update(updates)
        for k, v in response.json()["bma_response"].items():
            # "updated" will have changed of course,
            if k == "updated":
                assert v != original_metadata[k]
            # and "source" was initially set but not specified in the PUT call,
            # so it should be blank now, so it should return the files detail url
            elif k == "source":
                assert v == original_metadata["links"]["html"]
            # everything else should be the same
            else:
                assert v == original_metadata[k]

        # try with an invalid thumbnail url
        response = self.client.put(
            reverse("api-v1-json:file_get", kwargs={"file_uuid": self.file_uuid}),
            {"thumbnail_url": "/wrong/value.tiff"},
            headers={"authorization": self.user1.auth},
            content_type="application/json",
        )
        assert response.status_code == 422

        # update instead of replace, first with invalid source url
        response = self.client.patch(
            reverse("api-v1-json:file_get", kwargs={"file_uuid": self.file_uuid}),
            {"source": "outer space"},
            headers={"authorization": self.user1.auth},
            content_type="application/json",
        )
        assert response.status_code == 422
        # then with a valid url
        response = self.client.patch(
            reverse("api-v1-json:file_get", kwargs={"file_uuid": self.file_uuid}),
            {"source": "https://example.com/foo.png"},
            headers={"authorization": self.user1.auth},
            content_type="application/json",
        )
        assert response.status_code == 200

        # make sure we updated only the source attribute with the PATCH request
        assert response.json()["bma_response"]["source"] == "https://example.com/foo.png"
        assert response.json()["bma_response"]["attribution"] == "some attribution"

        # update thumbnail to an invalid value
        response = self.client.patch(
            reverse("api-v1-json:file_get", kwargs={"file_uuid": self.file_uuid}),
            {"thumbnail_url": "/foo/evil.ext"},
            headers={"authorization": self.user1.auth},
            content_type="application/json",
        )
        assert response.status_code == 422

    def test_post_csrf(self) -> None:
        """Make sure CSRF is enforced on API views when using django session cookie auth."""
        self.file_upload()
        self.client.force_login(self.user0)
        response = self.client.patch(
            reverse("api-v1-json:file_get", kwargs={"file_uuid": self.file_uuid}),
            {"attribution": "csrfcheck"},
            content_type="application/json",
        )
        # this should fail because we did not add CSRF..
        assert response.status_code == 403

    def test_file_delete(self) -> None:
        """Test deleting a file."""
        self.file_upload()
        # test with no auth
        response = self.client.delete(
            reverse("api-v1-json:file_get", kwargs={"file_uuid": self.file_uuid}),
        )
        assert response.status_code == 403

        # test with wrong auth
        response = self.client.delete(
            reverse("api-v1-json:file_get", kwargs={"file_uuid": self.file_uuid}),
            headers={"authorization": f"Bearer {self.user2.tokeninfo['access_token']}"},
        )
        assert response.status_code == 403

        # delete file, check mode
        response = self.client.delete(
            reverse("api-v1-json:file_get", kwargs={"file_uuid": self.file_uuid}) + "?check=true",
            headers={"authorization": self.user1.auth},
        )
        assert response.status_code == 202

        # delete file
        response = self.client.delete(
            reverse("api-v1-json:file_get", kwargs={"file_uuid": self.file_uuid}),
            headers={"authorization": self.user1.auth},
        )
        assert response.status_code == 204

    def test_metadata_get_404(self) -> None:
        """Get file metadata get with wrong uuid returns 404."""
        response = self.client.get(
            reverse(
                "api-v1-json:file_get",
                kwargs={"file_uuid": "a35ce7c9-f814-46ca-8c4e-87b992e15819"},
            ),
            headers={"authorization": self.user1.auth},
        )
        assert response.status_code == 404

    def test_metadata_get_validationerror(self) -> None:
        """Get file metadata get with something that is not a uuid."""
        response = self.client.get(
            reverse("api-v1-json:file_get", kwargs={"file_uuid": "notuuid"}), headers={"authorization": self.user1.auth}
        )
        assert response.status_code == 422

    def test_metadata_get_403(self) -> None:
        """Get file metadata get with wrong uuid returns 404."""
        self.file_upload()
        response = self.client.get(
            reverse(
                "api-v1-json:file_get",
                kwargs={"file_uuid": self.file_uuid},
            ),
            headers={"authorization": self.user1.auth},
        )
        assert response.status_code == 200
        response = self.client.get(
            reverse(
                "api-v1-json:file_get",
                kwargs={"file_uuid": self.file_uuid},
            ),
            headers={"authorization": f"Bearer {self.user2.tokeninfo['access_token']}"},
        )
        assert response.status_code == 403
        response = self.client.get(
            reverse(
                "api-v1-json:file_get",
                kwargs={"file_uuid": self.file_uuid},
            ),
        )
        assert response.status_code == 403

    def test_approve_files(self) -> None:
        """Approve multiple files."""
        for _ in range(10):
            self.file_upload()
        response = self.client.get(reverse("api-v1-json:file_list"), headers={"authorization": self.user1.auth})
        files = [f["uuid"] for f in response.json()["bma_response"]]
        # first try with no permissions
        response = self.client.patch(
            reverse("api-v1-json:approve_files"),
            {"files": files[0:5]},
            headers={"authorization": self.user1.auth},
            content_type="application/json",
        )
        assert response.status_code == 403

        # then check mode
        response = self.client.patch(
            reverse("api-v1-json:approve_files") + "?check=true",
            {"files": files[0:5]},
            headers={"authorization": self.superuser.auth},
            content_type="application/json",
        )
        assert response.status_code == 202

        # then with permission
        response = self.client.patch(
            reverse("api-v1-json:approve_files"),
            {"files": files[0:5]},
            headers={"authorization": self.superuser.auth},
            content_type="application/json",
        )
        assert response.status_code == 200

        # then try approving the same files again
        response = self.client.patch(
            reverse("api-v1-json:approve_files"),
            {"files": files[0:5]},
            headers={"authorization": self.superuser.auth},
            content_type="application/json",
        )
        assert response.status_code == 403

        # make sure files are now UNPUBLISHED
        response = self.client.get(
            reverse("api-v1-json:file_list"),
            data={"statuses": ["UNPUBLISHED"]},
            headers={"authorization": self.user1.auth},
        )
        assert len(response.json()["bma_response"]) == 5

    def test_file_missing_on_disk(self) -> None:
        """Test the case where a file has gone missing from disk for some reason."""
        self.file_upload()
        basefile = BaseFile.objects.get(uuid=self.file_uuid)
        Path(basefile.original.path).unlink()
        response = self.client.get(
            reverse(
                "api-v1-json:file_get",
                kwargs={"file_uuid": self.file_uuid},
            ),
            headers={"authorization": self.user1.auth},
        )
        assert response.status_code == 200
        assert response.json()["bma_response"]["size_bytes"] == 0
