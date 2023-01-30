import re
from copy import deepcopy
from io import BytesIO
from pathlib import Path
from typing import Type, Iterable, Union, Optional, List
from xml.dom.minidom import Text as XmlText

from PIL import Image
from nonebot.adapters import Message as BaseMessage
from nonebot.adapters import MessageSegment as BaseMessageSegment
from nonebot.internal.adapter.message import TMS, TM
from pydantic import BaseModel, AnyUrl

from .data import FaceEnum, Face, TagEnum, Tag
from .exceptions import *
from .utils import *


class _ImgUrlCheck(BaseModel):
    url: AnyUrl


class MessageSegment(BaseMessageSegment["Message"]):
    def __add__(self: TMS, other: Union[str, TMS, Iterable[TMS]]) -> TM:
        return Message([self, other])

    def __radd__(self: TMS, other: Union[str, TMS, Iterable[TMS]]) -> TM:
        return Message([other, self])

    @staticmethod
    def new_line() -> "NextLine":
        return NextLine()

    @staticmethod
    def text(txt: str, strong: bool = False, em: bool = False) -> "TextMsg":
        return TextMsg(txt, strong=strong, em=em)

    @staticmethod
    def face(
            name: Union[str, Face, FaceEnum], *,
            code: Optional[str] = None, type_: Optional[str] = None,
            url: Optional[str] = None, strict: bool = True
    ) -> "FaceMsg":
        return FaceMsg(name, code=code, type_=type_, url=url, strict=strict)

    @staticmethod
    def tag(
            name: Union[str, Tag, TagEnum], strict: bool = True
    ) -> "TagMsg":
        return TagMsg(name, strict=strict)

    def xml(self) -> str:
        for i in MessageSegment.__subclasses__():
            if self.type == i.type:
                return i.xml(self)
        raise NotImplementedError(f"{self.type}未实现")

    @classmethod
    def get_message_class(cls) -> Type["Message"]:
        return Message

    def __str__(self) -> str:
        for i in MessageSegment.__subclasses__():
            if self.type == i.type:
                return str(self)
        return f"[{self.type}:{self.data}]"

    def is_text(self) -> bool:
        return self.type == "text"


class TagMsg(MessageSegment):
    type = "tag"

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}(name="{self.data.get("name")}",id={self.get("id")})'

    def __str__(self) -> str:
        return f"[标签:{self.data['name']}]"

    @property
    def name(self) -> str:
        return self.data["name"]

    @property
    def id(self) -> str:
        if self.data.get("id") is None:
            raise NoTagException(f"没有该Tag:{self.name}")
        return self.data.get("id")

    def xml(self) -> str:
        return f'<a class="editor-hash-tag" href="/tag/{self.id}" ' \
               f'data-id="{self.id}" data-label="{self.name}">#{self.name}</a>'

    def __init__(self, name: Union[str, Tag, TagEnum], *, strict: bool = True):
        if isinstance(name, str):
            for i in TagEnum:
                if i.value.name == name:
                    super().__init__(
                        self.type,
                        {"name": name, "id": i.value.id}
                    )
                    return
            if strict:
                raise NoTagException(f"没有该Tag:{name}")
            else:
                super().__init__(
                    self.type,
                    {"name": name}
                )
        elif isinstance(name, Tag):
            super().__init__(
                self.type,
                {"name": name.name, "id": name.id}
            )
        elif isinstance(name, TagEnum):
            super().__init__(
                self.type,
                {"name": name.value.name, "id": name.value.id}
            )
        else:
            raise NoTagException("未知类型Tag")

    @classmethod
    def get_message_class(cls) -> Type["TagMsg"]:
        return cls


class VideoMsg(MessageSegment):
    type = "video"

    def __repr__(self) -> str:
        return (f'{self.__class__.__name__}('
                f'bv="{self.bv}",title="{self.title}",url="{self.url}"'
                f',cover="{self.cover}"'
                f')')

    def __str__(self) -> str:
        return f"[视频:{self.data['bv']}]"

    @property
    def bv(self) -> str:
        return self.data["bv"]

    @property
    def title(self) -> Optional[str]:
        return self.data.get("title")

    @property
    def url(self) -> str:
        return self.data["url"]

    @property
    def cover(self) -> Optional[str]:
        return self.data.get("cover")

    def check(self) -> bool:
        return bool(self.title) and bool(self.cover)

    def xml(self) -> str:
        if self.url is None or self.title is None:
            raise VideoUnUploadException(f"视频未上传:{self.bv}")

        return f'<p><img src="{self.url}" class="upload-img" data-bv="{self.bv}" referrerpolicy="no-referrer"></p>' \
               f'<p><a target="_blank" rel="noopener noreferrer nofollow" class="editor-link editor-link" ' \
               f'href="{self.url}">{self.title}</a></p>'

    def __init__(self, bv: str, cover: Optional[str] = None, title: Optional[str] = None, url: Optional[str] = None):
        super().__init__(
            self.type,
            {"bv": bv, "title": title, "url": url or f"https://www.bilibili.com/video/{bv}/", "cover": cover}
        )

    @classmethod
    def get_message_class(cls) -> Type["VideoMsg"]:
        return cls


