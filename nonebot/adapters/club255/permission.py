from nonebot.permission import Permission

from .event import PostEvent
from .types import UID


async def _birthday_post(event: PostEvent):
    return event.post.type == 3


async def _new_user_post(event: PostEvent):
    return event.post.type == 2


async def _level_post(event: PostEvent):
    return event.post.type == 1


async def _common_post(event: PostEvent):
    return event.post.type == 0


def User_Post(uid: UID) -> Permission:
    """
    只获取指定用户的帖子
    """

    async def _(event: PostEvent):
        return event.post.author.uid == uid

    return Permission(_)


"""生日帖"""
POST_BIRTHDAY: Permission = Permission(_birthday_post)
"""新人帖"""
POST_NEW_USER: Permission = Permission(_new_user_post)
"""等级贴(我的俱乐部等级已升到114514级啦！超越了100.01%的毛怪！)"""
POST_LEVEL: Permission = Permission(_level_post)
"""普通帖子"""
POST_COMMON: Permission = Permission(_common_post)
"""hanser的帖子"""
POST_HANSER: Permission = Permission(User_Post(1))
