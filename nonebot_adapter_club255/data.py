from enum import Enum

from urllib.parse import urljoin


class Tag:
    id: int
    name: str

    def __init__(self, id_: int, name: str):
        self.id = id_
        self.name = name

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}(name="{self.name}",id_={self.id})'

    def __str__(self) -> str:
        return f"[标签:{self.name}]"


class Face:
    name: str
    code: int
    type: str

    def __init__(self, data):
        self.name = data[0]
        self.type = data[1]
        self.code = data[2]

    def get_url(self) -> str:
        return urljoin("https://2550505.com", f"emotion/{self.code}/{self.name}.{self.type}")

    def __repr__(self) -> str:
        return (
            f'{self.__class__.__name__}('
            f'name="{self.name}",code="{self.code}",'
            f'type_="{self.type}"'
            f')'
        )

    def __str__(self) -> str:
        return f"[表情:{self.name}]"


class TagEnum(Enum):
    BUG = Tag(6, "BUG")
    hanser = Tag(1, "hanser")
    小天使 = Tag(2, "小天使")
    专辑 = Tag(8, "专辑")
    年贺 = Tag(3, "年贺")
    新人报到 = Tag(9, "新人报到")
    演唱会 = Tag(5, "演唱会")
    用户反馈 = Tag(7, "用户反馈")


