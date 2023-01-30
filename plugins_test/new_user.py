import os
from pathlib import Path

from nonebot import on_message, logger

from nonebot123.adapters.club255 import PostEvent, Bot, ImageMsg
from nonebot123.adapters.club255.permission import POST_NEW_USER

show = on_message(permission=POST_NEW_USER, block=False)

first = False

local = os.path.dirname(__file__)


@show.handle()
async def show_handle(event: PostEvent, bot: Bot):
    global first
    if not first:
        first = not first
        msg = "欢迎新人" + ImageMsg(Path(local, "peach.png"))
        logger.debug(f"发送:新人贴->({event.post.author.uid}:{event.post.postId}){msg}")
        await bot.send_post_reply(
            message=msg,
            pid=event.post.postId,
            uid=event.post.author.uid
        )
