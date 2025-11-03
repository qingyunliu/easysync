"""
认证相关测试
"""
import pytest
from backend import db
from backend.app.models import User


@pytest.mark.auth
@pytest.mark.unit
class TestUserModel:
    """用户模型测试"""
    
    def test_create_user(self, app, test_user):
        """测试创建用户"""
        assert test_user.username == 'testuser'
        assert test_user.email == 'test@example.com'
        assert test_user.check_password('testpass123')
        assert not test_user.check_password('wrongpass')
    
    def test_set_password(self, app):
        """测试设置密码"""
        with app.app_context():
            user = User(username='newuser', email='new@example.com')
            user.set_password('newpass123')
            assert user.password_hash is not None
            assert user.password_hash != 'newpass123'
            assert user.check_password('newpass123')
    
    def test_user_relationships(self, app, test_user):
        """测试用户关联关系"""
        with app.app_context():
            # 检查用户对象有预期的关系属性
            assert hasattr(test_user, 'storages')
            assert hasattr(test_user, 'tasks')
            assert hasattr(test_user, 'notifications')


@pytest.mark.auth
@pytest.mark.api
class TestAuthEndpoints:
    """认证API端点测试"""
    
    def test_get_captcha(self, client):
        """测试获取验证码"""
        response = client.get('/api/auth/captcha')
        assert response.status_code == 200
        assert 'Captcha-Id' in response.headers
    
    def test_login_missing_fields(self, client):
        """测试登录缺少字段"""
        response = client.post('/api/auth', json={})
        assert response.status_code in [400, 401]
    
    def test_login_invalid_user(self, client):
        """测试无效用户登录"""
        # 注意：需要mock验证码验证
        response = client.post('/api/auth', json={
            'username': 'nonexistent',
            'password': 'wrongpass',
            'captcha': 'TEST',
            'captcha_id': 'test-id'
        })
        assert response.status_code in [400, 401]
    
    def test_profile_requires_auth(self, client):
        """测试获取用户信息需要认证"""
        response = client.get('/api/auth/profile')
        assert response.status_code == 401


@pytest.mark.auth
@pytest.mark.api
class TestAuthService:
    """认证服务测试"""
    
    def test_authenticate_success(self, app, test_user):
        """测试认证成功"""
        from backend.app.auth.services import AuthService
        service = AuthService()
        user = service.authenticate('testuser', 'testpass123')
        assert user is not None
        assert user.id == test_user.id
    
    def test_authenticate_failure(self, app, test_user):
        """测试认证失败"""
        from backend.app.auth.services import AuthService
        service = AuthService()
        user = service.authenticate('testuser', 'wrongpass')
        assert user is None
    
    def test_authenticate_by_email(self, app, test_user):
        """测试邮箱认证"""
        from backend.app.auth.services import AuthService
        service = AuthService()
        user = service.authenticate_by_email('test@example.com', 'testpass123')
        assert user is not None
        assert user.id == test_user.id

