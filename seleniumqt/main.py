def main():
    from seleniumqt.logger import logger
    import unittest

    print(f"{f"{'starting tests':=^125}": ^150}")
    logger.info('starting tests')
    from seleniumqt.tests.test_remote import TestRemote
    from seleniumqt.tests.test_driver import TestDriver
    unittest.main()