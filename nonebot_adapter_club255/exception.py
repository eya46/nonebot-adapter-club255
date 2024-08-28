from nonebot.exception import ActionFailed as BaseActionFailed
from nonebot.exception import NetworkError as BaseNetworkError
from nonebot.exception import ApiNotAvailable as BaseApiNotAvailable


class Club255Exception(BaseException):
    pass


class ActionFailed(Club255Exception, BaseActionFailed):
    pass


class NetworkError(Club255Exception, BaseNetworkError):
    pass


class ApiNotAvailable(Club255Exception, BaseApiNotAvailable):
    pass


class SendNotImplemented(Club255Exception):
    pass


class NoFaceException(Club255Exception):
    pass


class NoTagException(Club255Exception):
    pass


class UnUploadException(Club255Exception):
    pass


class ImageUnUploadException(UnUploadException):
    pass


class VideoUnUploadException(UnUploadException):
    pass
