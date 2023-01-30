class Club255Exception(BaseException):
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
