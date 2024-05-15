"""module to store all custom exceptions."""


class DataNotGiven(Exception):

    """Raise When Data was not given to the remote which is required for it to function."""

    pass


class JavascriptException(Exception):

    """Raise when there was an error during javascript on remote."""

    pass


class InvalidUrl(Exception):

    """Raise when there was an invalid Url given to remote to open."""

    pass


class InternalWidgitNotFound(Exception):

    """Raise when the widgit which is to be found as a child of the browser widgit is not found.
    
    required for certain functions like click and any other function which sends events to this widgit.
    """

    pass


class InvalidSelectorType(Exception):

    """Raise when an Invalid selector was given to remote."""

    pass


class SetPageEror(Exception):

    """Raise When there was an error during self.__set_page."""

    pass


class RemoteExited(Exception):

    """Raise when remote exited while driver is still running."""

    pass


class NullPageError(Exception):

    """Raise when self.page() is None."""

    pass
