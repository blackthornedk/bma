"""Tests for the files API."""
from pathlib import Path

from bs4 import BeautifulSoup
from django.conf import settings
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
        response = self.client.get("/o/authorized_tokens/", headers={"authorization": self.creator2.auth})
        assert response.status_code == 200
        assert "revoke" in response.content.decode("utf-8")

    def test_api_auth_get_refresh_token(self) -> None:
        """Test getting a refresh token."""
        response = self.client.post(
            "/o/token/",
            {
                "grant_type": "refresh_token",
                "client_id": f"client_id_{self.creator2.username}",
                "refresh_token": self.creator2.tokeninfo["refresh_token"],
            },
        )
        assert response.status_code == 200
        assert "refresh_token" in response.json()

    def test_api_auth_django_session(self) -> None:
        """Test getting authorised tokens."""
        self.client.force_login(self.creator2)
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
        response = self.client.get(reverse("api-v1-json:file_list"), headers={"authorization": self.creator2.auth})
        assert response.status_code == 200
        assert len(response.json()["bma_response"]) == 15

        # test sorting
        response = self.client.get(
            reverse("api-v1-json:file_list"),
            data={"limit": 5, "sorting": "title_asc"},
            headers={"authorization": self.creator2.auth},
        )
        assert len(response.json()["bma_response"]) == 5
        assert response.json()["bma_response"][0]["title"] == "title0"
        assert response.json()["bma_response"][1]["title"] == "title1"
        assert response.json()["bma_response"][2]["title"] == "title10"
        assert response.json()["bma_response"][4]["title"] == "title12"
        response = self.client.get(
            reverse("api-v1-json:file_list"),
            data={"limit": 1, "sorting": "created_desc"},
            headers={"authorization": self.creator2.auth},
        )
        assert response.json()["bma_response"][0]["title"] == "title14"

        # test offset
        response = self.client.get(
            reverse("api-v1-json:file_list"),
            data={"offset": 5, "sorting": "created_asc"},
            headers={"authorization": self.creator2.auth},
        )
        assert response.json()["bma_response"][0]["title"] == "title5"
        assert response.json()["bma_response"][4]["title"] == "title9"

        # test uploader filter
        response = self.client.get(
            reverse("api-v1-json:file_list"),
            data={"uploaders": [self.creator2.uuid, self.user0.uuid]},
            headers={"authorization": self.creator2.auth},
        )
        assert len(response.json()["bma_response"]) == 15
        response = self.client.get(
            reverse("api-v1-json:file_list"),
            data={"uploaders": [self.user0.uuid]},
            headers={"authorization": self.creator2.auth},
        )
        assert len(response.json()["bma_response"]) == 0

        # test search
        response = self.client.get(
            reverse("api-v1-json:file_list"), data={"search": "title7"}, headers={"authorization": self.creator2.auth}
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
            headers={"authorization": self.creator2.auth},
            content_type="application/json",
        )
        assert response.status_code == 201
        self.album_uuid = response.json()["bma_response"]["uuid"]

        # test album filter
        response = self.client.get(
            reverse("api-v1-json:file_list"),
            data={"albums": [self.album_uuid]},
            headers={"authorization": self.creator2.auth},
        )
        assert len(response.json()["bma_response"]) == 3

        # create another empty album
        response = self.client.post(
            reverse("api-v1-json:album_create"),
            {
                "title": "another album title here",
            },
            headers={"authorization": self.creator2.auth},
            content_type="application/json",
        )
        assert response.status_code == 201
        uuid = response.json()["bma_response"]["uuid"]

        # test filtering for multiple albums
        response = self.client.get(
            reverse("api-v1-json:file_list"),
            data={"albums": [self.album_uuid, uuid]},
            headers={"authorization": self.creator2.auth},
        )
        assert len(response.json()["bma_response"]) == 3

        # test file size filter
        response = self.client.get(
            reverse("api-v1-json:file_list"), data={"size": 9478}, headers={"authorization": self.creator2.auth}
        )
        assert len(response.json()["bma_response"]) == 15

        # test file size_lt filter
        response = self.client.get(
            reverse("api-v1-json:file_list"), data={"size_lt": 10000}, headers={"authorization": self.creator2.auth}
        )
        assert len(response.json()["bma_response"]) == 15
        response = self.client.get(
            reverse("api-v1-json:file_list"), data={"size_lt": 1000}, headers={"authorization": self.creator2.auth}
        )
        assert len(response.json()["bma_response"]) == 0

        # test file size_gt filter
        response = self.client.get(
            reverse("api-v1-json:file_list"), data={"size_gt": 10000}, headers={"authorization": self.creator2.auth}
        )
        assert len(response.json()["bma_response"]) == 0
        response = self.client.get(
            reverse("api-v1-json:file_list"), data={"size_gt": 1000}, headers={"authorization": self.creator2.auth}
        )
        assert len(response.json()["bma_response"]) == 15

        # test file type filter
        response = self.client.get(
            reverse("api-v1-json:file_list"),
            data={"filetypes": ["picture"]},
            headers={"authorization": self.creator2.auth},
        )
        assert len(response.json()["bma_response"]) == 15
        response = self.client.get(
            reverse("api-v1-json:file_list"),
            data={"filetypes": ["audio", "video", "document"]},
            headers={"authorization": self.creator2.auth},
        )
        assert len(response.json()["bma_response"]) == 0

        # test file license filter
        response = self.client.get(
            reverse("api-v1-json:file_list"),
            data={"licenses": ["CC_ZERO_1_0"]},
            headers={"authorization": self.creator2.auth},
        )
        assert len(response.json()["bma_response"]) == 15
        response = self.client.get(
            reverse("api-v1-json:file_list"),
            data={"licenses": ["CC_BY_4_0", "CC_BY_SA_4_0"]},
            headers={"authorization": self.creator2.auth},
        )
        assert len(response.json()["bma_response"]) == 0

    def test_file_list_permissions(self) -> None:
        """Test various permissions stuff for the file_list endpoint."""
        files = [self.file_upload(title=f"title{i}") for i in range(15)]

        # no files should be visible
        response = self.client.get(reverse("api-v1-json:file_list"), headers={"authorization": self.user0.auth})
        assert response.status_code == 200
        assert len(response.json()["bma_response"]) == 0

        # the superuser can see all files
        response = self.client.get(reverse("api-v1-json:file_list"), headers={"authorization": self.superuser.auth})
        assert response.status_code == 200
        assert len(response.json()["bma_response"]) == 15

        # attempt to publish a file before approval
        response = self.client.patch(
            reverse("api-v1-json:publish_file", kwargs={"file_uuid": files[0]}),
            headers={"authorization": self.creator2.auth},
        )
        assert response.status_code == 403

        # approve the file without permission
        response = self.client.patch(
            reverse("api-v1-json:approve_file", kwargs={"file_uuid": files[0]}),
            headers={"authorization": self.creator2.auth},
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
            headers={"authorization": self.creator2.auth},
        )
        assert len(response.json()["bma_response"]) == 1

        # publish a file, check mode
        response = self.client.patch(
            reverse("api-v1-json:publish_file", kwargs={"file_uuid": files[0]}) + "?check=true",
            headers={"authorization": self.creator2.auth},
        )
        assert response.status_code == 202

        # publish the file
        response = self.client.patch(
            reverse("api-v1-json:publish_file", kwargs={"file_uuid": files[0]}),
            headers={"authorization": self.creator2.auth},
        )
        assert response.status_code == 200

        # make sure someone else can see it
        response = self.client.get(reverse("api-v1-json:file_list"), headers={"authorization": self.user0.auth})
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
            headers={"authorization": self.user0.auth},
        )
        assert response.status_code == 403

        # unpublish the file, check mode
        response = self.client.patch(
            reverse("api-v1-json:unpublish_file", kwargs={"file_uuid": files[0]}) + "?check=true",
            headers={"authorization": self.creator2.auth},
        )
        assert response.status_code == 202

        # unpublish the file
        response = self.client.patch(
            reverse("api-v1-json:unpublish_file", kwargs={"file_uuid": files[0]}),
            headers={"authorization": self.creator2.auth},
        )
        assert response.status_code == 200

        # make sure it is not visible anymore
        response = self.client.get(reverse("api-v1-json:file_list"), headers={"authorization": self.user0.auth})
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
            headers={"authorization": self.creator2.auth},
        )
        assert response.status_code == 200
        assert "uuid" in response.json()["bma_response"]
        assert response.json()["bma_response"]["uuid"] == self.file_uuid

    def test_file_download(self) -> None:
        """Test downloading a file after uploading it."""
        self.file_upload()
        metadata = self.client.get(
            reverse("api-v1-json:file_list"), headers={"authorization": self.creator2.auth}
        ).json()["bma_response"][0]
        url = metadata["links"]["downloads"]["original"]
        # try download of unpublished file without auth
        response = self.client.get(url)
        assert response.status_code == 403
        # try again with auth
        self.client.force_login(self.creator2)
        response = self.client.get(url)
        assert response.status_code == 200
        assert response["content-type"] == "image/png"
        with (settings.BASE_DIR / "static_src/images/logo_wide_black_500_RGB.png").open("rb") as f:
            assert f.read() == response.getvalue()

    def test_file_metadata_update(self) -> None:
        """Replace and then update file metadata."""
        self.file_upload()
        response = self.client.get(
            reverse("api-v1-json:file_get", kwargs={"file_uuid": self.file_uuid}),
            headers={"authorization": self.creator2.auth},
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
            headers={"authorization": f"Bearer {self.user0.tokeninfo['access_token']}"},
            content_type="application/json",
        )
        assert response.status_code == 403

        # update the file, check mode
        response = self.client.put(
            reverse("api-v1-json:file_get", kwargs={"file_uuid": self.file_uuid}) + "?check=true",
            updates,
            headers={"authorization": self.creator2.auth},
            content_type="application/json",
        )
        assert response.status_code == 202

        # replace the file metadata
        response = self.client.put(
            reverse("api-v1-json:file_get", kwargs={"file_uuid": self.file_uuid}),
            updates,
            headers={"authorization": self.creator2.auth},
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
            headers={"authorization": self.creator2.auth},
            content_type="application/json",
        )
        assert response.status_code == 422

        # update instead of replace, first with invalid source url
        response = self.client.patch(
            reverse("api-v1-json:file_get", kwargs={"file_uuid": self.file_uuid}),
            {"original_source": "outer space"},
            headers={"authorization": self.creator2.auth},
            content_type="application/json",
        )
        assert response.status_code == 422
        # then with a valid url
        response = self.client.patch(
            reverse("api-v1-json:file_get", kwargs={"file_uuid": self.file_uuid}),
            {"original_source": "https://example.com/foo.png"},
            headers={"authorization": self.creator2.auth},
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
            headers={"authorization": self.creator2.auth},
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
            headers={"authorization": f"Bearer {self.user0.tokeninfo['access_token']}"},
        )
        assert response.status_code == 403

        # delete file, check mode
        response = self.client.delete(
            reverse("api-v1-json:file_get", kwargs={"file_uuid": self.file_uuid}) + "?check=true",
            headers={"authorization": self.creator2.auth},
        )
        assert response.status_code == 202

        # delete file
        response = self.client.delete(
            reverse("api-v1-json:file_get", kwargs={"file_uuid": self.file_uuid}),
            headers={"authorization": self.creator2.auth},
        )
        assert response.status_code == 204

    def test_metadata_get_404(self) -> None:
        """Get file metadata get with wrong uuid returns 404."""
        response = self.client.get(
            reverse(
                "api-v1-json:file_get",
                kwargs={"file_uuid": "a35ce7c9-f814-46ca-8c4e-87b992e15819"},
            ),
            headers={"authorization": self.creator2.auth},
        )
        assert response.status_code == 404

    def test_metadata_get_validationerror(self) -> None:
        """Get file metadata get with something that is not a uuid."""
        response = self.client.get(
            reverse("api-v1-json:file_get", kwargs={"file_uuid": "notuuid"}),
            headers={"authorization": self.creator2.auth},
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
            headers={"authorization": self.creator2.auth},
        )
        assert response.status_code == 200
        response = self.client.get(
            reverse(
                "api-v1-json:file_get",
                kwargs={"file_uuid": self.file_uuid},
            ),
            headers={"authorization": f"Bearer {self.user0.tokeninfo['access_token']}"},
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
        response = self.client.get(reverse("api-v1-json:file_list"), headers={"authorization": self.creator2.auth})
        files = [f["uuid"] for f in response.json()["bma_response"]]
        # first try with no permissions
        response = self.client.patch(
            reverse("api-v1-json:approve_files"),
            {"files": files[0:5]},
            headers={"authorization": self.creator2.auth},
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
            headers={"authorization": self.creator2.auth},
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
            headers={"authorization": self.creator2.auth},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["bma_response"]["size_bytes"], 0)


class FileAdminTests(ApiTestBase):
    """Tests for the FileAdmin."""

    def test_file_list_status_code(self) -> None:
        """Test the access controls for the list page in the FileAdmin."""
        url = reverse("file_admin:files_basefile_changelist")
        # try accessing the file_admin without a login
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        # try accessing the file_admin with a user without permissions for it
        self.client.login(username="user0", password="secret")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        # try accessing the file_admin with a user with is_creator=True
        self.client.login(username="creator2", password="secret")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        # try accessing the file_admin with a user with is_moderator=True
        self.client.login(username="moderator4", password="secret")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        # try accessing the file_admin with a user with is_curator=True
        self.client.login(username="curator6", password="secret")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)

    def test_file_list_html(self) -> None:
        """Test the file list page in the FileAdmin."""
        # upload some files
        self.files = [self.file_upload() for _ in range(10)]
        for _ in range(10):
            self.files.append(self.file_upload(uploader="creator3"))

        # the superuser can see all files
        url = reverse("file_admin:files_basefile_changelist")
        self.client.login(username="superuser", password="secret")
        response = self.client.get(url)
        self.assertInHTML(
            '<p class="paginator">20 files</p>', response.content.decode(), msg_prefix="superuser can not see 20 files"
        )

        # each creator can see 10 files
        for c in ["creator2", "creator3"]:
            self.client.login(username=c, password="secret")
            response = self.client.get(url)
            self.assertInHTML(
                '<p class="paginator">10 files</p>',
                response.content.decode(),
                msg_prefix=f"creator {c} can not see 10 files",
            )

        # each moderator can see all 20 files
        for m in ["moderator4", "moderator5"]:
            self.client.login(username=m, password="secret")
            response = self.client.get(url)
            self.assertInHTML(
                '<p class="paginator">20 files</p>',
                response.content.decode(),
                msg_prefix=f"moderator {m} can not see 20 files",
            )

        # make moderator4 approve 5 of the files owned by creator2
        data = {"action": "approve", "_selected_action": self.files[:5]}
        self.client.login(username="moderator4", password="secret")
        response = self.client.post(url, data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertInHTML(
            '<p class="paginator">20 files</p>',
            response.content.decode(),
            msg_prefix=f"moderator {m} can not see 20 files",
        )

        # test filtering by status to show the approved files
        response = self.client.get(url + "?status__exact=UNPUBLISHED")
        self.assertInHTML(
            '<p class="paginator">5 files</p>', response.content.decode(), msg_prefix="can not see 5 unpublished files"
        )

        # each creator can still see 10 files
        for c in ["creator2", "creator3"]:
            self.client.login(username=c, password="secret")
            response = self.client.get(url)
            self.assertInHTML(
                '<p class="paginator">10 files</p>',
                response.content.decode(),
                msg_prefix=f"creator {c} can not see 10 files",
            )

        # make creator2 publish the 5 approved files
        data = {"action": "publish", "_selected_action": self.files[:5]}
        self.client.login(username="creator2", password="secret")
        response = self.client.post(url, data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertInHTML(
            '<p class="paginator">10 files</p>', response.content.decode(), msg_prefix="creator2 can not see 10 files"
        )
        response = self.client.get(url + "?status__exact=PUBLISHED")
        self.assertInHTML(
            '<p class="paginator">5 files</p>', response.content.decode(), msg_prefix="can not see 5 published files"
        )

        # make creator2 unpublish the 5 approved files
        data = {"action": "unpublish", "_selected_action": self.files[:5]}
        response = self.client.post(url, data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertInHTML(
            "5 files selected to be unpublished, "
            "out of those 5 files had needed permission and expected status, "
            "and out of those 5 files were successfully unpublished",
            response.content.decode(),
            msg_prefix="unpublished message not found",
        )
        self.assertInHTML(
            '<p class="paginator">10 files</p>', response.content.decode(), msg_prefix="creator2 can not see 10 files"
        )
        response = self.client.get(url + "?status__exact=UNPUBLISHED")
        self.assertInHTML(
            '<p class="paginator">5 files</p>',
            response.content.decode(),
            msg_prefix="creator2 can not see 5 unpublished files after unpublishing",
        )

        # make moderator4 unapprove 5 of the files owned by creator2
        data = {"action": "unapprove", "_selected_action": self.files[:5]}
        self.client.login(username="moderator4", password="secret")
        response = self.client.post(url, data, follow=True)
        self.assertEqual(response.status_code, 200)
        response = self.client.get(url + "?status__exact=PENDING_MODERATION")
        self.assertInHTML(
            '<p class="paginator">20 files</p>',
            response.content.decode(),
            msg_prefix=f"moderator {m} can not see 20 files pending moderation",
        )


class FileViewTests(ApiTestBase):
    """Unit tests for regular django views."""

    def test_file_list_view(self) -> None:  # noqa: PLR0915
        """Test the basics of the file list view."""
        # upload some files as creator2
        self.files = [self.file_upload() for _ in range(10)]
        # upload some files as creator3
        for _ in range(10):
            self.files.append(self.file_upload(uploader="creator3"))

        # the superuser can see all 20 files
        url = reverse("files:file_list")
        self.client.login(username="superuser", password="secret")
        response = self.client.get(url)
        content = response.content.decode()
        soup = BeautifulSoup(content, "html.parser")
        rows = soup.select("div.table-container > table > tbody > tr")
        self.assertEqual(len(rows), len(self.files), "superuser can not see 20 files")

        # anonymous can see 0 files
        self.client.logout()
        response = self.client.get(url)
        content = response.content.decode()
        soup = BeautifulSoup(content, "html.parser")
        rows = soup.select("div.table-container > table > tbody > tr")
        self.assertEqual(len(rows), 0, "anonymous user can not see 0 files")

        # each creator can see 10 files
        for c in ["creator2", "creator3"]:
            self.client.login(username=c, password="secret")
            response = self.client.get(url)
            content = response.content.decode()
            soup = BeautifulSoup(content, "html.parser")
            rows = soup.select("div.table-container > table > tbody > tr")
            self.assertEqual(len(rows), 10, f"creator {c} can not see 10 files")

        # each moderator can see all 20 files
        for m in ["moderator4", "moderator5"]:
            self.client.login(username=m, password="secret")
            response = self.client.get(url)
            content = response.content.decode()
            soup = BeautifulSoup(content, "html.parser")
            rows = soup.select("div.table-container > table > tbody > tr")
            self.assertEqual(len(rows), 20, f"moderator {m} can not see 20 files")

        # each curator can see 0 files since none are approved yet
        for m in ["curator6", "curator7"]:
            self.client.login(username=m, password="secret")
            response = self.client.get(url)
            content = response.content.decode()
            soup = BeautifulSoup(content, "html.parser")
            rows = soup.select("div.table-container > table > tbody > tr")
            self.assertEqual(len(rows), 0, f"curator {m} can not see 0 files")

        # make moderator4 approve 5 of the files owned by creator2
        adminurl = reverse("file_admin:files_basefile_changelist")
        data = {"action": "approve", "_selected_action": self.files[:5]}
        self.client.login(username="moderator4", password="secret")
        response = self.client.post(adminurl, data, follow=True)
        self.assertEqual(response.status_code, 200)

        # test filtering by status to show the approved files
        response = self.client.get(url + "?status=UNPUBLISHED")
        content = response.content.decode()
        soup = BeautifulSoup(content, "html.parser")
        rows = soup.select("div.table-container > table > tbody > tr")
        self.assertEqual(len(rows), 5, "filtering by status does not return 5 files")

        # each curator can still see 0 files since none are published yet
        for m in ["curator6", "curator7"]:
            self.client.login(username=m, password="secret")
            response = self.client.get(url)
            content = response.content.decode()
            soup = BeautifulSoup(content, "html.parser")
            rows = soup.select("div.table-container > table > tbody > tr")
            self.assertEqual(len(rows), 0, f"curator {m} can not see 0 files")

        # make creator2 publish the 5 approved files
        adminurl = reverse("file_admin:files_basefile_changelist")
        data = {"action": "publish", "_selected_action": self.files[:5]}
        self.client.login(username="creator2", password="secret")
        response = self.client.post(adminurl, data, follow=True)
        self.assertEqual(response.status_code, 200)

        # each curator can now see 5 files
        for m in ["curator6", "curator7"]:
            self.client.login(username=m, password="secret")
            response = self.client.get(url)
            content = response.content.decode()
            soup = BeautifulSoup(content, "html.parser")
            rows = soup.select("div.table-container > table > tbody > tr")
            self.assertEqual(len(rows), 5, f"curator {m} can not see 5 files")
