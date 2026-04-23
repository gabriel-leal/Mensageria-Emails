from cryptography.fernet import Fernet
import os
KEY = os.getenv("FERNET_KEY").encode()

fernet = Fernet(KEY)

def encrypt_password(password: str):
    return fernet.encrypt(password.encode()).decode()

def decrypt_password(encrypted_password: str):
    return fernet.decrypt(encrypted_password.encode()).decode()