from copy import deepcopy
from datetime import datetime
from typing import Literal, Optional

from nonebot import escape_tag
from nonebot.adapters import Event as BaseEvent
from pydantic import root_validator, Field

from .bean import BasePost, BaseFloor, PostInfo, BaseUser
from .message import Message
from .utils import truncate


class Event(BaseEvent):
    time: datetime
    self_uid: int
    post_type: str
    raw_data: dict

    @root_validator(pre=True, allow_reuse=True)
    def _set_raw_data(cls, values: dict):
        if values.get("time") is None:
            values["time"] = datetime.now()
        values["raw_data"] = deepcopy(values)
        return values

    def get_type(self) -> str:
        return self.post_type

    def get_event_name(self) -> str:
        return self.post_type

    def get_event_description(self) -> str:
        return escape_tag(str(self.dict()))

    def get_user_id(self) -> str:
        return str(self.self_uid)

    def get_session_id(self) -> str:
        raise ValueError("Event has no session id!")

    def get_message(self) -> "Message":
        raise ValueError("Event has no message!")

    def is_tome(self) -> bool:
        return False


class NoticeEvent(Event):
    post_type: Literal["notice"] = "notice"
    notice_type: str


class MessageEvent(Event):
    post_type: Literal["message"] = "message"
    content: str
    message: Message

    def get_message(self) -> "Message":
        return self.message

    @root_validator(pre=True, allow_reuse=True)
    def _set_message(cls, values: dict):
        Message.join_url(values)
        values["message"] = values["content"]
        return values


class OnLiveNoticeEvent(NoticeEvent):
    notice_type = "on_live"
    # 直播消息
    keyframe: str
    # 直播状态: 1开播,2未开播
    live_status: int
    user_cover: str

    def get_event_description(self) -> str:
        return f"hanser开播啦!"


class AtNoticeEvent(NoticeEvent):
    notice_type = "at"
    # 没被@过，写不出来
    pass


class FollowNoticeEvent(NoticeEvent):
    notice_type = "follow"

    sort: int
    status: int
    time: datetime
    avatar: str
    nickname: str
    uid: int

    def get_event_description(self) -> str:
        return f"{self.nickname}({self.uid}) 关注了你"


class SystemNoticeEvent(NoticeEvent):
    notice_type = "system_notice"

    sort: int
    status: int
    time: datetime
    # # 2:你的个性签名已通过审核
    type: int

    def get_event_description(self) -> str:
        return f"系统通知,type -> {self.type}"


class SystemNoticeMessageEvent(NoticeEvent):
    notice_type = "system_message_notice"

    # 消息中心->系统消息
    content: str
    time: datetime

    def get_event_description(self) -> str:
        return f"系统通知消息 -> {self.content}"


class LikeNoticeEvent(NoticeEvent):
    notice_type = "like"

    postId: int
    time: datetime
    # 1:帖子点赞 or 2楼层点赞
    type: int
    user: BaseUser

    def get_event_description(self) -> str:
        return f"{self.user.nickname}({self.user.uid}) 给你点赞了"


class PostLikeNoticeEvent(LikeNoticeEvent):
    notice_type = "notice_like"

    postId: int
    time: datetime
    # 1:帖子点赞 or 2楼层点赞
    type: int = Field(default=1)
    user: BaseUser
    post: BasePost

    def get_event_description(self) -> str:
        return f"{self.user.nickname}({self.user.uid}) 给你的帖子点赞了({self.post.title})"


class FloorLikeNoticeEvent(LikeNoticeEvent):
    notice_type = "floor_like"

    postId: int
    time: datetime
    # 1:帖子点赞 or 2楼层点赞
    type: int = Field(default=2)
    user: BaseUser
    floor: BaseFloor

    def get_event_description(self) -> str:
        return f"{self.user.nickname}({self.user.uid}) 给你的楼层点赞了({truncate(self.floor.message)})"


class ReplyEvent(MessageEvent):
    content: str
    message: Message
    postId: int
    time: datetime
    # 1:帖子回复 or 2楼层回复
    type: int
    user: BaseUser

    def get_event_description(self) -> str:
        return f"{self.user.nickname}({self.user.uid}) 给你回复了({truncate(self.message)})"

    @root_validator(pre=True, allow_reuse=True)
    def _set_message(cls, values: dict):
        Message.join_url(values)
        values["message"] = values["content"]
        return values

    def to_post_reply_event(self) -> Optional["PostReplyEvent"]:
        if self.type != 1:
            return None
        return PostReplyEvent.parse_obj(self.raw_data)

    def to_floor_reply_event(self) -> Optional["FloorReplyEvent"]:
        if self.type != 2:
            return None
        return FloorReplyEvent.parse_obj(self.raw_data)


class PostReplyEvent(ReplyEvent):
    type: int = Field(default=1)
    post: BasePost

    def get_event_description(self) -> str:
        return f"{self.user.nickname}({self.user.uid}) " \
               f"给你的帖子({self.post.title})回复了({truncate(self.message)})"


class FloorReplyEvent(ReplyEvent):
    type: int = Field(default=2)
    floor: BaseFloor

    def get_event_description(self) -> str:
        return f"{self.user.nickname}({self.user.uid}) " \
               f"给你的回帖({truncate(self.floor.message)})回复了({truncate(self.message)})"


class PostEvent(MessageEvent):
    message_type: str = "post"
    post: PostInfo

    @root_validator(pre=True, allow_reuse=True)
    def _set_post(cls, values: dict):
        values["post"] = values["raw_data"]
        return values

    def get_event_description(self) -> str:
        return f"帖子 | {self.post.title} | {truncate(self.message)}"


class NewPostEvent(PostEvent):
    message_type: str = "new_post"

    post: PostInfo

    def get_event_description(self) -> str:
        return f"新帖 | {self.post.title} | {truncate(self.message)}"


class NicePostEvent(PostEvent):
    message_type: str = "nice_post"

    post: PostInfo

    def get_event_description(self) -> str:
        return f"新精华帖 | {self.post.title} | {truncate(self.message)}"
