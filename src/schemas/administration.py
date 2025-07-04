from pydantic import BaseModel

from ._mixins import EmailMixin


class BaseEmailSchema(EmailMixin, BaseModel):
    pass


class ChangeGroupRequest(BaseEmailSchema):
    group_id: int
