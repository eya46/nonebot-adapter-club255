from typing import Any
from xml.dom.minidom import Element


def escape(s: str) -> str:
    return s.replace(" ", "&nbsp;")


def unescape(s: str) -> str:
    return s.replace("&nbsp;", " ")


def set_father(child: Any, father: Element) -> Element:
    father.appendChild(child)
    return father


def set_father_tag(child: Any, father: str) -> Element:
    father = Element(father)
    father.appendChild(child)
    return father


# copy by adapter-onebot-v11
def truncate(
        s: Any, length: int = 100, kill_words: bool = False, end: str = "..."
) -> str:
    """将给定字符串截断到指定长度。

    参数:
        s: 需要截取的字符串
        length: 截取长度
        kill_words: 是否不保留完整单词
        end: 截取字符串的结尾字符

    返回:
        截取后的字符串
    """
    s = str(s)
    if len(s) <= length:
        return s

    if kill_words:
        return s[: length - len(end)] + end

    result = s[: length - len(end)].rsplit(maxsplit=1)[0]
    return result + end
