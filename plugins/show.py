from nonebot import on_message, logger

from nonebot_adapter_club255 import Bot
from nonebot_adapter_club255.event import NewPostEvent

show = on_message(block=False)


@show.handle()
async def show_handle(bot: Bot, event: NewPostEvent):
    logger.info(f"{event.post.title}[{event.post.postId}]")
