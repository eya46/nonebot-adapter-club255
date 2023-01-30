import json
import time
from datetime import datetime
from typing import Union, Any, List

from nonebot import logger
from nonebot.adapters import Bot as BaseBot
from nonebot.internal.adapter import Adapter
from nonebot.internal.driver import Request
from nonebot.message import handle_event
from pydantic import parse_obj_as

from .bean import *
from .config import Config
from .event import Event, PostEvent, ReplyEvent, FloorReplyEvent
from .exceptions import SendNotImplemented
from .message import Message, MessageSegment, TextMsg, VideoMsg, ImageMsg
from .types import *


class Bot(BaseBot):
    def get_self_id(self) -> int:
        return int(self.self_id)

    async def handle_event(self, event: Event):
        await handle_event(self, event)

    async def call_api(self, api: str, **data: Any) -> Any:
        data = (await super().call_api(api, **data)).content
        try:
            return json.loads(data)
        except Exception as e:
            logger.exception(e)
            logger.error("解析api失败")
            return data

    async def send(self, event: "Event", message: Union[str, "Message", "MessageSegment"], **kwargs: Any) -> Any:
        if isinstance(event, PostEvent):
            return await self.send_post_reply(message=message, pid=event.post.postId, uid=event.post.id)
        elif isinstance(event, ReplyEvent):
            if isinstance(event, FloorReplyEvent):
                return await self.send_floor_reply(
                    message=message, pid=event.postId, fid=event.floor.floorId
                )
            else:
                return await self.send_post_reply(
                    message=message, pid=event.postId, uid=event.user.uid
                )
        else:
            raise SendNotImplemented(f"{event.__class__}({event.get_event_name()}) -> 未实现该Event的send")

    async def set_floor_top(self, pid: PID, fid: FID) -> None:
        """
        不知道为啥，这个api不会返回信息
        """
        return await self.call_api("reply/set-top", method="POST", postId=pid, replyId=fid)

    async def edit_post(self, pid: PID, title: str, message: Union[str, Message, MessageSegment]) -> dict:
        message = message.xml() if isinstance(message, Message) else Message(message).xml()
        return await self.call_api(f"post/edit/{pid}", method="POST", title=title, content=message)

    async def get_video_info(self, bv: str) -> VideoInfo:
        data = await self.call_api(f"forward/get-video-info?bv={bv}", method="GET")
        return VideoInfo.parse_obj(data)

    async def detail_msg(self, message: Union[str, Message, MessageSegment]) -> Message:
        if isinstance(message, str):
            # 避免解析文本中的[]
            return Message(TextMsg(message))
        else:
            if isinstance(message, MessageSegment):
                message = Message(message)
            for m in message:
                if isinstance(m, VideoMsg) and not m.check():
                    _ = await self.get_video_info(m.bv)
                    m.data["title"] = _.title
                    m.data["cover"] = _.cover
                    continue
                elif isinstance(m, ImageMsg) and not m.check():
                    m.data["file"] = await self.upload_image(m)
        return message

    async def send_post(self, title: str, message: Union[str, Message, MessageSegment]) -> PostResult:
        message = await self.detail_msg(message)
        data = await self.call_api("post/hansering", method="POST", title=title, content=message.xml())
        return PostResult.parse_obj(data)

    async def send_floor_reply(
            self, *, message: Union[str, Message, MessageSegment],
            pid: PID, fid: FID
    ) -> ReplyResult:
        """
        楼层回复只能发纯文本，并且无法换行，所以这个api不解析NextLine和非TextMsg
        """
        message = (
            message.extract_plain_text() if isinstance(message, Message) else Message(message).extract_plain_text()
        )
        data = await self.call_api(
            f"reply/floor/{fid}", method="POST",
            **{
                "content": message,
                "postId": int(pid)
            }
        )
        return ReplyResult.parse_obj(data)

    async def send_post_reply(
            self, *, message: Union[str, Message, MessageSegment],
            pid: PID, uid: UID
    ) -> ReplyResult:
        message = await self.detail_msg(message)
        data = await self.call_api(
            f"reply/{pid}", method="POST",
            **{
                "author": int(uid),
                "content": message.xml(),
                "postId": int(pid)
            }
        )
        return ReplyResult.parse_obj(data)

    async def upload_image(self, /, img_msg: ImageMsg) -> UploadResult:
        if img_msg.url:
            return UploadResult.parse_obj({"err": 0, "id": "", "url": img_msg.url})
        key: UploadKey = await self.get_upload_key()

        file_name = f"{self.self_id}.{int(time.time() * 1000)}.{key.sign}.{img_msg.type_}"

        data = {"data": {
            "id": key.id, "ts": key.ts, "sign": key.sign,
            "filename": file_name,
            "categories": datetime.now().strftime("%Y%m")
        }, "files": {"file": (file_name, img_msg.file)}}

        req = Request(
            "POST", self.config.club255_upload_api, **data
        )
        res = (await self.adapter.request(req))
        result = json.loads(res.content)

        try:
            return UploadResult.parse_obj(result)
        except Exception as e:
            logger.error(f"图片上传失败:{str(img_msg)} -> {result.get('msg')}")
            raise e

    async def get_upload_key(self) -> UploadKey:
        data = await self.call_api(f"auth/upload", method="GET")
        return UploadKey.parse_obj(data)

    async def get_post_by_user(self, uid: UID, *, page: int = 1, page_size=0) -> List[UserPostInfo]:
        """
        获取帖子列表
        :param page_size: 帖子数量
        :param page: 页数
        :param uid: 用户id
        :return: List[PostInfo]
        """
        data = await self.call_api(
            f"post/user/list?page={page}&pageSize={page_size or self.config.club255_page_size}&uid={uid}", method="GET"
        )
        return parse_obj_as(
            List[UserPostInfo],
            data["list"]
        )

    async def get_post_details(self, pid: PID) -> PostDetails:
        data = await self.call_api(f"post/detail/{pid}", method="GET")
        return PostDetails.parse_obj(data["info"])

    async def follow_user(self, uid: UID) -> FollowResult:
        """
        关注/取关
        :param uid:
        :return: FollowResult relation：0:取关 1:关注
        """
        data = await self.call_api(f"user/follow/{uid}", method="POST", uid=int(uid))
        return FollowResult.parse_obj(data)

    async def get_notice_count(self) -> NoticeCount:
        data = await self.call_api("notice/count", method="GET")
        return NoticeCount.parse_obj(data["count"])

    async def get_system_notice_message(self, page: int = 1, pageSize=20) -> List[SystemNoticeMessage]:
        data = await self.call_api(f"notice/site?page={page}&pageSize={pageSize}", method="GET")
        return parse_obj_as(List[SystemNoticeMessage], data["list"])

    async def get_level_list(self) -> List[Level]:
        data = await self.call_api("level/list", method="GET")
        return parse_obj_as(List[Level], data["list"])

    async def get_site_notice(self, page: int = 0, pageSize=20) -> List[BaseNotice]:
        data = await self.call_api(f"notice/site?page={page}&pageSize={pageSize}", method="GET")
        return parse_obj_as(List[BaseNotice], data["list"])

    async def get_self_level(self) -> Level:
        data = await self.call_api("level/info", method="GET")
        return Level.parse_obj(data["levelInfo"])

    async def get_next_level(self) -> Level:
        data = await self.call_api("level/info", method="GET")
        return Level.parse_obj(data["nextLevel"])

    async def get_nav_list(self) -> List[NavInfo]:
        data = await self.call_api("post/nav-list", method="GET")
        return parse_obj_as(List[NavInfo], data["list"])

    async def like_post(self, pid: PID, uid: UID) -> LikeInfo:
        """
        点赞/取消点赞帖子
        :param pid: 帖子id
        :param uid: 作者id
        :return:
        """
        data = await self.call_api(f"post/like/{pid}", method="POST", author=int(uid))
        return LikeInfo.parse_obj(data)

    async def get_user_data(self, uid: UID) -> UserData:
        """
        获取指定用户的积分，粉丝，收藏等信息
        :param uid: uid
        :return: UserData
        """
        data = await self.call_api(f"user/data/count?uid={uid}", method="GET")
        return UserData.parse_obj(data["data"])

    async def get_self_data(self) -> UserData:
        """
        获取自己的积分，粉丝，收藏等信息
        :return: UserData
        """
        return await self.get_user_data(self.self_id)

    async def sign_now(self) -> SignInfo:
        data = await self.call_api(f"sign", method="GET")
        return SignInfo.parse_obj(data)

    async def get_chat_list(self) -> List[ChatList]:
        data = (
            await self.call_api("chat/list", method="GET")
        )
        return parse_obj_as(List[ChatList], data["list"])

    async def get_chat_newest(self, uid: UID, mid: MID) -> dict:
        return await self.call_api(f"chat/chat-newest?uid={uid}&id={mid}", method="GET")

    async def get_self_info(self) -> User:
        # return await self.get_user_info(self.self_id)
        return User.parse_obj((await self.call_api("user/info", method="GET"))["info"])

    async def get_user_info(self, uid: UID) -> User:
        return User.parse_obj((await self.call_api(f"user/user-info?uid={uid}", method="GET"))["info"])

    async def get_newest_post_id(self) -> int:
        data = await self.get_post_list_by_time()
        # data.sort(key=lambda x:-x.id)
        return data[0].id

    async def get_newest_nice_post_id(self) -> int:
        data = await self.get_nice_post_list_by_time()
        # data.sort(key=lambda x:-x.id)
        return data[0].id

    async def get_vision_info(self) -> VersionInfo:
        data = await self.call_api("version", method="GET")
        return VersionInfo.parse_obj(data)

    async def check_if_sign(self) -> bool:
        data = await self.call_api("sign/signed", method="GET")
        return data["signed"]

    async def get_sign_days(self) -> int:
        data = await self.call_api("sign/days", method="GET")
        return data["day"]

    async def get_admin(self) -> List[RawUser]:
        """
        获取管理员
        :return: List[RawUser]
        """
        data = await self.call_api("user/manager", method="GET")
        return parse_obj_as(List[RawUser], data["list"])

    async def get_manager(self) -> List[RawUser]:
        """
        获取管理员
        :return: List[RawUser]
        """
        return await self.get_admin()

    async def get_live_info(self) -> LiveInfo:
        """
        获取hanser直播间信息
        :return:
        """
        data = await self.call_api(f"forward/getRoomInfo", method="GET")
        return LiveInfo.parse_obj(data["data"])

    async def get_reply_list(self, *, page: int = 1, pageSize: int = 0) -> List[BaseReply]:
        data = await self.call_api(
            f"notice/reply/list?page={page}&pageSize={pageSize or self.config.club255_page_size}",
            method="GET"
        )
        return parse_obj_as(List[BaseReply], data["list"])

    async def get_like_list(self, *, page: int = 1, pageSize: int = 0) -> List[BaseLike]:
        """
        点赞列表
        :param page:
        :param pageSize: 由于点赞数量大，较小的club255_page_size可能会导致错失部分点赞信息
        :return:
        """
        data = await self.call_api(
            f"notice/like/list?page={page}&pageSize={pageSize or self.config.club255_page_size}",
            method="GET"
        )
        return parse_obj_as(List[BaseLike], data["list"])

    async def get_post_list(self, *, page: int = 1, _order: int = 1, _filter: int = 0, page_size=0) -> List[PostInfo]:
        """
        获取帖子列表
        :param page: 页数
        :param page_size: 帖子数量
        :param _order: 0->最后回复 1->最新发贴
        :param _filter: 帖子分类类型: 0->新帖 1->精华帖
        :return: List[PostInfo]
        """
        data = await self.call_api(
            f"post/list?page={page}&pageSize={page_size or self.config.club255_page_size}"
            f"&order={_order}&filter={_filter}", method="GET"
        )
        datas = parse_obj_as(
            List[PostInfo],
            data["result"]
        )
        if self.config.club255_receive_me:
            return datas
        else:
            return list(filter(
                lambda x: x.author.uid != self.self_id,
                datas
            ))

    async def get_post_list_by_time(self, *, page: int = 1, _order=1, page_size=0) -> List[PostInfo]:
        return await self.get_post_list(page=page, _order=_order, _filter=0, page_size=page_size)

    async def get_post_list_by_reply(self, *, page: int = 1, _order=0, page_size=0) -> List[PostInfo]:
        return await self.get_post_list(page=page, _order=_order, _filter=0, page_size=page_size)

    async def get_nice_post_list_by_time(self, *, page: int = 1, _order=1, page_size=0) -> List[PostInfo]:
        return await self.get_post_list(page=page, _order=_order, _filter=1, page_size=page_size)

    async def get_nice_post_list_by_replay(self, *, page: int = 1, _order=0, page_size=0) -> List[PostInfo]:
        return await self.get_post_list(page=page, _order=_order, _filter=1, page_size=page_size)

    def __init__(self, adapter: "Adapter", self_id: str, header: dict, config: Config):
        super().__init__(adapter, self_id)
        self.header = header
        self._config = config

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
            logger.debug(f"{self.get_name()} | {account} | 登录成功:{data['uid']}")

        return LoginInfo.parse_obj(data)
