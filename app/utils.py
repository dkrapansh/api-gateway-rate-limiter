import secrets
import hashlib

def generate_api_key():
    return secrets.token_hex(32)

def hash_api_key(api_key: str):
    return hashlib.sha256(api_key.encode()).hexdigest()