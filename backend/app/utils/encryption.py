from cryptography.fernet import Fernet
from flask import current_app
import base64

def get_encryption_key():
    """获取或生成加密密钥"""
    key = current_app.config.get('ENCRYPTION_KEY')
    if not key:
        key = Fernet.generate_key()
        current_app.config['ENCRYPTION_KEY'] = key
    return key

def encrypt_data(data):
    """加密数据"""
    if not data:
        return data
    
    f = Fernet(get_encryption_key())
    return f.encrypt(data.encode()).decode()

def decrypt_data(encrypted_data):
    """解密数据"""
    if not encrypted_data:
        return encrypted_data
    
    f = Fernet(get_encryption_key())
    return f.decrypt(encrypted_data.encode()).decode() 