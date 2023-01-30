from typing import Optional

from pydantic import Field, BaseModel


class Config(BaseModel):
    club255_url: str = Field(default="https://2550505.com")
    club255_upload_api: str = Field(default="https://api.superbed.cn/upload")
    club255_account: Optional[str]
    club255_password: Optional[str]
    # 是否响应自己的帖子
    club255_receive_me: bool = Field(default=False)
    # 请求时间间隔 单位:秒
    club255_interval: int = Field(default=20)
    # 每次获取到贴子数
    club255_page_size: int = Field(default=20)
    # 是否一运行就处理
    club255_run_now: bool = Field(default=False)

    class Config:
        extra = "ignore"
