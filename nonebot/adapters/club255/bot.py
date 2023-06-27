import json
from typing import Union, Any, List, Callable, Type, Optional

from nonebot import logger
from nonebot.adapters import Bot as RawBot
from nonebot.internal.adapter import Adapter
from nonebot.internal.driver import Response
from nonebot.message import handle_event
from pydantic import parse_obj_as

from .bean import *
from .client import Client, LoginClient
from .config import Config
from .event import Event, PostEvent, ReplyEvent, FloorReplyEvent
from .exception import SendNotImplemented, ActionFailed
from .message import Message, MessageSegment, ImageMsg
from .types import *


class BaseBot(RawBot):

    def __getattr__(self, name: str) -> Callable:
        if name.startswith("__") and name.endswith("__"):
            raise AttributeError(
                f"'{self.__class__.__name__}' object has no attribute '{name}'"
            )
        return getattr(self.client, name)

    async def handle_event(self, event: Event):
        await handle_event(self, event)

    def get_self_id(self) -> int:
        return int(self.self_id)

    async def send(self, event: "Event", message: Union[str, "Message", "MessageSegment"], **kwargs: Any) -> Any:
        if isinstance(self, UnLoginBot):
            raise SendNotImplemented("未登录的Bot无法发送消息")
        if isinstance(event, PostEvent):
            return await self.send_post_reply(message=message, pid=event.post.postId, author=event.post.id)
        elif isinstance(event, ReplyEvent):
            if isinstance(event, FloorReplyEvent):
                return await self.send_floor_reply(
                    message=message, pid=event.postId, fid=event.floor.floorId
                )
            else:
                return await self.send_post_reply(
                    message=message, pid=event.postId, author=event.user.uid
                )
        else:
            raise SendNotImplemented(f"{event.__class__}({event.get_event_name()}) -> 未实现该Event的send")

    async def call_api(self, api: str, **data: Any) -> Any:
        if data.get("raw") and data.get("raw") is True:
            return await super().call_api(api, **data)
        resp: Response = await super().call_api(api, **data)
        data: bytes = resp.content
        try:
            return json.loads(data)
        except Exception as e:
            logger.error(f"调用api失败,code:{resp.status_code}")
            raise e

    async def call_api_get(self, api: str, **data: Any) -> Any:
        return await self.call_api(api, method=data.pop("method") if data.get("method") else "GET", **data)

    async def call_api_post(self, api: str, **data: Any) -> Any:
        return await self.call_api(api, method=data.pop("method") if data.get("method") else "POST", **data)

    async def api_post_to_type(
            self, api: str, type_: Type[T], strict=True, data_from: Optional[Union[str, Callable]] = None, **data: Any
    ) -> T:
        res = await self.call_api_post(api, **data)
        if strict and res.get("code", 0) != 0:
            raise ActionFailed(f"API调用失败: {res.get('msg', '未知错误')}")
        return parse_obj_as(
            type_, (
                res[data_from] if isinstance(data_from, str) else data_from(res)
            ) if data_from else res
        )

    async def api_get_to_type(
            self, api: str, type_: Type[T], strict: bool = True, data_from: Optional[Union[str, Callable]] = None,
            **data: Any
    ) -> T:
        res = await self.call_api_get(api, **data)
        if strict and res.get("code", 0) != 0:
            raise ActionFailed(f"API调用失败: {res.get('msg', '未知错误')}")
        return parse_obj_as(
            type_, (
                res[data_from] if isinstance(data_from, str) else data_from(res)
            ) if data_from else res
        )

    def __init__(self, *, adapter: "Adapter", self_id: str, header: dict, config: Config):
        super().__init__(adapter, self_id)
        self.header = header
        self._config = config
        self.client = Client(self.api_get_to_type, self.api_post_to_type, self.call_api, self.adapter.request)

    @property
    def config(self) -> Config:
        return self._config

    def set_token(self, token: str):
        self.header["cookie"] = f"token={token};"

    async def login(self, account: str = "", password: str = "") -> LoginInfo:
        data = await self.call_api(
            "auth/login", method="POST", **{
                "account": account or self.config.club255_account,
                "password": password or self.config.club255_password
            }
        )

        if data["code"] != 0:
            logger.error(f"{self.get_name()} | {account} | 登录失败:{data.get('msg', '未知原因')}")
        else:
            logger.info(f"{self.get_name()} | {account} | 登录成功:{data['self_uid']}")

        if isinstance(self, UnLoginBot):
            self.set_token(data["token"])
            self.adapter.bot_disconnect(self)
            self.adapter.bot_connect(Bot(
                adapter=self.adapter, self_id=str(data["uid"]), header=self.header, config=self.config
            ))

        return LoginInfo.parse_obj(data)

    async def get_post_list_brief(
            self, *, page: int = 1, _order: int = 1, _filter: int = 0, page_size=0
    ) -> List[BasePost]:
        datas = await self.client.get_post_list_brief(
            page=page, _order=_order, _filter=_filter, page_size=page_size or self.config.club255_page_size
        )
        if self.config.club255_receive_me:
            return datas
        else:
            return list(filter(
                lambda x: x.author.uid != self.self_id,
                datas
            ))

    async def get_post_list_brief_by_time(self, *, page: int = 1, page_size=0) -> List[BasePost]:
        return await self.get_post_list(page=page, _order=1, _filter=0, page_size=page_size)

    async def get_post_list_brief_by_reply(self, *, page: int = 1, page_size=0) -> List[BasePost]:
        return await self.get_post_list(page=page, _order=0, _filter=0, page_size=page_size)

    async def get_nice_post_list_brief_by_time(self, *, page: int = 1, page_size=0) -> List[BasePost]:
        return await self.get_post_list_brief(page=page, _order=1, _filter=1, page_size=page_size)

    async def get_nice_post_list_brief_by_replay(self, *, page: int = 1, page_size=0) -> List[BasePost]:
        return await self.get_post_list_brief(page=page, _order=0, _filter=1, page_size=page_size)


