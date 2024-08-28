from pydantic import Field, HttpUrl, BaseModel

from .types import AccessEventName


class Config(BaseModel):
    club255_url: HttpUrl = Field(default="https://ihan.club/")
    # 图床上传地址
    club255_upload_api: HttpUrl = Field(default="https://api.superbed.cn/upload")
    # 账号密码登录
    club255_account: str | None = Field(default=None)
    club255_password: str | None = Field(default=None)

    # 默认监听的事件
    club255_listen: list[AccessEventName] | None = Field(default=["post", "notice", "on_live", "nice_post"])

    # token优先级比账号密码高，如果token无效就会使用账号密码登录
    club255_token: str | None = Field(default=None)
    # 是否响应自己的帖子
    club255_receive_me: bool = Field(default=False)
    # 请求时间间隔 单位:秒
    club255_interval: int = Field(default=60)
    # 每次请求的贴子数
    club255_page_size: int = Field(default=20)
    # 是否一运行就处理 True:立即处理获取到的帖子 False:从第二次获取开始处理
    club255_run_now: bool = Field(default=False)


__all__ = ["Config"]