class ImageMsg(MessageSegment):
    """
    目前没法添加水印，上水印是本地进行的
    """

    type = "image"

    def __repr__(self) -> str:
        return super(MessageSegment).__repr__()

    def __str__(self) -> str:
        type_ = self.data["type"]
        return f"[图片:{self.url or type_}]"

    def xml(self) -> str:
        if not self.check():
            raise ImageUnUploadException("图片未上传")
        return f'<img src="{self.url}" class="upload-img" referrerpolicy="no-referrer">'.strip()

    @property
    def file(self) -> Optional[bytes]:
        return self.data["file"]

    @property
    def url(self) -> Optional[str]:
        return self.data.get("url")

    @property
    def type_(self) -> str:
        return self.data["type"]

    def check(self) -> bool:
        return bool(self.url)

    def __init__(self, file: Union[str, bytes, BytesIO, Path], watermark: bool = False):
        url = None
        type_ = None
        if isinstance(file, str):
            try:
                _url = _ImgUrlCheck.parse_obj({"url": file})
                type_ = file.split(".")[-1]
                url = file
                file = None
            except:
                file = Path(file)

        if isinstance(file, Path):
            img = Image.open(file)
            file = BytesIO()
            img.save(file, format=img.format)
            type_ = img.format.lower()
        if isinstance(file, BytesIO):
            file = file.getvalue()
        if type_ is None:
            type_ = Image.open(file).format.lower()
        super().__init__(
            self.type,
            {"file": file, "type": type_, "url": url, "watermark": watermark}
        )

    @classmethod
    def get_message_class(cls) -> Type["ImageMsg"]:
        return cls


class LinkMsg(MessageSegment):
    """
    预览文本里面只显示 链接文本
    """
    type = "link"

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}(text="{self.txt}",url="{self.url}")'

    def __str__(self):
        return self.data["url"]

    @property
    def url(self) -> str:
        return self.data["url"]

    @property
    def txt(self) -> str:
        return self.data["text"]

    def xml(self) -> str:
        return f'<a target="_blank" rel="noopener noreferrer nofollow" class="editor-link editor-link" ' \
               f'href="{self.url}">{self.txt}</a>'

    def __init__(self, text: str, url: str):
        super().__init__(
            self.type,
            {"text": text, "url": url}
        )


class NextLine(MessageSegment):
    """
    显式换行，在event的Message中不会出现，只是便于 回帖/发贴 时换行
    左右两条消息换行显示
    """

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}(text="{self.data.get("text")}",strong={self.get("strong")},em={self.get("em")})'

    @staticmethod
    def new_line() -> "NextLine":
        return NextLine()

    type = "next_line"

    def __str__(self) -> str:
        return "\n"

    def xml(self) -> str:
        return ""

    def __init__(self) -> None:
        super().__init__(
            "text", {"text": "\n", "strong": False, "em": False}
        )

    @classmethod
    def get_message_class(cls) -> Type["NextLine"]:
        return cls


class FaceMsg(MessageSegment):
    type = "face"

    def __repr__(self) -> str:
        return (
            f'{self.__class__.__name__}('
            f'name="{self.data.get("name")}",code="{self.data.get("code")}",'
            f'type_="{self.data.get("type")}",url="{self.data.get("url")}"'
            f')'
        )

    def __str__(self) -> str:
        return f"[表情:{self.data['name']}]"

    def __init__(
            self, name: Union[str, Face, FaceEnum], *,
            code: Optional[str] = None, type_: Optional[str] = None, url: Optional[str] = None, strict: bool = True
    ) -> None:
        if isinstance(name, str):
            for i in FaceEnum:
                if i.value.name == name:
                    super().__init__(
                        "face", {
                            "name": name, "code": code or i.value.code,
                            "type": type_ or i.value.type, "url": url or i.value.get_url()
                        }
                    )
                    return
            if strict and not (code or type_ or url):
                raise NoFaceException(f"没有该表情:{name}")
            else:
                super().__init__(
                    "face", {
                        "name": name, "code": code, "type": type_, "url": url
                    }
                )
        elif isinstance(name, Face):
            super().__init__(
                "face", {"name": name.name, "code": name.code, "type": name.type, "url": name.get_url()}
            )
        elif isinstance(name, FaceEnum):
            super().__init__(
                "face", {
                    "name": name.value.name, "code": name.value.code,
                    "type": name.value.type, "url": name.value.get_url()
                }
            )
        else:
            raise NoFaceException("未知类型表情")

    @property
    def url(self) -> str:
        if self.data.get("url") is None:
            raise NoFaceException("没有该表情")
        return self.data["url"]

    def xml(self) -> str:
        name = self.data["name"]
        return f'<img src="{self.url}" alt="{name}" title="{name}" class="emoticon-img" ' \
               f'referrerpolicy="no-referrer" data-emotion-name="{name}">'.strip()

    @classmethod
    def get_message_class(cls) -> Type["FaceMsg"]:
        return cls


