from privas.bases import PrivaError
from privas.common import CommonPriva
from privas.ten_wins import TenWinsPriva

__priva_classes = [CommonPriva, TenWinsPriva]
Privas = {
    cls.Meta.pkg_name: cls
    for cls in __priva_classes
}

__all__ = [Privas, *__priva_classes, PrivaError]
