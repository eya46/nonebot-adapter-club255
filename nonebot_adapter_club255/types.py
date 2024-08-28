from copy import deepcopy
from typing import TypeVar, Optional, Literal

from pydantic import BaseModel, root_validator, AnyUrl

AccessEventName = Literal['on_live', 'notice', 'nice_post', 'post']

T = TypeVar("T")


class HttpUrl(AnyUrl):
    """http或https url"""

    allow_schemes = {"http", "https"}


UID = TypeVar('UID', int, str)  # 用户id
PID = TypeVar('PID', int, str)  # 帖子id
FID = TypeVar('FID', int, str)  # 楼层id
MID = TypeVar('MID', int, str)  # 消息id


class RawModel(BaseModel):
    raw_data: dict

    @root_validator(pre=True, allow_reuse=True)
    def _set_raw_data(cls, values: dict):
        values["raw_data"] = deepcopy(values)
        return values


class ApiResult(BaseModel):
    code: int
    msg: Optional[str]
    data: Optional[RawModel]


__all__ = [
    "RawModel", "ApiResult", "T", "UID", "PID", "FID", "MID", "AccessEventName", "HttpUrl"
]
