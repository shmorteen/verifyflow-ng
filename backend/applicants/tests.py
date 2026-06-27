from django.test import TestCase
from .utils import hash_sensitive_value, mask_identity_number

class IdentityUtilsTests(TestCase):
    def test_mask_identity_number(self):
        self.assertEqual(mask_identity_number("12345678901"), "123****8901")

    def test_hash_sensitive_value_is_stable(self):
        self.assertEqual(hash_sensitive_value("12345678901"), hash_sensitive_value("12345678901"))
        self.assertNotEqual(hash_sensitive_value("12345678901"), hash_sensitive_value("12345678902"))
