from cryptography.fernet import Fernet
import base64
import os
import jwt
from datetime import datetime
import json

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

    def validate_token(self, token):
        """Validate JWT token without verification (since we don't have the secret)"""
        try:
            # Split the token and decode the payload
            parts = token.split('.')
            if len(parts) != 3:
                return False, "Invalid token format"
            
            # Decode the payload
            payload = base64.b64decode(parts[1] + '=' * (-len(parts[1]) % 4))
            claims = json.loads(payload)
            
            # Check expiration
            exp = claims.get('exp')
            if not exp:
                return False, "No expiration claim found"
            
            exp_datetime = datetime.fromtimestamp(exp)
            if exp_datetime < datetime.now():
                return False, f"Token expired at {exp_datetime}"
                
            return True, claims
            
        except Exception as e:
            return False, f"Token validation error: {str(e)}"
