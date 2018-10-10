from privas.bases import PrivaError
from privas.common import CommonPriva
from privas.n_wins import NWinsPriva, TenWinsPriva

__priva_classes = [
    CommonPriva,
    NWinsPriva, TenWinsPriva
]
Privas = {
    cls.Meta.type_name: cls
    for cls in __priva_classes
}

__all__ = [Privas, *__priva_classes, PrivaError]
