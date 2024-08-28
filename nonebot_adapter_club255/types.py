from typing import Literal, TypeVar

from pydantic import BaseModel

AccessEventName = Literal["on_live", "notice", "nice_post", "post"]

T = TypeVar("T")


UID = TypeVar("UID", int, str)  # 用户id
PID = TypeVar("PID", int, str)  # 帖子id
FID = TypeVar("FID", int, str)  # 楼层id
MID = TypeVar("MID", int, str)  # 消息id


class ApiResult(BaseModel):
    code: int
    msg: str | None
    data: BaseModel | None


__all__ = ["ApiResult", "T", "UID", "PID", "FID", "MID", "AccessEventName"]
