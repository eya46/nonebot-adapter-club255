from typing import Any
from collections.abc import Callable

from pydantic import HttpUrl
from nonebot.adapters import Bot as RawBot
from nonebot.internal.driver import Response
from nonebot.internal.adapter import Adapter

from .bean import (
    User,
    Level,
    NavInfo,
    RawUser,
    BaseLike,
    BasePost,
    ChatList,
    LikeInfo,
    LiveInfo,
    PostInfo,
    SignInfo,
    UserData,
    BaseReply,
    LoginInfo,
    UploadKey,
    VideoInfo,
    BaseNotice,
    PostResult,
    NoticeCount,
    PostDetails,
    ReplyResult,
    VersionInfo,
    FollowResult,
    UploadResult,
    UserPostInfo,
    SystemNoticeMessage,
    RawUserWithContribution,
)
from .event import Event
from .types import FID, MID, PID, UID, T
from .config import Config
from .message import Message, ImageMsg, MessageSegment

class BaseBot(RawBot):
    async def handle_event(self, event: Event): ...
    async def send(
        self,
        event: Event,
        message: str | Message | MessageSegment,
        **kwargs: Any,
    ) -> Any: ...
    async def get_version(self) -> VersionInfo: ...
    async def get_level_list(self) -> list[Level]: ...
    async def get_manager(self) -> list[RawUser]: ...
    async def get_nav_list(self) -> list[NavInfo]:
        """
        获取公告列表
        """
        ...

    async def get_week_rank(self, page: int = 1, pageSize: int = 10) -> list[RawUserWithContribution]: ...
    async def get_month_rank(self, page: int = 1, pageSize: int = 10) -> list[RawUserWithContribution]: ...
    async def get_video_info(self, bv: str) -> VideoInfo: ...
    async def get_live_info(self) -> LiveInfo:
        """
        获取hanser直播间信息
        :return: LiveInfo
        """
        ...

    async def get_post_list_brief(
        self, *, page: int = 1, _order: int = 1, _filter: int = 0, page_size=0
    ) -> list[BasePost]: ...
    async def get_post_list_brief_by_time(self, *, page: int = 1, page_size=0) -> list[BasePost]: ...
    async def get_post_list_brief_by_reply(self, *, page: int = 1, page_size=0) -> list[BasePost]: ...
    async def get_nice_post_list_brief_by_time(self, *, page: int = 1, page_size=0) -> list[BasePost]: ...
    async def get_nice_post_list_brief_by_replay(self, *, page: int = 1, page_size=0) -> list[BasePost]: ...
    def __getattr__(self, name: str) -> Callable: ...
    def get_self_id(self) -> int: ...
    async def call_api(self, api: str, **data: Any) -> Any: ...
    async def call_api_get(self, api: str, **data: Any) -> Any: ...
    async def call_api_post(self, api: str, **data: Any) -> Any: ...
    async def api_post_to_type(
        self,
        api: str,
        type_: type[T],
        strict=True,
        data_from: str | Callable | None = None,
        **data: Any,
    ) -> T: ...
    async def api_get_to_type(
        self,
        api: str,
        type_: type[T],
        strict: bool = True,
        data_from: str | Callable | None = None,
        **data: Any,
    ) -> T: ...
    def __init__(self, *, adapter: Adapter, self_id: str, header: dict, config: Config): ...
    @property
    def config(self) -> Config: ...
    def set_token(self, token: str): ...
    async def login(self, account: str = "", password: str = "") -> LoginInfo: ...

class UnLoginBot(BaseBot):
    def __init__(
        self,
        *,
        adapter: Adapter,
        self_id: str = "2550505",
        header: dict,
        config: Config,
    ):
        """
        未登录Bot默认的id是2550505
        """
        ...

class Bot(BaseBot):
    def __init__(self, *, adapter: Adapter, self_id: str, header: dict, config: Config): ...
    async def get_self_data(self) -> UserData: ...
    async def upload_image(self, *, img_msg: ImageMsg) -> UploadResult: ...
    async def dispose_msg(self, *, message: str | Message | MessageSegment) -> Message: ...
    async def send_post(self, title: str, message: str | Message | MessageSegment) -> PostResult: ...
    async def send_post_reply(
        self, *, author: UID, message: str | Message | MessageSegment, pid: PID
    ) -> ReplyResult: ...
    async def send_floor_reply(self, *, message: str | Message | MessageSegment, pid: PID, fid: FID) -> ReplyResult: ...
    async def get_post_list(
        self, *, page: int = 1, _order: int = 1, _filter: int = 0, page_size=0
    ) -> list[PostInfo]: ...
    async def get_post_list_by_time(self, *, page: int = 1, page_size=0) -> list[PostInfo]: ...
    async def get_post_list_by_reply(self, *, page: int = 1, page_size=0) -> list[PostInfo]: ...
    async def get_nice_post_list_by_time(self, *, page: int = 1, page_size=0) -> list[PostInfo]: ...
    async def get_nice_post_list_by_replay(self, *, page: int = 1, page_size=0) -> list[PostInfo]: ...
    def get_token(self) -> str: ...
    async def get_post_by_user(self, uid: UID, *, page: int = 1, page_size=0) -> list[UserPostInfo]: ...
    async def get_reply_list(self, *, page: int = 1, pageSize: int = 0) -> list[BaseReply]: ...
    async def get_like_list(self, *, page: int = 1, pageSize: int = 0) -> list[BaseLike]: ...
    async def get_upload_key(self) -> UploadKey: ...
    async def like_post(self, pid: PID, uid: UID) -> LikeInfo:
        """
        点赞/取消点赞帖子
        :param pid: 帖子id
        :param uid: 作者id
        :return:
        """
        ...

    async def get_user_data(self, uid: UID) -> UserData:
        """
        获取指定用户的积分，粉丝，收藏等信息
        :param uid: self_uid
        :return: UserData
        """
        ...

    async def sign_now(self) -> SignInfo: ...
    async def get_chat_list(self) -> list[ChatList]: ...
    async def get_chat_newest(self, uid: UID, mid: MID) -> dict: ...
    async def get_self_info(self) -> User: ...
    async def get_user_info(self, uid: UID) -> User: ...
    async def get_newest_post_id(self) -> int: ...
    async def get_newest_nice_post_id(self) -> int: ...
    async def get_vision_info(self) -> VersionInfo: ...
    async def check_if_sign(self) -> bool: ...
    async def get_sign_days(self) -> int: ...
    async def get_self_level(self) -> Level: ...
    async def get_next_level(self) -> Level: ...
    async def get_notice_count(self) -> NoticeCount: ...
    async def get_system_notice_message(self, page: int = 1, pageSize=20) -> list[SystemNoticeMessage]: ...
    async def get_site_notice(self, page: int = 0, pageSize=20) -> list[BaseNotice]: ...
    async def get_post_details(self, pid: PID) -> PostDetails: ...
    async def follow_user(self, uid: UID) -> FollowResult:
        """
        关注/取关
        :param uid:
        :return: FollowResult relation：0:取关 1:关注
        """
        ...

    async def edit_post(
        self,
        url: HttpUrl,
        self_uid: UID,
        pid: PID,
        title: str,
        message: str | Message | MessageSegment,
    ) -> Response:
        """
        修改帖子
        没有返回值
        """
        ...

    async def set_floor_top(self, pid: PID, fid: FID) -> None:
        """
        这个api不会返回信息
        """
        ...

__all__ = ["BaseBot", "UnLoginBot", "Bot"]
