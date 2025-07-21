from werkzeug.security import check_password_hash
from backend import db
from backend.app.models import User

class AuthService:
    """认证服务类"""
    
    def authenticate(self, username: str, password: str) -> User:
        """验证用户凭据"""
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password_hash, password):
            return user
        return None
        
    def authenticate_by_email(self, email: str, password: str) -> 'User':
        """通过邮箱验证用户凭据"""
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password_hash, password):
            return user
        return None
        
    def change_password(self, user_id: int, old_password: str, new_password: str) -> bool:
        """修改用户密码"""
        user = User.query.get(user_id)
        if not user or not check_password_hash(user.password_hash, old_password):
            return False
            
        user.set_password(new_password)
        db.session.commit()
        return True 