class TextMsg(MessageSegment):
    type = "text"

    def __repr__(self) -> str:
        return (
            f'{self.__class__.__name__}('
            f'text="{self.data.get("text")}",'
            f'strong={self.data.get("strong")},em={self.data.get("em")}'
            f')'
        )

    def __str__(self) -> str:
        return self.data.get("text", "")

    def __init__(self, text: str, *, strong: bool = False, em: bool = False) -> None:
        super().__init__(
            "text", {"text": text, "strong": strong, "em": em}
        )

    @property
    def txt(self) -> str:
        return self.data["text"]

    @property
    def strong(self) -> bool:
        return self.data["strong"]

    @property
    def em(self) -> bool:
        return self.data["em"]

    def raw_xml(self) -> List[Element]:
        def _xml(_txt):
            root = XmlText()
            root.data = _txt
            if self.data["em"]:
                root = set_father_tag(root, "em")
            if self.data["strong"]:
                root = set_father_tag(root, "strong")
            return set_father_tag(root, "p")

        txt = self.txt

        return [_xml(i) for i in txt.split("\n")]

    def xml(self) -> str:
        def _xml(_txt):
            root = XmlText()
            root.data = _txt
            if self.data["em"]:
                root = set_father_tag(root, "em")
            if self.data["strong"]:
                root = set_father_tag(root, "strong")
            return root.toxml()

        txt = self.data["text"]
        txts = txt.split("\n")
        return "".join(
            f"<p>{_xml(i)}</p>" if index != len(txts) - 1 else _xml(i) for index, i in enumerate(txts)
        )

    @classmethod
    def get_message_class(cls) -> Type["TextMsg"]:
        return cls


class Message(BaseMessage[MessageSegment]):

    def extract_plain_text(self) -> str:
        """
        楼层回复只能发纯文本，并且无法换行，所以这个api不解析NextLine
        """
        return super().extract_plain_text()

    @classmethod
    def get_segment_class(cls) -> Type[MessageSegment]:
        return MessageSegment

    @staticmethod
    def join_url(data: dict):
        for i in data.get("videos", []):
            data["content"] = data["content"].replace("[视频]", f"[视频:{i}]", 1)
        for i in data.get("primaryPictures", []) or data.get("pictures", []):
            data["content"] = data["content"].replace("[图片]", f"[图片:{i}]", 1)

    def xml(self) -> str:
        msgs = []
        tmp = []
        for index, i in enumerate(self):
            if isinstance(i, NextLine) or (isinstance(i, TextMsg) and i.txt == "\n"):
                if len(tmp) != 0:
                    msgs.append(Message(deepcopy(tmp)))
                    tmp = []
                else:
                    msgs.append([])
            elif isinstance(i, VideoMsg):
                if len(tmp) == 0:
                    msgs.append(Message(i))
                else:
                    msgs.append(Message(deepcopy(tmp)))
                    msgs.append(Message(i))
                    tmp = []
            elif isinstance(i, TextMsg):
                txts = [j for j in i.txt.split("\n") if len(j) > 0]
                if len(txts) == 0:
                    continue
                elif len(txts) == 1:
                    tmp.append(i)
                else:
                    tmp.append(TextMsg(txts[0], strong=i.strong, em=i.em))
                    msgs.append(deepcopy(tmp))
                    if len(txts) == 2:
                        tmp = [TextMsg(txts[1], strong=i.strong, em=i.em)]
                    else:
                        for j in txts[1:-1]:
                            msgs.append(Message(TextMsg(j, strong=i.strong, em=i.em)))
                        tmp = [TextMsg(txts[-1], strong=i.strong, em=i.em)]
            else:
                tmp.append(i)
        if len(tmp) != 0:
            msgs.append(Message(deepcopy(tmp)))

        return "".join([
            f"<p>{''.join(j.xml() for j in i)}</p>"
            if not isinstance(i, VideoMsg) else
            ''.join(j.xml() for j in i)
            for i in msgs
        ])

    @staticmethod
    def _construct(msg: str) -> Iterable[MessageSegment]:
        # 有时候莫名其妙报 Message[0] -> IndexError的错，所以就加个这个
        if msg == "":
            yield TextMsg("")
            return

        msg = unescape(msg)

        def _split(txt: str):
            for i in re.finditer(
                    # r"(\[(?P<type>\S+?)])|(?P<txt>([^[\]]+))",
                    r"(#(?P<tag>(\S+))\s)|(\[(?P<type>\S+?)])|(?P<txt>([^[\]]+))",
                    txt
            ):
                if i.group("tag") is not None:
                    yield "tag", i.group("tag")
                elif (_type := i.group("type")) is None:
                    yield "text", i.group("txt")
                elif "视频" in _type:
                    yield "video", i.group("type").split(":", 1)[1]
                elif "图片" in _type:
                    yield "image", i.group("type").split(":", 1)[1]
                else:
                    yield "face", i.group("type")

        for type_, data in _split(msg):
            if type_ == "text":
                yield TextMsg(data)
            elif type_ == "tag":
                yield TagMsg(data, strict=False)
            elif type_ == "face":
                yield FaceMsg(data, strict=False)
            elif type_ == "video":
                yield VideoMsg(data)
            else:
                yield ImageMsg(data)
