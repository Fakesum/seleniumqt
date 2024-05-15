import sys
import pathlib


# Access the module in a external manner.
def __external_import():
    sys.path.append(pathlib.Path(__file__).parent.parent.absolute().__str__())


__external_import()

from seleniumqt.main import main as _main
from seleniumqt.tests.test_remote import TestRemote, unittest


def main():  # wrapper to link pyproject.toml to, just in case seleniumqt.main:main might not be the best way.
    # since this should work better.
    _main()


if (
    __name__ == "__main__"
):  # always true for this file, but still good practice due to.
    # multi-processing requiring this line to not be global, but rather bounded in some way.
    # this is the recommended way of bounding as such.
    unittest.main()
