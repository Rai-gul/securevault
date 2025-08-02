from django.test import SimpleTestCase
from filemanager.utils.encryption import encrypt_text, decrypt_text

class EncryptionTests(SimpleTestCase):
    def test_encrypt_decrypt_roundtrip(self):
        original = "This is a secret note."
        token = encrypt_text(original)
        # The encrypted token should not match the plaintext
        self.assertNotEqual(token, original)
        # Decrypting the token must return the original
        self.assertEqual(decrypt_text(token), original)
