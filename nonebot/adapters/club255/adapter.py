import asyncio
import json
from typing import Any, List, Optional, Tuple, Union
from urllib.parse import urljoin
from uuid import uuid1

from nonebot import Driver, logger
from nonebot.adapters import Adapter as BaseAdapter
from nonebot.drivers import Request, Response
from nonebot.internal.driver import ForwardDriver

from .bot import Bot, UnLoginBot
from .config import Config
from .factory import EventFactory


class Adapter(BaseAdapter):
    def __init__(self, driver: Driver, **kwargs: Any):
        super().__init__(driver, **kwargs)
        self.club255_config: Config = Config(**self.config.dict())
        EventFactory.add_listen(self.club255_config.club255_listen or [])
        self.ROOT = "https://2550505.com"
        self.tasks: List[asyncio.Task] = []
        self._setup()

    async def sleep(self):
        await asyncio.sleep(self.club255_config.club255_interval)

    @classmethod
    def get_name(cls) -> str:
        return "Club255"

    async def _call_api(self, bot: Bot, api: str, **data: Any) -> Response:
        method = data.get("method") if data.get("method") else "GET"
        if method == "GET":
            return await self.request(Request(
                method, urljoin(self.ROOT, api), params=data, headers=bot.header
            ))
        elif method == "POST":
            return await self.request(Request(
                method, urljoin(self.ROOT, api), json=data, headers=bot.header
            ))
        else:
            raise ValueError(f"未知method:{method}")

    async def _check_token(self, token: str) -> Tuple[bool, Optional[dict]]:
        resp = await self.request(Request(
            "GET", urljoin(self.ROOT, "user/info"), cookies={"token": token}
        ))
        if resp.status_code != 200:
            return False, None
        try:
            data = json.loads(resp.content)
            return data["code"] == 0, data
        except Exception as e:
            logger.error(e)
            return False, None

    async def _get_token(
            self, account: Optional[str] = None, password: Optional[str] = None, token: Optional[str] = None
    ) -> Union[str, dict]:
        reason = []
        if token:
            logger.debug(f"{self.get_name()} | 使用token登录")
            res, data = await self._check_token(token)
            if res:
                return {
                    "token": token,
                    "code": 0,
                    "uid": data["info"]["uid"]
                }
            else:
                logger.debug(f"{self.get_name()} | token无效")
                reason.append("token无效")

        if not (account and password):
            reason.append("账号密码为空")
            return "、".join(reason)

        logger.debug(f"{self.get_name()} | 使用密码登录")
        data = json.loads((await self.request(Request(
            "POST", urljoin(self.ROOT, "auth/login"), json={
                "account": account, "password": password
            }
        ))).content)

        if msg := data.get("msg"):
            reason.append(msg)

        if data["code"] == 0:
            return data
        else:
            reason.append(f"code:{data['code']}")
            return " | ".join(reason)

    async def _keep_get_event(self, bot: Bot):
        try:
            await EventFactory.main(bot, self.club255_config.club255_run_now)
        except Exception as e:
            logger.error(f"{self.get_name()}:{bot.self_id} -> 处理事件失败:{e}")
            logger.error(e)

    def _create_unlogin_bot(self) -> UnLoginBot:
        bot = UnLoginBot(adapter=self, header={
            "user-agent": f"NoneBot-Adapter-{self.get_name()}:maoguai",
            "authorization": str(uuid1())
        }, config=self.club255_config)
        return bot

    async def _create_bot(
            self, *, account: Optional[str] = None, password: Optional[str] = None, token: Optional[str] = None
    ) -> Optional[Bot]:
        bot: Optional[Bot]

        login_res = await self._get_token(account, password, token)

        if isinstance(login_res, str):
            logger.error(f"{self.get_name()} | {account or '未配置账号'} | 登录失败 | {login_res}")
            return

        logger.success(f"{self.get_name()} | {account or '未配置账号'} | 登录成功:{login_res['uid']}")

        return Bot(
            adapter=self, self_id=str(login_res["uid"]), header={
                "cookie": f"token={login_res['token']};",
                "user-agent": f"NoneBot-Adapter-{self.get_name()}:{account}({login_res['uid']})",
                "authorization": str(uuid1())
            }, config=self.club255_config
        )

    async def _start_forward(self) -> None:
        if (
                not (self.club255_config.club255_account and self.club255_config.club255_password) and
                self.club255_config.club255_token is None
        ):
            logger.info(f"{self.get_name()} 未配置账号密码或token")
            bot = self._create_unlogin_bot()
        else:
            try:
                bot = await self._create_bot(
                    account=self.club255_config.club255_account,
                    password=self.club255_config.club255_password,
                    token=self.club255_config.club255_token
                )
            except Exception as e:
                logger.error(f"{self.get_name()} 创建Bot失败", e)
                raise e

        if bot:
            self.bot_connect(bot)
            try:
                self.tasks.append(asyncio.create_task(self._keep_get_event(bot)))
            finally:
                if bot:
                    self.bot_disconnect(bot)

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


__all__ = ["Adapter"]
