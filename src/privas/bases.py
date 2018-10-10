import os

PKG_PATH = os.path.abspath(os.path.dirname(__file__))


class PrivaError(BaseException):
    def __init__(self, code, message):
        super().__init__(code, message)

    def __str__(self):
        return ': '.join(map(str, self.args))


class BasePriva:
    """Base class for Priva (private battles)."""

    def rules(self):
        """Return descriptions of the rules."""
        return 'No rules for %s' % self.__class__.__name__

    def start(self, *args, **kwargs):
        """Start the Priva."""
        raise PrivaError(-1, 'Priva unimplemented.')

    def end(self, *args, **kwargs):
        """End the Priva."""
        raise PrivaError(-1, 'Priva unimplemented.')

    def start_battle(self, *args, **kwargs):
        """Start a battle."""
        raise PrivaError(-1, 'Priva unimplemented.')

    def end_battle(self, *args, **kwargs):
        """End a battle."""
        raise PrivaError(-1, 'Priva unimplemented.')

