"""
pytest配置和fixtures
"""
import os
import pytest
from backend import create_app, db
from backend.app.models import User


@pytest.fixture(scope='session')
def app():
    """创建测试应用"""
    # 设置测试环境变量
    os.environ['FLASK_ENV'] = 'testing'
    os.environ['SECRET_KEY'] = 'test-secret-key-for-pytest-only'
    os.environ['JWT_SECRET_KEY'] = 'test-jwt-secret-key-for-pytest-only'
    
    # 使用SQLite内存数据库进行测试
    test_db_uri = os.environ.get(
        'TEST_DATABASE_URL',
        'sqlite:///:memory:'
    )
    os.environ['SQLALCHEMY_DATABASE_URI'] = test_db_uri
    
    app = create_app('testing')
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """测试客户端"""
    return app.test_client()


@pytest.fixture
def runner(app):
    """命令行测试运行器"""
    return app.test_cli_runner()


@pytest.fixture
def auth_headers(client, test_user):
    """获取认证头"""
    # 登录获取token
    response = client.post('/api/auth', json={
        'username': test_user.username,
        'password': 'testpass123',
        'captcha': 'TEST',
        'captcha_id': 'test-captcha-id'
    })
    
    # 注意：实际测试中需要mock验证码
    if response.status_code == 200:
        data = response.get_json()
        token = data.get('data', {}).get('access_token')
        if token:
            return {'Authorization': f'Bearer {token}'}
    
    return {}


@pytest.fixture
def test_user(app):
    """创建测试用户"""
    with app.app_context():
        user = User(
            username='testuser',
            email='test@example.com',
            role='user'
        )
        user.set_password('testpass123')
        db.session.add(user)
        db.session.commit()
        yield user
        db.session.delete(user)
        db.session.commit()


@pytest.fixture
def admin_user(app):
    """创建管理员用户"""
    with app.app_context():
        user = User(
            username='admin',
            email='admin@example.com',
            role='admin',
            is_admin=True
        )
        user.set_password('adminpass123')
        user.email_verified = True
        db.session.add(user)
        db.session.commit()
        yield user
        db.session.delete(user)
        db.session.commit()


@pytest.fixture(autouse=True)
def cleanup_db(app):
    """自动清理数据库"""
    yield
    with app.app_context():
        db.session.rollback()

