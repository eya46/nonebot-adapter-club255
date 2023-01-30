from copy import deepcopy
from datetime import date, datetime
from typing import Optional, List

from pydantic import BaseModel, root_validator, Field

from .message import Message


# try:
#     from .message import Message
# except:
#     from nonebot123.adapters.club255.message import Message


class RawModel(BaseModel):
    raw_data: dict

    @root_validator(pre=True, allow_reuse=True)
    def _set_raw_data(cls, values: dict):
        values["raw_data"] = deepcopy(values)
        return values


class UploadKey(RawModel):
    code: int
    id: int
    sign: str
    ts: int


class UploadResult(RawModel):
    err: int
    id: str
    url: str


class VideoInfo(RawModel):
    code: int
    cover: str
    title: str


class UserData(RawModel):
    bilibiliScore: int
    douyuScore: int
    fans: int
    favorite: int
    follow: int
    post: int


class SignInfo(RawModel):
    code: int
    exp: int
    msg: str


class LoginInfo(RawModel):
    # code=0登录成功
    code: int
    token: str
    uid: int
    msg: Optional[str]


class FollowResult(RawModel):
    code: int
    msg: str
    # 0:取关 1:关注
    relation: int


class ReplyResult(RawModel):
    # 回帖时:id = floor_id，回复楼层时没有
    id: Optional[int]
    code: int
    exp: int
    msg: str


class PostResult(RawModel):
    post_id: int
    code: int
    exp: int
    msg: str


class NavInfo(RawModel):
    # 公告栏
    link: str
    text: str
    time: datetime


class LiveInfo(RawModel):
    # 直播消息
    keyframe: str
    # 直播状态: 1开播,2未开播
    live_status: int
    user_cover: str


class VersionInfo(RawModel):
    # 安卓下载地址
    android: str
    # 描述
    description: str
    # ios下载地址
    ios: str
    # 版本号
    version: str


class LikeInfo(RawModel):
    code: int
    exp: int
    liked: bool
    msg: str


class NoticeCount(RawModel):
    at: int
    chats: int
    likes: int
    message: int
    notice: int
    replies: int


class Label(RawModel):
    labelId: int
    labelName: str
    # "rgb(250,143,34)"
    color: str


class Level(RawModel):
    # "#ffffff"
    color: str
    exp: int
    # 当前的经验
    currentExp: Optional[int]
    id: Optional[int]
    label_color: str
    level: int
    name: str

    def __str__(self) -> str:
        return f"等级:{self.level}|{self.name}"

    @root_validator(pre=True, allow_reuse=True)
    def _set_label_color(cls, values: dict):
        if values.get("label_color") is not None:
            values["labelColor"] = values["label_color"]
        if values.get("labelColor") is not None:
            values["label_color"] = values["labelColor"]
        return values


class Tag(RawModel):
    tagId: int
    tagName: str


class RawUser(RawModel):
    avatar: str
    nickname: str
    uid: int


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
    isp: Optional[str]
    # 归属地
    location: Optional[str]
    # 签名
    sign: str
    role: int
    status: int


class ChatList(RawModel):
    isTop: bool
    lastMessage: str
    time: datetime
    unread: int
    user: BaseUser


class BaseFloor(RawModel):
    content: str
    message: Message
    floor: int
    floorId: int

    @root_validator(pre=True, allow_reuse=True)
    def _set_message(cls, values: dict):
        Message.join_url(values)
        values["message"] = values["content"]
        return values


class BasePost(RawModel):
    id: int
    postId: int
    title: str

    @root_validator(pre=True, allow_reuse=True)
    def _set_id_postId(cls, data: dict):
        if data.get("id") is not None:
            data["postId"] = data["id"]
        if data.get("postId") is not None:
            data["id"] = data["postId"]
        return data


class BaseLike(RawModel):
    postId: int
    time: datetime
    # 1:帖子点赞 or 2楼层点赞
    type: int
    user: BaseUser

    def to_floor_like(self) -> Optional["FloorLike"]:
        if self.type != 2:
            return None
        return FloorLike.parse_obj(self.raw_data)

    def to_post_like(self) -> Optional["PostLike"]:
        if self.type != 1:
            return None
        return PostLike.parse_obj(self.raw_data)


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
    post: BasePost


