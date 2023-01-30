import os
from pathlib import Path

from nonebot import on_message, logger

from nonebot123.adapters.club255 import PostEvent, Bot, ImageMsg
from nonebot123.adapters.club255.permission import User_Post

show = on_message(block=False)

first = False

local = os.path.dirname(__file__)


@show.handle()
async def show_handle(event: PostEvent, bot: Bot):
    global first
    if not first:
        first = not first
        msg = "这是一段文本" + ImageMsg(ImageMsg(Path(local, "peach.png")))
        logger.debug("尝试上传文件")
        await bot.upload_image(msg[1])
        # logger.debug(f"发送:->({event.post.author.uid}:{event.post.postId}){msg}")
        # await bot.send_post_reply(
        #     message=msg,
        #     pid=event.post.postId,
        #     uid=event.post.author.uid
        # )
