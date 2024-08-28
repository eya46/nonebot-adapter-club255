from typing import Optional
from datetime import date, datetime

from pydantic import Field, BaseModel, model_validator

from .message import Message


class UploadKey(BaseModel):
    code: int
    id: int
    sign: str
    ts: int


class UploadResult(BaseModel):
    err: int
    id: str
    url: str


class VideoInfo(BaseModel):
    code: int
    cover: str
    title: str


class UserData(BaseModel):
    bilibiliScore: int
    douyuScore: int
    fans: int
    favorite: int
    follow: int
    post: int


class SignInfo(BaseModel):
    code: int
    exp: int
    msg: str


class LoginInfo(BaseModel):
    # code=0登录成功
    code: int
    token: str
    uid: int
    msg: str | None


class FollowResult(BaseModel):
    code: int
    msg: str
    # 0:取关 1:关注
    relation: int


class ReplyResult(BaseModel):
    # 回帖时:id = floor_id，回复楼层时没有
    id: int | None
    code: int
    exp: int
    msg: str


class PostResult(BaseModel):
    post_id: int
    code: int
    exp: int
    msg: str


class NavInfo(BaseModel):
    # 公告栏
    link: str
    text: str
    time: datetime


class LiveInfo(BaseModel):
    # 直播消息
    keyframe: str
    # 直播状态: 1开播,2未开播
    live_status: int
    user_cover: str


class VersionInfo(BaseModel):
    # 安卓下载地址
    android: str
    # ios下载地址
    ios: str
    # 描述
    description: str
    # 版本号
    version: str


class LikeInfo(BaseModel):
    code: int
    exp: int
    liked: bool
    msg: str


class NoticeCount(BaseModel):
    at: int
    chats: int
    likes: int
    message: int
    notice: int
    replies: int


class Label(BaseModel):
    labelId: int
    labelName: str
    # "rgb(250,143,34)"
    color: str


class Level(BaseModel):
    # "#ffffff"
    color: str
    exp: int
    # 当前的经验
    currentExp: int | None
    id: int | None
    label_color: str
    level: int
    name: str

    def __str__(self) -> str:
        return f"等级:{self.level}|{self.name}"

    @model_validator(mode="before")
    @classmethod
    def _set_label_color(cls, values: dict):
        if values.get("label_color") is not None:
            values["labelColor"] = values["label_color"]
        if values.get("labelColor") is not None:
            values["label_color"] = values["labelColor"]
        return values


class Tag(BaseModel):
    tagId: int
    tagName: str


class RawUser(BaseModel):
    """
    基础用户信息
    属性:
        avatar: 头像
        nickname: 昵称
        self_uid: 用户id
    """

    avatar: str
    nickname: str
    uid: int


class RawUserWithContribution(RawUser):
    contribution: int


class BaseUser(RawUser):
    auth: int
    authentication: str
    exp: int
    avatar: str
    nickname: str
    uid: int


class User(BaseUser):
    auth: int
    authentication: str
    exp: int
    avatar: str
    nickname: str
    uid: int
    # 性别 1,2,3 保密
    sex: int
    # 生日
    birthday: date
    # 运营商
    isp: str | None
    # 归属地
    location: str | None
    # 签名
    sign: str
    role: int
    status: int


class ChatList(BaseModel):
    isTop: bool
    lastMessage: str
    time: datetime
    unread: int
    user: BaseUser


class BaseFloor(BaseModel):
    content: str
    message: Message
    floor: int
    floorId: int

    @model_validator(mode="before")
    @classmethod
    def _set_message(cls, values: dict):
        Message.join_url(values)
        values["message"] = values["content"]
        return values


class RawPost(BaseModel):
    id: int
    postId: int
    title: str

    @model_validator(mode="before")
    @classmethod
    def _set_id_postId(cls, data: dict):
        if data.get("id") is not None:
            data["postId"] = data["id"]
        if data.get("postId") is not None:
            data["id"] = data["postId"]
        return data


class BasePost(RawPost):
    content: str
    labels: list[Label]
    post_time: datetime


class BaseLike(BaseModel):
    postId: int
    time: datetime
    # 1:帖子点赞 or 2楼层点赞
    type: int
    user: BaseUser

    def to_floor_like(self) -> Optional["FloorLike"]:
        if self.type != 2:
            return None
        return FloorLike.model_validate(self)

    def to_post_like(self) -> Optional["PostLike"]:
        if self.type != 1:
            return None
        return PostLike.model_validate(self)


class FloorLike(BaseLike):
    postId: int
    time: datetime
    # 1:帖子点赞 or 2楼层点赞
    type: int = Field(default=2)
    user: BaseUser
    floor: BaseFloor