class BaseNotice(RawModel):
    sort: int
    status: int
    time: datetime

    def to_system_notice(self) -> Optional["SystemNotice"]:
        if self.raw_data.get("type") is None:
            return None
        return SystemNotice.parse_obj(self.raw_data)

    def to_follow_notice(self) -> Optional["FollowNotice"]:
        if self.raw_data.get("uid") is None:
            return None
        return FollowNotice.parse_obj(self.raw_data)


class SystemNotice(BaseNotice):
    # 消息中心->站务通知
    # 2:你的个性签名已通过审核
    type: int


class SystemNoticeMessage(RawModel):
    # 消息中心->系统消息
    content: str
    time: datetime


class FollowNotice(BaseNotice):
    # 用户关注
    avatar: str
    nickname: str
    uid: int


class BaseReply(RawModel):
    content: str
    message: Message
    postId: int
    time: datetime
    # 1:帖子回复 or 2楼层回复
    type: int
    user: BaseUser

    @root_validator(pre=True, allow_reuse=True)
    def _set_message(cls, values: dict):
        Message.join_url(values)
        values["message"] = values["content"]
        return values

    def to_post_reply(self) -> Optional["PostReply"]:
        if self.type != 1:
            return None
        return PostReply.parse_obj(self.raw_data)

    def to_floor_reply(self) -> Optional["FloorReply"]:
        if self.type != 2:
            return None
        return FloorReply.parse_obj(self.raw_data)


class PostReply(BaseReply):
    content: str
    message: Message
    postId: int
    time: datetime
    type: int = Field(default=1)
    post: BasePost


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

    auth: int
    authentication: str
    author: BaseUser
    content: str
    # message: Message
    hanserLike: bool
    hanserReply: bool
    last_reply_time: datetime
    last_reply_user: int
    post_time: datetime
    likes: int
    replies: int
    readings: int
    # 0普通帖子, 1 等级贴, 2 新人贴, 3生日帖
    type: int
    role: int
    exp: int
    tags: List[Tag]
    labels: List[Label]
    videos: List[str]
    liked: bool
    pictures: List[str]
    primaryPictures: List[str]


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
    labels: List[Label]
    # html格式
    content: str
    likes: int
    liked: bool
    pictures: List[str]
    primaryPictures: List[str]
    post_time: datetime
    readings: int
    replies: int
    tags: List[Tag]
    type: int

    valued: bool
    top: bool
    status: int

    showLocation: int
    favorite: bool
    isp: str
    location: str


class UserPostInfo(BasePost):
    """
    api:post/user/list
    获取的帖子信息
    """
    auth: int
    authentication: str
    avatar: int
    content: str
    id: int
    labels: List[Label]
    liked: bool
    likes: int
    nickname: str
    pictures: List[str]
    post_time: datetime
    primaryPictures: List[str]
    readings: int
    replies: int
    tags: List[Tag]
    title: str


if __name__ == '__main__':
    def get_subclasses(class_):
        classes = []
        for i in class_.__subclasses__():
            classes.append(i.__name__)
            if len(i.__subclasses__()) > 0:
                classes.extend(get_subclasses(i))
        return classes


    models = [RawModel.__name__]
    models.extend(get_subclasses(RawModel))

    print(models)

__all__ = [
    'RawModel', 'UploadKey', 'UploadResult', 'VideoInfo', 'UserData', 'SignInfo', 'LoginInfo', 'FollowResult',
    'ReplyResult', 'PostResult', 'NavInfo', 'LiveInfo', 'VersionInfo', 'LikeInfo', 'NoticeCount', 'Label',
    'Level', 'Tag', 'RawUser', 'BaseUser', 'User', 'PostUser', 'ChatList', 'BaseFloor', 'BasePost', 'PostInfo',
    'PostDetails', 'UserPostInfo', 'BaseLike', 'FloorLike', 'PostLike', 'BaseNotice', 'SystemNotice',
    'FollowNotice', 'SystemNoticeMessage', 'BaseReply', 'PostReply', 'FloorReply'
]
