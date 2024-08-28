import asyncio
from typing import Optional, List, Set, Type, Any, Union, Iterable

from .bot import Bot, UnLoginBot, BaseBot
from .event import Event, OnLiveNoticeEvent, FollowNoticeEvent, SystemNoticeEvent, SystemNoticeMessageEvent, \
    FloorLikeNoticeEvent, PostLikeNoticeEvent, NewNicePostEvent, NewPostEvent, NewBaseNicePostEvent, NewBasePostEvent
from .types import AccessEventName


class _EventFactory:
    bot: Optional[Union[Bot, UnLoginBot]] = None
    listen: Set[AccessEventName] = set()
    data: dict = {}

    @classmethod
    def build_event(cls, event: Type[Event], data: Any, bot: BaseBot) -> Event:
        data = {**data.raw_data, "self_uid": bot.get_self_id()}
        return event.parse_obj(data)

    def add_listen(self, events: Union[AccessEventName, Iterable[AccessEventName]]):
        if isinstance(events, Iterable):
            self.listen.update(events)
        else:
            self.listen.add(events)

    def remove_listen(self, events: Union[AccessEventName, Iterable[AccessEventName]]):
        if isinstance(events, Iterable):
            self.listen.difference_update(events)
        else:
            self.listen.remove(events)

    async def build_new_live_event(self, bot: BaseBot, allow_first: bool) -> List:
        live_info = await bot.get_live_info()
        if last_live_info := self.data.get("live_info"):
            if live_info.live_status != last_live_info.live_status and live_info.live_status == 1:
                self.data["live_info"] = live_info
                return await asyncio.gather(
                    *[bot.handle_event(e) for e in [self.build_event(OnLiveNoticeEvent, live_info, bot)]]
                )
        else:
            self.data["live_info"] = live_info
        if allow_first and live_info.live_status == 1:
            return await asyncio.gather(
                *[bot.handle_event(e) for e in [self.build_event(OnLiveNoticeEvent, live_info, bot)]]
            )
        return []

    async def build_new_notice_event(self, bot: Bot, allow_first: bool) -> List:
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

        if not self.data.get("notice"):
            self.data["notice"] = True

        return await asyncio.gather(*[bot.handle_event(e) for e in events]) if allow_first else []

    async def build_new_nice_post_event(self, bot: Union[BaseBot, Bot], allow_first: bool) -> List[Event]:
        if isinstance(bot, Bot):
            nice_post_list = await bot.get_nice_post_list_by_time()
        else:
            nice_post_list = await bot.get_nice_post_list_brief_by_time()
        if exist_pid := self.data.get("nice_post"):
            nice_post_list = list(filter(
                lambda x: x.id not in exist_pid, nice_post_list
            ))
            exist_pid.update([i.postId for i in nice_post_list])
            return await asyncio.gather(*[bot.handle_event(e) for e in [
                self.build_event(NewNicePostEvent if isinstance(bot, Bot) else NewBaseNicePostEvent, i, bot)
                for i in nice_post_list
            ]])
        else:
            self.data["nice_post"] = set([i.postId for i in nice_post_list])
            return await asyncio.gather(*[bot.handle_event(e) for e in [
                self.build_event(NewNicePostEvent if isinstance(bot, Bot) else NewBaseNicePostEvent, i, bot)
                for i in nice_post_list
            ]]) if allow_first else []

    async def build_new_post_event(self, bot: Union[BaseBot, Bot], allow_first: bool) -> List[Event]:
        if isinstance(bot, Bot):
            post_list = await bot.get_post_list()
        else:
            post_list = await bot.get_post_list_brief()
        if exist_pid := self.data.get("post"):
            post_list = list(filter(
                lambda x: x.id not in exist_pid, post_list
            ))
            exist_pid.update([i.postId for i in post_list])
            return await asyncio.gather(*[bot.handle_event(e) for e in [
                self.build_event(NewPostEvent if isinstance(bot, Bot) else NewBasePostEvent, i, bot)
                for i in post_list
            ]])
        else:
            self.data["post"] = set([i.postId for i in post_list])
            return await asyncio.gather(*[bot.handle_event(e) for e in [
                self.build_event(NewPostEvent if isinstance(bot, Bot) else NewBasePostEvent, i, bot)
                for i in post_list
            ]]) if allow_first else []

    async def main(self, bot: Union[BaseBot, Bot], allow_first: bool):
        funcs = []
        for etype in self.listen:
            if etype == "on_live":
                funcs.append(self.build_new_live_event)
            elif etype == "notice" and isinstance(bot, Bot):
                funcs.append(self.build_new_notice_event)
            elif etype == "post":
                funcs.append(self.build_new_post_event)
            elif etype == "nice_post":
                funcs.append(self.build_new_nice_post_event)
        await asyncio.gather(*[i(bot, allow_first) for i in funcs])  # type: ignore


EventFactory = _EventFactory()

__all__ = [
    "EventFactory", "_EventFactory"
]
