"""__main__.py for seleniumqt, this will start tests."""

import sys
import pathlib


# Access the module in a external manner.
def __external_import():
    sys.path.append(pathlib.Path(__file__).parent.parent.absolute().__str__())


__external_import()

from seleniumqt.tests import main as _main
from seleniumqt.tests import *


def main():
    """Wrap arround seleniumqt.main for use in commandline."""
    _main()


# always true for this file, but still good practice due to.
# multi-processing requiring this line to not be global,
# but rather bounded in some way. this is the recommended
# way of bounding as such.
if __name__ == "__main__":
    main()
