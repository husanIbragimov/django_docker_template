import enum
from enum import unique


@unique
class ResponseCode(enum.Enum):
    UNSUBSCRIBE_TOKEN_INVALID = 4001
