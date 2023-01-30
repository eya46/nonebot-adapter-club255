from nonebot import on_message, logger

from nonebot123.adapters.club255 import PostEvent
from nonebot123.adapters.club255.event import NicePostEvent
from nonebot123.adapters.club255.permission import POST_NEW_USER

show = on_message(permission=POST_NEW_USER)


@show.handle()
async def show_handle(event: PostEvent):
    logger.info(event.message.xml())
    if isinstance(event, NicePostEvent):
        logger.info(f"精华帖:{event.post.title}")
    else:
        logger.info(f"普通新帖:{event.post.title}")
