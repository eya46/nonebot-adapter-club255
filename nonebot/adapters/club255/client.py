import json
import time
from datetime import datetime
from typing import Callable, Any, Optional, Protocol, Type, List, Union, Awaitable

from nonebot.internal.driver import Request, Response

from .bean import *
from .message import Message, MessageSegment, TextMsg, VideoMsg, ImageMsg, ActionFailed
from .types import T, UID, PID, FID, MID, HttpUrl


class API(Protocol):
    async def __call__(
            self, api: str, type_: Type[T], strict: bool = True, data_from: Optional[Union[str, Callable]] = None,
            **data: Any
    ) -> Any:
        ...


class CallAPI(Protocol):
    async def __call__(self, api: str, **data: Any) -> Any:
        ...


class Client:
    def __init__(
            self, api_get: API, api_post: API, call_api: CallAPI, request: Callable[[Request], Awaitable[Response]]
    ):
        self.call_api = call_api
        self.get = api_get
        self.post = api_post
        self.request = request

    async def get_live_info(self) -> LiveInfo:
        """
        获取hanser直播间信息
        :return:
        """
        return await self.get(f"forward/getRoomInfo", LiveInfo, data_from="data")

    async def get_version(self) -> VersionInfo:
        return await self.get("get_version", VersionInfo)

    async def get_level_list(self) -> List[Level]:
        return await self.get("level/list", List[Level])

    async def get_manager(self) -> List[RawUser]:
        return await self.get("user/manager", List[RawUser])

    async def get_nav_list(self) -> List[NavInfo]:
        """
        获取公告列表
        """
        return await self.get("post/nav-list", List[NavInfo])

    async def get_week_rank(self, page: int = 1, pageSize: int = 10) -> List[RawUserWithContribution]:
        return await self.get(
            f"contribution/rank?page={page}&pageSize={pageSize}&sort=week", List[RawUserWithContribution]
        )

    async def get_month_rank(self, page: int = 1, pageSize: int = 10) -> List[RawUserWithContribution]:
        return await self.get(
            f"contribution/rank?page={page}&pageSize={pageSize}&sort=month", List[RawUserWithContribution]
        )

    async def get_video_info(self, bv: str) -> VideoInfo:
        return await self.get(f"forward/get-video-info?bv={bv}", VideoInfo)

    async def get_post_list_brief(
            self, *, page: int = 1, _order: int = 1, _filter: int = 0, page_size=20
    ) -> List[BasePost]:
        """
        获取帖子列表，无详细内容
        :param page: 页数
        :param page_size: 帖子数量
        :param _order: 0->最后回复 1->最新发贴
        :param _filter: 帖子分类类型: 0->新帖 1->精华帖
        :return: List[PostInfo]
        """
        return await self.get(
            f"post/list?page={page}&pageSize={page_size}"
            f"&order={_order}&filter={_filter}", List[BasePost], data_from="result"
        )

    async def get_post_list_brief_by_time(self, *, page: int = 1, page_size=20) -> List[BasePost]:
        return await self.get_post_list_brief(page=page, _order=1, _filter=0, page_size=page_size)

    async def get_post_list_brief_by_reply(self, *, page: int = 1, page_size=20) -> List[BasePost]:
        return await self.get_post_list_brief(page=page, _order=0, _filter=0, page_size=page_size)

    async def get_nice_post_list_brief_by_time(self, *, page: int = 1, page_size=20) -> List[BasePost]:
        return await self.get_post_list_brief(page=page, _order=1, _filter=1, page_size=page_size)

    async def get_nice_post_list_brief_by_replay(self, *, page: int = 1, page_size=20) -> List[BasePost]:
        return await self.get_post_list_brief(page=page, _order=0, _filter=1, page_size=page_size)


