from contextlib import nullcontext as not_raises
from io import BytesIO
from unittest.mock import AsyncMock

import pytest
from fastapi import UploadFile
from pydantic import ValidationError

from services.database.models import Picture
from services.media_service.schemas import (
    DataBaseLoadSchema,
    MediaResponseSchema,
)
from services.media_service.service import MediaService
from services.response_schema import ExceptionSchema

service = MediaService()
session_mock = AsyncMock()
session_mock.add.return_value = None
session_mock.flush.return_value = None
session_mock.commit.return_value = None
service.session = session_mock


class TestMediaServiceUnit:

    @staticmethod
    @pytest.mark.parametrize(
        "file_name, expectation",
        [
            ("example.png", not_raises()),
            (1, pytest.raises(AttributeError)),
            ("example", pytest.raises(AssertionError)),
            (["example.png"], pytest.raises(AttributeError)),
        ],
    )
    def test_get_file_extension(file_name, expectation):
        with expectation:
            result = service._get_file_extension(file_name)
            assert result == file_name.split(".")[-1]

    @staticmethod
    @pytest.mark.parametrize(
        "file, mock_return_value, expected_result",
        [
            (
                UploadFile(
                    filename="test.png", file=BytesIO(b"test byte file")
                ),
                "http://example.com/test.png",
                DataBaseLoadSchema(link="http://example.com/test.png"),
            ),
            (
                [123],
                "http://example.com/test.png",
                ExceptionSchema(
                    result=False,
                    error_type="AttributeError",
                    error_message="'list' object has no attribute 'filename'",
                ),
            ),
        ],
    )
    async def test_write_file(
        mocker, file, mock_return_value, expected_result
    ):
        mocker.patch(
            "services.media_service.service.s3client.upload_file",
            return_value=mock_return_value,
        )
        result = await service._write_file(file)
        assert result == expected_result

    @staticmethod
    @pytest.mark.parametrize(
        "media_id, link, expectation",
        [
            (1, "http://example.com/test.png", not_raises()),
            (1, 1, pytest.raises(ValidationError)),
            (
                "str",
                "http://example.com/test.png",
                pytest.raises(AssertionError),
            ),
            (
                None,
                "http://example.com/test.png",
                pytest.raises(AssertionError),
            ),
        ],
    )
    async def test_load_into_the_database(mocker, media_id, link, expectation):
        with expectation:
            mocker.patch(
                "services.database.models.Picture.from_schema",
                return_value=Picture(id=media_id, link=link),
            )
            data = await service._load_into_the_database(
                DataBaseLoadSchema(link=link)
            )
            assert data == MediaResponseSchema(result=True, media_id=1)

    @staticmethod
    @pytest.mark.parametrize(
        "fake_file, "
        "get_file_response, "
        "write_file_response, "
        "load_db_response, "
        "expectation",
        [
            (
                UploadFile(
                    filename="test.txt", file=BytesIO(b"test byte file")
                ),
                "txt",
                ExceptionSchema(
                    result=False,
                    error_type="Authorization failed",
                    error_message="Authentication failed: "
                    "invalid credentials. Status code: 415",
                ),
                {"result": True, "media_id": 2},
                not_raises(),
            ),
            (
                list["pic1.png", "pic2.jpg"],
                "png",
                ExceptionSchema(
                    result=False,
                    error_type="AttributeError",
                    error_message="type object 'list' has no attribute "
                    "'filename'",
                ),
                {"result": True, "media_id": 1},
                not_raises(),
            ),
        ],
    )
    async def test_upload_picture(
        mocker,
        fake_file,
        get_file_response,
        write_file_response,
        load_db_response,
        expectation,
    ):
        with expectation:
            mocker.patch(
                "services.media_service.service."
                "MediaService._get_file_extension",
                return_value=get_file_response,
            )
            mocker.patch(
                "services.media_service.service.MediaService._write_file",
                return_value=write_file_response,
            )
            mocker.patch(
                "services.media_service.service."
                "MediaService._load_into_the_database",
                return_value=load_db_response,
            )
            response = await service.upload_picture(fake_file)
            assert response == write_file_response
