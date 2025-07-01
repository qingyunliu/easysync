from backend import db
from backend.app.models import User

class UserService:
    """用户服务类"""
    
    def create_user(self, username: str, password: str, email: str, role: str = 'user') -> User:
        """创建新用户"""
        user = User(username=username, email=email, role=role)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        return user
        
    def get_users(self):
        """获取所有用户"""
        return User.query.all()
        
    def get_user(self, user_id: str) -> User:
        """获取用户详情"""
        return User.query.get(user_id)
        
    def update_user(self, user_id: str, email: str = None, role: str = None) -> User:
        """更新用户信息"""
        user = User.query.get(user_id)
        if not user:
            return None
            
        if email:
            user.email = email
        if role:
            user.role = role
            
        db.session.commit()
        return user
        
    def delete_user(self, user_id: str) -> bool:
        """删除用户"""
        user = User.query.get(user_id)
        if not user:
            return False
            
        db.session.delete(user)
        db.session.commit()
        return True

    def update_user_avatar(self, user_id: str, avatar_url: str) -> User:
        """更新用户头像"""
        user = User.query.get(user_id)
        if not user:
            return None
            
        user.avatar = avatar_url
        db.session.commit()
        return user 