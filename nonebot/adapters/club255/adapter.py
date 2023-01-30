import asyncio
import json
import traceback
import uuid
from typing import Any, List, Optional, Type
from urllib.parse import urljoin

from nonebot import Driver, logger
from nonebot.adapters import Adapter as BaseAdapter
from nonebot.drivers import URL, Request, Response
from nonebot.internal.driver import ForwardDriver

from .bot import Bot
from .config import Config
from .event import Event, NicePostEvent, NewPostEvent, FollowNoticeEvent, SystemNoticeEvent, \
    SystemNoticeMessageEvent, PostLikeNoticeEvent, FloorLikeNoticeEvent, OnLiveNoticeEvent


class Adapter(BaseAdapter):
    def __init__(self, driver: Driver, **kwargs: Any):
        super().__init__(driver, **kwargs)
        self.club255_config: Config = Config(**self.config.dict())
        self.tasks: List["asyncio.Task"] = []
        self._setup()

    async def sleep(self):
        await asyncio.sleep(self.club255_config.club255_interval)

    @classmethod
    def build_event(cls, event: Type[Event], data: Any, bot: Bot) -> Optional[Event]:
        data = {**data.raw_data, "self_uid": bot.get_self_id()}
        return event.parse_obj(data)

    @classmethod
    def get_name(cls) -> str:
        return "Club255"

    async def _call_api(self, bot: Bot, api: str, **data: Any) -> Response:
        if (method := data.pop("method")) == "GET":
            return await self.request(Request(
                method, urljoin(self.club255_config.club255_url, api), params=data, headers=bot.header
            ))
        else:
            return await self.request(Request(
                method, urljoin(self.club255_config.club255_url, api), json=data, headers=bot.header
            ))

    async def _get_token(self, account: str, password: str) -> Optional[dict]:
        data = json.loads((await self.request(Request(
            "POST", urljoin(self.club255_config.club255_url, "auth/login"), json={
                "account": account, "password": password
            }
        ))).content)

        if data["code"] != 0:
            logger.error(f"{self.get_name()} | {account}| 登录失败:{data.get('msg', '未知原因')}")
            return None
        logger.debug(f"{self.get_name()} | {account} | 登录成功:{data['uid']}")

        return data

    async def _on_live_get(self, bot: Bot):
        first = self.club255_config.club255_run_now
        status = 0
        while True:
            if first:
                first = False
            else:
                await self.sleep()
            try:
                live_info = await bot.get_live_info()
                if live_info.live_status == status:
                    await self.sleep()
                    return
                else:
                    status = live_info.live_status
                if live_info.live_status != 1:
                    continue
                event = self.build_event(OnLiveNoticeEvent, live_info, bot)
                await bot.handle_event(
                    event
                )
            except Exception as e:
                logger.error(f"{self.get_name()}:{bot.self_id} -> 获取live事件失败:{e}")
                traceback.print_exc()

    async def _notice_count_get(self, bot: Bot):
        first = self.club255_config.club255_run_now
        while True:
            if first:
                first = False
            else:
                await self.sleep()
            try:
                events = []
                notices = await bot.get_notice_count()
                if notices.notice > 0:
                    site_notice = (await bot.get_site_notice())[:notices.notice]
                    follow_notice = [i.to_follow_notice() for i in site_notice if i.to_follow_notice()]
                    system_notice = [i.to_system_notice() for i in site_notice if i.to_system_notice()]
                    events.extend([self.build_event(FollowNoticeEvent, i, bot) for i in follow_notice])
                    events.extend([self.build_event(SystemNoticeEvent, i, bot) for i in system_notice])
                if notices.message > 0:
                    system_notice_message = (await bot.get_system_notice_message())[:notices.message]
                    events.extend([self.build_event(SystemNoticeMessageEvent, i, bot) for i in system_notice_message])
                if notices.likes > 0:
                    like_list = (await bot.get_like_list())[:notices.likes]
                    floor_like_list = [i.to_floor_like() for i in like_list if i.to_floor_like()]
                    post_like_list = [i.to_post_like() for i in like_list if i.to_post_like()]
                    events.extend([self.build_event(FloorLikeNoticeEvent, i, bot) for i in floor_like_list])
                    events.extend([self.build_event(PostLikeNoticeEvent, i, bot) for i in post_like_list])
                if notices.replies > 0:
                    reply_list = (await bot.get_reply_list())[:notices.replies]
                    floor_reply_list = [i.to_floor_reply() for i in reply_list if i.to_floor_reply()]
                    post_reply_list = [i.to_post_reply() for i in reply_list if i.to_post_reply()]
                    events.extend([self.build_event(FloorLikeNoticeEvent, i, bot) for i in floor_reply_list])
                    events.extend([self.build_event(PostLikeNoticeEvent, i, bot) for i in post_reply_list])

                await asyncio.gather(*map(bot.handle_event, events))
            except Exception as e:
                logger.error(f"{self.get_name()}:{bot.self_id} -> 获取notice事件失败:{e}")

            await self.sleep()

    async def _new_nice_post_get(self, bot: Bot):
        first = self.club255_config.club255_run_now
        newest_id = 0 if first else await bot.get_newest_nice_post_id()
        while True:
            if first:
                first = False
            else:
                await self.sleep()
            try:
                post_list = list(filter(
                    lambda x: x.id > newest_id,
                    await bot.get_nice_post_list_by_time()
                ))
                if len(post_list) == 0:
                    continue
                if post_list[0].id > newest_id:
                    newest_id = post_list[0].id
                events = [self.build_event(NicePostEvent, i, bot) for i in post_list]
                await asyncio.gather(*map(bot.handle_event, events))
            except Exception as e:
                logger.error(f"{self.get_name()}:{bot.self_id} -> 获取新精华帖事件失败:{e}")
                traceback.print_exc()

    async def _new_post_get(self, bot: Bot):
        first = self.club255_config.club255_run_now
        newest_id = 0 if first else await bot.get_newest_post_id()
        while True:
            if first:
                first = False
            else:
                await self.sleep()
            try:
                post_list = list(filter(
                    lambda x: x.id > newest_id,
                    await bot.get_post_list_by_time()
                ))
                if len(post_list) == 0:
                    continue
                if post_list[0].id > newest_id:
                    newest_id = post_list[0].id
                events = [self.build_event(NewPostEvent, i, bot) for i in post_list]
                await asyncio.gather(*map(bot.handle_event, events))
            except Exception as e:
                logger.error(f"{self.get_name()}:{bot.self_id} -> 获取新帖事件失败:{e}")
                traceback.print_exc()

    async def _keep_get_event(self, bot: Bot):
        funcs = [
            self._new_post_get(bot), self._new_nice_post_get(bot),
            self._notice_count_get(bot), self._on_live_get(bot)
        ]
        await asyncio.gather(*funcs)

    async def _create_bot(self, account: str, password: str):
        bot: Optional[Bot]

        login_res = await self._get_token(account, password)
        if login_res is None:
            return

        bot = Bot(
            self, str(login_res["uid"]), {
                "cookie": f"token={login_res['token']};",
                "user-agent": f"{self.get_name()}:{account}({login_res['uid']})",
                "authorization": str(uuid.uuid1())
            }, self.club255_config
        )

        self.bot_connect(bot)
        try:
            self.tasks.append(asyncio.create_task(self._keep_get_event(bot)))
        finally:
            if bot:
                self.bot_disconnect(bot)

    async def _start_forward(self) -> None:
        # 没配置账号和密码就退出
        if not (self.club255_config.club255_account and self.club255_config.club255_password):
            return
        try:
            URL(self.club255_config.club255_url)
            await self._create_bot(
                self.club255_config.club255_account, self.club255_config.club255_password
            )
        except Exception as e:
            logger.error(f"{self.get_name()} URL错误", e)

    async def _stop_forward(self) -> None:
        for task in self.tasks:
            if not task.done():
                task.cancel()

        await asyncio.gather(*self.tasks, return_exceptions=True)

    def _setup(self) -> None:
        if isinstance(self.driver, ForwardDriver):
            self.driver.on_startup(self._start_forward)
            self.driver.on_shutdown(self._stop_forward)
        else:
            logger.error(f"{self.get_name()} 需要ForwardDriver!")
