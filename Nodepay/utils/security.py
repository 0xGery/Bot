from cryptography.fernet import Fernet
import base64
import os

class SecurityManager:
    def __init__(self):
        self.key = self._load_or_generate_key()
        self.cipher_suite = Fernet(self.key)

    def _load_or_generate_key(self):
        key_file = "data/.key"
        if os.path.exists(key_file):
            with open(key_file, "rb") as f:
                return f.read()
        key = Fernet.generate_key()
        with open(key_file, "wb") as f:
            f.write(key)
        return key

    def encrypt_token(self, token):
        return self.cipher_suite.encrypt(token.encode()).decode()

    def decrypt_token(self, encrypted_token):
        return self.cipher_suite.decrypt(encrypted_token.encode()).decode()