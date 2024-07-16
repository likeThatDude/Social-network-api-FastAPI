"""
Data schemas for handling API responses and exceptions.
"""

from pydantic import BaseModel


class ResponseSchema(BaseModel):
    result: bool


class ExceptionSchema(ResponseSchema):
    error_type: str
    error_message: str
