import enum


class UserGroupEnum(enum.Enum):
    ADMIN = "admin"
    USER = "user"
    MODERATOR = "moderator"


class GenderEnum(enum.Enum):
    MAN = "man"
    WOMAN = "woman"


class OrderStatusEnum(enum.Enum):
    PENDING = "pending"
    PAID = "paid"
    CANCELLED = "cancelled"


class PaymentStatusEnum(enum.Enum):
    SUCCESSFUL = "successfull"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"