class PostLike(BaseLike):
    postId: int
    time: datetime
    # 1:帖子点赞 or 2楼层点赞
    type: int = Field(default=1)
    user: BaseUser
    post: RawPost


class BaseNotice(BaseModel):
    sort: int
    status: int
    time: datetime

    def to_system_notice(self) -> Optional["SystemNotice"]:
        if self.get("type") is None:
            return None
        return SystemNotice.model_validate(self)

    def to_follow_notice(self) -> Optional["FollowNotice"]:
        if self.get("self_uid") is None:
            return None
        return FollowNotice.model_validate(self)


class SystemNotice(BaseNotice):
    # 消息中心->站务通知
    # 2:你的个性签名已通过审核
    type: int


class SystemNoticeMessage(BaseModel):
    # 消息中心->系统消息
    content: str
    time: datetime


class FollowNotice(BaseNotice):
    # 用户关注
    avatar: str
    nickname: str
    uid: int


class BaseReply(BaseModel):
    content: str
    message: Message
    postId: int
    time: datetime
    # 1:帖子回复 or 2楼层回复
    type: int
    user: BaseUser

    @model_validator(mode="before")
    @classmethod
    def _set_message(cls, values: dict):
        Message.join_url(values)
        values["message"] = values["content"]
        return values

    def to_post_reply(self) -> Optional["PostReply"]:
        if self.type != 1:
            return None
        return PostReply.model_validate(self)

    def to_floor_reply(self) -> Optional["FloorReply"]:
        if self.type != 2:
            return None
        return FloorReply.model_validate(self)


class PostReply(BaseReply):
    content: str
    message: Message
    postId: int
    time: datetime
    type: int = Field(default=1)
    post: RawPost


class FloorReply(BaseReply):
    content: str
    message: Message
    postId: int
    time: datetime
    type: int = Field(default=1)
    floor: BaseFloor


class PostInfo(BasePost):
    id: int
    postId: int
    title: str
    content: str
    post_time: datetime
    labels: list[Label]

    auth: int
    authentication: str
    author: BaseUser
    # message: Message
    hanserLike: bool
    hanserReply: bool
    last_reply_time: datetime
    last_reply_user: int

    likes: int
    replies: int
    readings: int
    # 0普通帖子, 1 等级贴, 2 新人贴, 3生日帖
    type: int
    role: int
    exp: int
    tags: list[Tag]
    videos: list[str]
    liked: bool
    pictures: list[str]
    primaryPictures: list[str]


class PostUser(BaseUser):
    auth: int
    authentication: str
    avatar: str
    exp: int
    nickname: str
    uid: int

    focusHe: bool
    role: int
    status: int


class PostDetails(PostInfo):
    id: int
    title: str
    auth: int
    authentication: str
    author: PostUser
    labels: list[Label]
    # html格式
    content: str
    likes: int
    liked: bool
    pictures: list[str]
    primaryPictures: list[str]
    post_time: datetime
    readings: int
    replies: int
    tags: list[Tag]
    type: int

    valued: bool
    top: bool
    status: int

    showLocation: int
    favorite: bool
    isp: str
    location: str


class UserPostInfo(RawPost):
    """
    api:post/user/list
    获取的帖子信息
    """

    auth: int
    authentication: str
    avatar: int
    content: str
    id: int
    labels: list[Label]
    liked: bool
    likes: int
    nickname: str
    pictures: list[str]
    post_time: datetime
    primaryPictures: list[str]
    readings: int
    replies: int
    tags: list[Tag]
    title: str


if __name__ == "__main__":

    def get_subclasses(class_):
        classes = []
        for i in class_.__subclasses__():
            classes.append(i.__name__)
            if len(i.__subclasses__()) > 0:
                classes.extend(get_subclasses(i))
        return classes

    models = [BaseModel.__name__]
    models.extend(get_subclasses(BaseModel))

    print(models)

__all__ = [
    "UploadKey",
    "UploadResult",
    "VideoInfo",
    "UserData",
    "SignInfo",
    "LoginInfo",
    "FollowResult",
    "ReplyResult",
    "PostResult",
    "NavInfo",
    "LiveInfo",
    "VersionInfo",
    "LikeInfo",
    "NoticeCount",
    "Label",
    "Level",
    "Tag",
    "RawUser",
    "BaseUser",
    "User",
    "PostUser",
    "ChatList",
    "BaseFloor",
    "RawPost",
    "PostInfo",
    "PostDetails",
    "UserPostInfo",
    "BaseLike",
    "FloorLike",
    "PostLike",
    "BaseNotice",
    "SystemNotice",
    "FollowNotice",
    "SystemNoticeMessage",
    "BaseReply",
    "PostReply",
    "FloorReply",
    "RawUserWithContribution",
    "BasePost",
]
