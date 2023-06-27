# [club255](https://2550505.com) 适配器
毛怪俱乐部适配器，纯练习，不保证可用性（超低可用性）

## 库

* pillow
* nonebot2[httpx]

## 测试使用
```python
# 在导包前使用
import nonebot

nonebot.adapters.__path__.append(
    str((Path(__file__).parent / "nonebot" / "adapters").resolve())
)
```

## 配置项
```python
# 图床上传地址
club255_upload_api: HttpUrl = Field(default="https://api.superbed.cn/upload")
# 账号密码登录
club255_account: Optional[str] = Field(default=None)
club255_password: Optional[str] = Field(default=None)

# 默认监听的事件
club255_listen: Optional[List[AccessEventName]] = Field(default=["post", "notice", "on_live", "nice_post"])

# token优先级比账号密码高，如果token无效就会使用账号密码登录
club255_token: Optional[str] = Field(default=None)
# 是否响应自己的帖子
club255_receive_me: bool = Field(default=False)
# 请求时间间隔 单位:秒
club255_interval: int = Field(default=60)
# 每次请求的贴子数
club255_page_size: int = Field(default=20)
# 是否一运行就处理 True:立即处理获取到的帖子 False:从第二次获取开始处理
club255_run_now: bool = Field(default=False)
```

# 未完成

- 仅测试过发消息
- 图片上传还未测试，为什么👇
- 20s的间隔请求，被ban了，444😭
- ...