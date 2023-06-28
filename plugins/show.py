from nonebot import on_message, logger

from nonebot.adapters.club255 import NewPostEvent, Bot, FaceEnum, NextLine, FaceMsg  # type: ignore
from nonebot.adapters.club255.event import NewNicePostEvent  # type: ignore
from nonebot.adapters.club255.permission import POST_NEW_USER  # type: ignore

show = on_message(block=False)


@show.handle()
async def show_handle(bot: Bot, event: NewPostEvent):
    logger.info(f"{event.post.title}[{event.post.postId}]")
