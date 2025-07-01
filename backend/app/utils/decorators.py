from functools import wraps
from flask import jsonify, g
from flask_jwt_extended import jwt_required, get_jwt_identity
from backend.app.models import User, Task

def admin_required(f):
    """管理员权限装饰器"""
    @wraps(f)
    @jwt_required()
    def decorated_function(*args, **kwargs):
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        if not user or user.role != 'admin':
            return jsonify({"error": "需要管理员权限"}), 403
        return f(*args, **kwargs)
    return decorated_function

def task_owner_required(f):
    """任务所有者权限装饰器"""
    @wraps(f)
    @jwt_required()
    def decorated_function(task_id, *args, **kwargs):
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        task = Task.query.get_or_404(task_id)
        
        if not user:
            return jsonify({"error": "用户不存在"}), 404
            
        if task.user_id != current_user_id and user.role != 'admin':
            return jsonify({"error": "无权访问此任务"}), 403
            
        return f(task_id, *args, **kwargs)
    return decorated_function

def require_user(f):
    """要求用户登录的装饰器"""
    @wraps(f)
    @jwt_required()
    def decorated_function(*args, **kwargs):
        user_id = get_jwt_identity()
        if not user_id:
            return jsonify({'message': '未登录'}), 401
            
        user = User.query.get(user_id)
        if not user:
            return jsonify({'message': '用户不存在'}), 401
            
        # 将用户信息存储在g对象中
        g.user = user
        return f(*args, **kwargs)
    return decorated_function 