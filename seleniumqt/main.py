from .logger import logger

from .tests.test_remote import TestRemote
from .tests.test_driver import TestDriver


def main():
    import unittest

    print(f"{f"{'starting tests':=^125}": ^150}")
    logger.info("starting tests")
    unittest.main()
