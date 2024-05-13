# Access the module in a external manner.
def __external_import():
    import sys
    import pathlib
    sys.path.append(pathlib.Path(__file__).parent.parent.absolute().__str__())
__external_import()

from seleniumqt.logger import logger
import unittest

logger.info(f"{f"{'starting tests':=^125}": ^150}")
from seleniumqt.tests.test_remote import TestRemote
from seleniumqt.tests.test_driver import TestDriver

if __name__ == "__main__": # always true for this file, but still good practice due to.
    # multi-processing requiring this line to not be global, but rather bounded in some way.
    # this is the recommended way of bounding as such.
    unittest.main()