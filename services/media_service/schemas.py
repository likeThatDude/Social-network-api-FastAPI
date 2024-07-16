"""
Defines Pydantic schemas for handling media responses and database load
operations.

Dependencies:
    - ResponseSchema: Base schema imported from services.response_schema.
    - BaseModel: Base class for defining Pydantic models.

Classes:
    - MediaResponseSchema (ResponseSchema):
        Schema for representing media response data, inheriting from
        ResponseSchema.
        Attributes:
            media_id (int): ID of the uploaded media.

    - DataBaseLoadSchema (BaseModel):
        Schema for representing data from database load operations.
        Attributes:
            link (str): URL link to the loaded data.
"""

from pydantic import BaseModel

from services.response_schema import ResponseSchema


class MediaResponseSchema(ResponseSchema):
    media_id: int


class DataBaseLoadSchema(BaseModel):
    link: str