class UnLoginBot(BaseBot):
    def __init__(self, *, adapter: "Adapter", self_id: str = "2550505", header: dict, config: Config):
        """
        未登录Bot默认的id是2550505
        """
        super().__init__(adapter=adapter, self_id=self_id, header=header, config=config)


class Bot(BaseBot):
    def __init__(self, *, adapter: "Adapter", self_id: str, header: dict, config: Config):
        """
        已登录Bot的id是用户的uid
        """
        super().__init__(adapter=adapter, self_id=self_id, header=header, config=config)
        self.client = LoginClient(self.api_get_to_type, self.api_post_to_type, self.call_api, self.adapter.request)

    async def get_self_data(self) -> UserData:
        """
        获取自己的积分，粉丝，收藏等信息
        :return: UserData
        """
        return await self.get_user_data(self.self_id)

    async def upload_image(self, *, img_msg: ImageMsg) -> UploadResult:
        return await self.client.upload_image(url=self.config.club255_upload_api, self_uid=self.self_id,
                                              img_msg=img_msg)

    async def dispose_msg(self, *, message: Union[str, Message, MessageSegment]) -> Message:
        return await self.client.dispose_msg(url=self.config.club255_upload_api, self_uid=self.self_id, message=message)

    async def send_post(
            self, title: str, message: Union[str, Message, MessageSegment]
    ) -> PostResult:
        return await self.client.send_post(
            title=title, url=self.config.club255_upload_api, self_uid=self.self_id, message=message
        )

    async def send_post_reply(
            self, *, author: UID, message: Union[str, Message, MessageSegment], pid: PID
    ) -> ReplyResult:
        return await self.client.send_post_reply(
            upload_url=self.config.club255_upload_api, self_uid=self.self_id, pid=pid, message=message, author=author
        )

    async def send_floor_reply(
            self, *, message: Union[str, Message, MessageSegment], pid: PID, fid: FID
    ) -> ReplyResult:
        return await self.client.send_floor_reply(
            upload_url=self.config.club255_upload_api, self_uid=self.self_id, pid=pid, fid=fid, message=message
        )

    async def get_post_list(self, *, page: int = 1, _order: int = 1, _filter: int = 0, page_size=0) -> List[PostInfo]:
        datas = await self.client.get_post_list(
            page=page, _order=_order, _filter=_filter, page_size=page_size or self.config.club255_page_size
        )
        if self.config.club255_receive_me:
            return datas
        else:
            return list(filter(
                lambda x: x.author.uid != self.self_id,
                datas
            ))

    async def get_post_list_by_time(self, *, page: int = 1, page_size=0) -> List[PostInfo]:
        return await self.get_post_list(page=page, _order=1, _filter=0, page_size=page_size)

    async def get_post_list_by_reply(self, *, page: int = 1, page_size=0) -> List[PostInfo]:
        return await self.get_post_list(page=page, _order=0, _filter=0, page_size=page_size)

    async def get_nice_post_list_by_time(self, *, page: int = 1, page_size=0) -> List[PostInfo]:
        return await self.get_post_list(page=page, _order=1, _filter=1, page_size=page_size)

    async def get_nice_post_list_by_replay(self, *, page: int = 1, page_size=0) -> List[PostInfo]:
        return await self.get_post_list(page=page, _order=0, _filter=1, page_size=page_size)

    def get_token(self) -> str:
        return self.header["cookie"].split(";")[0].split("=")[1]

    async def get_post_by_user(self, uid: UID, *, page: int = 1, page_size=0) -> List[UserPostInfo]:
        """
        获取帖子列表
        :param page_size: 帖子数量
        :param page: 页数
        :param uid: 用户id
        :return: List[PostInfo]
        """
        return await self.client.get_post_by_user(
            uid=uid, page=page, page_size=page_size or self.config.club255_page_size
        )

    async def get_reply_list(self, *, page: int = 1, pageSize: int = 0) -> List[BaseReply]:
        return await self.client.get_reply_list(page=page, pageSize=pageSize or self.config.club255_page_size)

    async def get_like_list(self, *, page: int = 1, pageSize: int = 0) -> List[BaseLike]:
        """
        点赞列表
        :param page:
        :param pageSize: 由于点赞数量大，较小的club255_page_size可能会导致错失部分点赞信息
        :return:
        """
        return await self.client.get_like_list(page=page, pageSize=pageSize or self.config.club255_page_size)


__all__ = ["BaseBot", "UnLoginBot", "Bot"]
