"""
API集成测试
"""
import pytest
from backend import db
from backend.app.models import User, Task, Storage


@pytest.mark.integration
@pytest.mark.api
class TestTaskAPI:
    """任务API集成测试"""
    
    def test_create_task_requires_auth(self, client):
        """测试创建任务需要认证"""
        response = client.post('/api/tasks', json={
            'name': 'Test Task',
            'type': 'sync'
        })
        assert response.status_code == 401
    
    def test_get_tasks_requires_auth(self, client):
        """测试获取任务列表需要认证"""
        response = client.get('/api/tasks')
        assert response.status_code == 401


@pytest.mark.integration
@pytest.mark.api
class TestStorageAPI:
    """存储API集成测试"""
    
    def test_create_storage_requires_auth(self, client):
        """测试创建存储需要认证"""
        response = client.post('/api/storages', json={
            'name': 'Test Storage',
            'type': 'local'
        })
        assert response.status_code == 401
    
    def test_get_storages_requires_auth(self, client):
        """测试获取存储列表需要认证"""
        response = client.get('/api/storages')
        assert response.status_code == 401


@pytest.mark.integration
@pytest.mark.api
class TestUserAPI:
    """用户API集成测试"""
    
    def test_get_users_requires_auth(self, client):
        """测试获取用户列表需要认证"""
        response = client.get('/api/users')
        assert response.status_code == 401
    
    def test_get_profile_requires_auth(self, client):
        """测试获取个人资料需要认证"""
        response = client.get('/api/auth/profile')
        assert response.status_code == 401


@pytest.mark.integration
@pytest.mark.db
class TestDatabaseOperations:
    """数据库操作集成测试"""
    
    def test_user_crud(self, app):
        """测试用户CRUD操作"""
        with app.app_context():
            # Create
            user = User(
                username='crudtest',
                email='crudtest@example.com'
            )
            user.set_password('testpass')
            db.session.add(user)
            db.session.commit()
            
            assert user.id is not None
            
            # Read
            found_user = User.query.filter_by(username='crudtest').first()
            assert found_user is not None
            assert found_user.email == 'crudtest@example.com'
            
            # Update
            found_user.email = 'updated@example.com'
            db.session.commit()
            
            updated_user = User.query.get(found_user.id)
            assert updated_user.email == 'updated@example.com'
            
            # Delete
            db.session.delete(updated_user)
            db.session.commit()
            
            deleted_user = User.query.get(found_user.id)
            assert deleted_user is None

