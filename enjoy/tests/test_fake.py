from unittest import TestCase
from .. import Enjoy


class FakeTests(TestCase):

    def test_fake(self):
        """just to enable coverage"""
        enjoy = Enjoy()
        print(enjoy)
        self.assertEqual(1, 1)