class FaceEnum(Enum):
    """
    表情枚举类: 命名规则: 表情名_表情编号
    推荐仅做代码提示使用
    实际使用时，建议使用Face来创建表情
    """
    生日快乐叹_birthday = Face(["生日快乐！", "png", "birthday"])
    生日快乐问_birthday = Face(["生日快乐？", "png", "birthday"])
    吃瓜_8 = Face(["吃瓜", "png", "8"])
    打不着_8 = Face(["打不着", "png", "8"])
    交出手脚_8 = Face(["交出手脚", "png", "8"])
    嗯问_8 = Face(["嗯？", "png", "8"])
    傻dog_8 = Face(["傻dog", "png", "8"])
    天才_8 = Face(["天才", "png", "8"])
    lz怎么可能没有女粉_1 = Face(["lz怎么可能没有女粉", "png", "1"])
    awsl_1 = Face(["awsl", "png", "1"])
    不行吗_1 = Face(["不行吗", "png", "1"])
    恭喜_1 = Face(["恭喜", "png", "1"])
    冲冲冲叹_1 = Face(["冲冲冲！", "png", "1"])
    暗中观察_1 = Face(["暗中观察", "png", "1"])
    哈_1 = Face(["哈", "png", "1"])
    peach_1 = Face(["peach", "png", "1"])
    飞扑_1 = Face(["飞扑", "png", "1"])
    不想努力_1 = Face(["不想努力", "png", "1"])
    昂波力无_1 = Face(["昂波力无", "png", "1"])
    ok_1 = Face(["ok", "png", "1"])
    冲呀_1 = Face(["冲呀", "png", "1"])
    不愧是你_1 = Face(["不愧是你", "png", "1"])
    抱奶瓶_1 = Face(["抱奶瓶", "png", "1"])
    海星_1 = Face(["海星", "png", "1"])
    面具_2 = Face(["面具", "png", "2"])
    加倍_2 = Face(["加倍", "png", "2"])
    恐怖_2 = Face(["恐怖", "png", "2"])
    嘿嘿_2 = Face(["嘿嘿", "png", "2"])
    毛怪哭哭_2 = Face(["毛怪哭哭", "png", "2"])
    哭哭_2 = Face(["哭哭", "png", "2"])
    惊_2 = Face(["惊", "png", "2"])
    滑稽_2 = Face(["滑稽", "png", "2"])
    美女_2 = Face(["美女", "png", "2"])
    流啤_2 = Face(["流啤", "png", "2"])
    害羞_2 = Face(["害羞", "png", "2"])
    喵_2 = Face(["喵", "png", "2"])
    憨憨飘过_2 = Face(["憨憨飘过", "png", "2"])
    好听_2 = Face(["好听", "png", "2"])
    篮球_2 = Face(["篮球", "png", "2"])
    惊吓_2 = Face(["惊吓", "png", "2"])
    热_3 = Face(["热", "png", "3"])
    拿扫把气呼呼_3 = Face(["拿扫把气呼呼", "png", "3"])
    亲亲_3 = Face(["亲亲", "png", "3"])
    扑通_3 = Face(["扑通", "png", "3"])
    你假装持久_3 = Face(["你假装持久", "png", "3"])
    怂呐_3 = Face(["怂呐", "png", "3"])
    南瓜头毛怪_3 = Face(["南瓜头毛怪", "png", "3"])
    嗯_3 = Face(["嗯", "png", "3"])
    叹气_3 = Face(["叹气", "png", "3"])
    破肺_3 = Face(["破肺", "png", "3"])
    摸摸_3 = Face(["摸摸", "png", "3"])
    爬_3 = Face(["爬", "png", "3"])
    天使_3 = Face(["天使", "png", "3"])
    你tmghs_3 = Face(["你tmghs", "png", "3"])
    挠头_3 = Face(["挠头", "png", "3"])
    抢地主_3 = Face(["抢地主", "png", "3"])
    谢谢_4 = Face(["谢谢", "png", "4"])
    抓狂_4 = Face(["抓狂", "png", "4"])
    王炸_4 = Face(["王炸", "png", "4"])
    晚安_4 = Face(["晚安", "png", "4"])
    学习_4 = Face(["学习", "png", "4"])
    嘤嘤嘤_4 = Face(["嘤嘤嘤", "png", "4"])
    晕晕_4 = Face(["晕晕", "png", "4"])
    肖邦_4 = Face(["肖邦", "png", "4"])
    贴贴_4 = Face(["贴贴", "png", "4"])
    知识增加_4 = Face(["知识增加", "png", "4"])
    疑问_4 = Face(["疑问", "png", "4"])
    痛哭_4 = Face(["痛哭", "png", "4"])
    真好_4 = Face(["真好", "png", "4"])
    我是天才_4 = Face(["我是天才", "png", "4"])
    委屈_4 = Face(["委屈", "png", "4"])
    早_4 = Face(["早", "png", "4"])
    惊_5 = Face(["惊", "png", "5"])
    听不见_5 = Face(["听不见", "png", "5"])
    听我说_5 = Face(["听我说", "png", "5"])
    哟_5 = Face(["哟", "png", "5"])
    咻咻_5 = Face(["咻咻", "png", "5"])
    吓_5 = Face(["吓", "png", "5"])
    抱抱_5 = Face(["抱抱", "png", "5"])
    喝茶_5 = Face(["喝茶", "png", "5"])
    无语_5 = Face(["无语", "png", "5"])
    晚安_5 = Face(["晚安", "png", "5"])
    噗_5 = Face(["噗", "png", "5"])
    吊着_5 = Face(["吊着", "png", "5"])
    自闭_5 = Face(["自闭", "png", "5"])
    出拳_5 = Face(["出拳", "png", "5"])
    哭哭_5 = Face(["哭哭", "png", "5"])
    好朋友_5 = Face(["好朋友", "png", "5"])
    溜了_6 = Face(["溜了", "png", "6"])
    放空_6 = Face(["放空", "png", "6"])
    岁岁芭比油_6 = Face(["岁岁芭比油", "png", "6"])
    躺平_6 = Face(["躺平", "png", "6"])
    吃毛怪_6 = Face(["吃毛怪", "png", "6"])
    给心心_6 = Face(["给心心", "png", "6"])
    哈哈哈_6 = Face(["哈哈哈", "png", "6"])
    唱歌_6 = Face(["唱歌", "png", "6"])
    期待_6 = Face(["期待", "png", "6"])
    吃我一拳_6 = Face(["吃我一拳", "png", "6"])
    喝奶_6 = Face(["喝奶", "png", "6"])
    闪亮登场_6 = Face(["闪亮登场", "png", "6"])
    吃我三拳_6 = Face(["吃我三拳", "png", "6"])
    脱单憨憨_6 = Face(["脱单憨憨", "png", "6"])
    就是你_7 = Face(["就是你", "png", "7"])
    遇到困难睡大觉_7 = Face(["遇到困难睡大觉", "png", "7"])
    恭喜_7 = Face(["恭喜", "png", "7"])
    交出来_7 = Face(["交出来", "png", "7"])
    疑问_7 = Face(["疑问", "png", "7"])
    Zzz_7 = Face(["Zzz", "png", "7"])
    光速下班_7 = Face(["光速下班", "png", "7"])
    打call_7 = Face(["打call", "png", "7"])
    趴_7 = Face(["趴", "png", "7"])
    登场_7 = Face(["登场", "png", "7"])
    饿_7 = Face(["饿", "png", "7"])
    点赞_7 = Face(["点赞", "png", "7"])
    心动_7 = Face(["心动", "png", "7"])
    抱大腿_7 = Face(["抱大腿", "png", "7"])
    打咩_7 = Face(["打咩", "png", "7"])
    暗中观察_7 = Face(["暗中观察", "png", "7"])
    哭哭_7 = Face(["哭哭", "png", "7"])
    不要睡_7 = Face(["不要睡", "png", "7"])
    石化_7 = Face(["石化", "png", "7"])
    伸懒腰_7 = Face(["伸懒腰", "png", "7"])
    天才_7 = Face(["天才", "png", "7"])
    开心_7 = Face(["开心", "png", "7"])
    鬼脸_7 = Face(["鬼脸", "png", "7"])
    恰柠檬_7 = Face(["恰柠檬", "png", "7"])
    干杯_0 = Face(["干杯", "png", "0"])
    鞭炮上_0 = Face(["鞭炮上", "png", "0"])
    鞭炮下_0 = Face(["鞭炮下", "png", "0"])
    变兔子_0 = Face(["变兔子", "png", "0"])
    不想起床_0 = Face(["不想起床", "png", "0"])
    吃饺子_0 = Face(["吃饺子", "png", "0"])
    打卡_0 = Face(["打卡", "png", "0"])
    发红包_0 = Face(["发红包", "png", "0"])
    放烟花_0 = Face(["放烟花", "png", "0"])
    恭喜_0 = Face(["恭喜", "png", "0"])
    毛怪灯笼_0 = Face(["毛怪灯笼", "png", "0"])
    毛怪哭哭_0 = Face(["毛怪哭哭", "png", "0"])
    失落_0 = Face(["失落", "png", "0"])
    玩雪_0 = Face(["玩雪", "png", "0"])
    新年快乐_0 = Face(["新年快乐", "png", "0"])
    许愿_0 = Face(["许愿", "png", "0"])
    棒_0 = Face(["棒", "png", "0"])
    饱了_0 = Face(["饱了", "png", "0"])


__all__ = [
    "Tag", "Face", "TagEnum", "FaceEnum"
]
