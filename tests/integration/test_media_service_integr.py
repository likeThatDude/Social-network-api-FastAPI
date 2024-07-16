import pytest
from httpx import AsyncClient


@pytest.mark.order(1)
class TestMediaService:

    @staticmethod
    @pytest.mark.parametrize(
        "picture, number",
        [
            (f"tests/media_for_test/{number}.png", number)
            for number in range(1, 4)
        ],
    )
    async def test_upload_tweet_media(ac: AsyncClient, picture, number):
        with open(picture, "rb") as image_file:
            files = {"file": (f"{number}image.png", image_file, "image/png")}
            response = await ac.post(
                "/api/medias", headers={"api-key": "test0"}, files=files
            )
            assert response.status_code == 200
            assert response.json() == {"result": True, "media_id": number}

    @staticmethod
    async def test_upload_not_valid_file(ac: AsyncClient):
        picture = "tests/conftest.py"
        with open(picture, "rb") as image_file:
            print(picture)
            files = {"file": ("conftest.py", image_file, "image/png")}
            response = await ac.post(
                "/api/medias", headers={"api-key": "test0"}, files=files
            )
            assert response.status_code == 200
            assert response.json() == {
                "result": False,
                "error_type": "Authorization failed",
                "error_message": "Authentication failed: "
                "invalid credentials. Status code: 415",
            }