class LoginClient(Client):
    async def get_post_list(self, *, page: int = 1, _order: int = 1, _filter: int = 0, page_size=20) -> List[PostInfo]:
        """
        获取帖子列表
        :param page: 页数
        :param page_size: 帖子数量
        :param _order: 0->最后回复 1->最新发贴
        :param _filter: 帖子分类类型: 0->新帖 1->精华帖
        :return: List[PostInfo]
        """
        return await self.get(
            f"post/list?page={page}&pageSize={page_size}"
            f"&order={_order}&filter={_filter}", List[PostInfo], data_from="result"
        )

    async def get_post_list_by_time(self, *, page: int = 1, page_size=20) -> List[PostInfo]:
        return await self.get_post_list(page=page, _order=1, _filter=0, page_size=page_size)

    async def get_post_list_by_reply(self, *, page: int = 1, page_size=20) -> List[PostInfo]:
        return await self.get_post_list(page=page, _order=0, _filter=0, page_size=page_size)

    async def get_nice_post_list_by_time(self, *, page: int = 1, page_size=20) -> List[PostInfo]:
        return await self.get_post_list(page=page, _order=1, _filter=1, page_size=page_size)

    async def get_nice_post_list_by_replay(self, *, page: int = 1, page_size=20) -> List[PostInfo]:
        return await self.get_post_list(page=page, _order=0, _filter=1, page_size=page_size)

    async def get_upload_key(self) -> UploadKey:
        return await self.get(f"auth/upload", UploadKey)

    async def upload_image(self, *, url: HttpUrl, self_uid: UID, img_msg: ImageMsg) -> UploadResult:
        if img_msg.url:
            return UploadResult.parse_obj({"err": 0, "id": "", "url": img_msg.url})
        key: UploadKey = await self.get_upload_key()

        file_name = f"{self_uid}.{int(time.time() * 1000)}.{key.sign}.{img_msg.type_}"

        data = {"data": {
            "id": key.id, "ts": key.ts, "sign": key.sign,
            "filename": file_name,
            "categories": datetime.now().strftime("%Y%m")
        }, "files": {"file": (file_name, img_msg.file)}}

        req = Request(
            "POST", url, **data
        )
        res = (await self.request(req))
        result = json.loads(res.content)

        try:
            return UploadResult.parse_obj(result)
        except Exception as e:
            raise ActionFailed(f"图片上传失败:{str(img_msg)} -> {result.get('msg', '未知错误')},{e}")

    async def dispose_msg(self, url: HttpUrl, self_uid: UID, message: Union[str, Message, MessageSegment]) -> Message:
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
                    m.data["file"] = await self.upload_image(self_uid=self_uid, url=url, img_msg=m)
        return message

    async def send_post(
            self, url: HttpUrl, self_uid: UID, title: str, message: Union[str, Message, MessageSegment]
    ) -> PostResult:
        message = await self.dispose_msg(url, self_uid, message)
        return await self.post("post/hansering", PostResult, title=title, content=message.xml())

    async def send_floor_reply(
            self, *, message: Union[str, Message, MessageSegment],
            pid: PID, fid: FID, upload_url: HttpUrl, self_uid: UID
    ) -> ReplyResult:
        # """
        # 过去式了，现在楼层回复也是富文本
        # 楼层回复只能发纯文本，并且无法换行，所以这个api不解析NextLine和非TextMsg
        # """
        # message = (
        #     message.extract_plain_text() if isinstance(message, Message) else Message(message).extract_plain_text()
        # )
        message = await self.dispose_msg(self_uid=self_uid, message=message, url=upload_url)
        return await self.post(
            f"reply/floor/{fid}", ReplyResult, **{"content": message, "postId": int(pid)}
        )

    async def send_post_reply(
            self, *, upload_url: HttpUrl, self_uid: UID, message: Union[str, Message, MessageSegment],
            pid: PID, author: UID
    ) -> ReplyResult:
        message = await self.dispose_msg(self_uid=self_uid, message=message, url=upload_url)
        return await self.post(
            f"reply/{pid}", ReplyResult,
            **{
                "author": int(author),
                "content": message.xml(),
                "postId": int(pid)
            }
        )

    async def like_post(self, pid: PID, uid: UID) -> LikeInfo:
        """
        点赞/取消点赞帖子
        :param pid: 帖子id
        :param uid: 作者id
        :return:
        """
        return await self.post(f"post/like/{pid}", LikeInfo, author=int(uid))

    async def get_user_data(self, uid: UID) -> UserData:
        """
        获取指定用户的积分，粉丝，收藏等信息
        :param uid: self_uid
        :return: UserData
        """
        return await self.get(f"user/data/count?self_uid={uid}", UserData, data_from="data")

    async def get_self_data(self, self_uid: UID) -> UserData:
        """
        获取自己的积分，粉丝，收藏等信息
        :return: UserData
        """
        return await self.get_user_data(self_uid)

    async def sign_now(self) -> SignInfo:
        return await self.get("sign", SignInfo)

    async def get_chat_list(self) -> List[ChatList]:
        return await self.get("chat/list", List[ChatList], data_from="list")

    async def get_chat_newest(self, uid: UID, mid: MID) -> dict:
        return await self.call_api(f"chat/chat-newest?self_uid={uid}&id={mid}", method="GET")

    async def get_self_info(self) -> User:
        # return await self.get_user_info(self.self_id)
        return await self.get("user/info", User, data_from="info")

    async def get_user_info(self, uid: UID) -> User:
        return await self.get(f"user/user-info?self_uid={uid}", User, data_from="info")

    async def get_newest_post_id(self) -> int:
        data = await self.get_post_list_by_time()
        # data.sort(key=lambda x:-x.id)
        return data[0].id

    async def get_newest_nice_post_id(self) -> int:
        data = await self.get_nice_post_list_by_time()
        # data.sort(key=lambda x:-x.id)
        return data[0].id

    async def get_vision_info(self) -> VersionInfo:
        return await self.get("version", VersionInfo)

    async def check_if_sign(self) -> bool:
        data = await self.call_api("sign/signed", method="GET")
        return data["signed"]

    async def get_sign_days(self) -> int:
        data = await self.call_api("sign/days", method="GET")
        return data["day"]

    async def get_reply_list(self, *, page: int = 1, pageSize: int = 20) -> List[BaseReply]:
        return await self.get(
            f"notice/reply/list?page={page}&pageSize={pageSize}",
            List[BaseReply], data_from="list"
        )

    async def get_like_list(self, *, page: int = 1, pageSize: int = 20) -> List[BaseLike]:
        """
        点赞列表
        :param page:
        :param pageSize: 由于点赞数量大，较小的club255_page_size可能会导致错失部分点赞信息
        :return:
        """
        return await self.get(
            f"notice/like/list?page={page}&pageSize={pageSize}",
            List[BaseLike], data_from="list"
        )

    async def get_self_level(self) -> Level:
        return await self.get("level/info", Level, data_from="levelInfo")

    async def get_next_level(self) -> Level:
        return await self.get("level/info", Level, data_from="nextLevel")

    async def get_notice_count(self) -> NoticeCount:
        return await self.get("notice/count", NoticeCount, data_from="count")

    async def get_system_notice_message(self, page: int = 1, pageSize=20) -> List[SystemNoticeMessage]:
        return await self.get(
            f"notice/system?page={page}&pageSize={pageSize}",
            List[SystemNoticeMessage], data_from="list"
        )

    async def get_site_notice(self, page: int = 0, pageSize=20) -> List[BaseNotice]:
        return await self.get(
            f"notice/site?page={page}&pageSize={pageSize}",
            List[BaseNotice], data_from="list"
        )

    async def get_post_details(self, pid: PID) -> PostDetails:
        return await self.get(f"post/detail/{pid}", PostDetails, data_from="info")

    async def follow_user(self, uid: UID) -> FollowResult:
        """
        关注/取关
        :param uid:
        :return: FollowResult relation：0:取关 1:关注
        """
        return await self.post(f"user/follow/{uid}", FollowResult, uid=int(uid))

    async def edit_post(
            self, url: HttpUrl, self_uid: UID, pid: PID, title: str, message: Union[str, Message, MessageSegment]
    ) -> Response:
        """
        修改帖子
        没有返回值
        """
        message = await self.dispose_msg(url, self_uid, message)
        return await self.call_api(f"post/edit/{pid}", method="POST", raw=True, title=title, content=message.xml())

    async def get_post_by_user(self, uid: UID, *, page: int = 1, page_size=20) -> List[UserPostInfo]:
        """
        获取帖子列表
        :param page_size: 帖子数量
        :param page: 页数
        :param uid: 用户id
        :return: List[PostInfo]
        """
        return await self.get(
            f"post/user/list?page={page}&pageSize={page_size}&self_uid={uid}",
            List[UserPostInfo], data_from="list"
        )

    async def set_floor_top(self, pid: PID, fid: FID) -> None:
        """
        这个api不会返回信息
        """
        return await self.call_api("reply/set-top", method="POST", raw=True, postId=pid, replyId=fid)


__all__ = [
    "Client", "LoginClient"
]
