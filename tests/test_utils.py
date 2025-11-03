"""
工具函数测试
"""
import pytest
from werkzeug.security import check_password_hash


@pytest.mark.unit
class TestUtils:
    """工具函数测试"""
    
    def test_password_hashing(self, app):
        """测试密码哈希"""
        from backend.app.models import User
        
        with app.app_context():
            user = User(username='test', email='test@test.com')
            user.set_password('testpass')
            
            assert user.password_hash is not None
            assert user.password_hash != 'testpass'
            assert user.check_password('testpass')
            assert not user.check_password('wrongpass')
    
    def test_encryption(self, app):
        """测试加密工具"""
        from backend.app.utils.encryption import encrypt_data, decrypt_data
        
        with app.app_context():
            # 设置加密密钥
            app.config['ENCRYPTION_KEY'] = app.config.get('SECRET_KEY', 'test-key')[:32].encode()
            
            test_data = "sensitive information"
            encrypted = encrypt_data(test_data)
            
            assert encrypted != test_data
            assert len(encrypted) > 0
            
            decrypted = decrypt_data(encrypted)
            assert decrypted == test_data

