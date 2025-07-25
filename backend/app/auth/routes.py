from flask import Blueprint, request, jsonify, session, send_file
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity
from . import auth_bp
from .services import AuthService
from backend.app.models import User, AuditLog
from captcha.image import ImageCaptcha
import io
import random
import string
import uuid
from backend.app.utils.email_utils import send_email
from datetime import datetime, timedelta
import os

auth_service = AuthService()

@auth_bp.route('/captcha', methods=['GET'])
def get_captcha():
    code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
    captcha_id = str(uuid.uuid4())
    session['captcha_' + captcha_id] = code.lower()
    image = ImageCaptcha(width=150, height=50)
    data = image.generate(code)
    resp = send_file(data, mimetype='image/png')
    resp.headers['Captcha-Id'] = captcha_id
    resp.headers['Access-Control-Expose-Headers'] = 'Captcha-Id'
    return resp

@auth_bp.route('', methods=['POST'])
def login():
    """用户登录"""
    data = request.json
    username = data.get('username')
    password = data.get('password')
    captcha = data.get('captcha', '').lower()
    captcha_id = data.get('captcha_id')
    # 校验验证码
    if not captcha_id or not captcha:
        return jsonify({'status': 'fail', 'msg': '验证码不能为空'}), 400
    real_code = session.get('captcha_' + captcha_id)
    if not real_code or captcha != real_code:
        return jsonify({'status': 'fail', 'msg': '验证码错误'}), 400
    
    if not username or not password:
        return jsonify({'error': '用户名和密码不能为空'}), 400
        
    # 支持用户名或邮箱登录
    user = None
    if '@' in username:
        user = auth_service.authenticate_by_email(email=username, password=password)
    else:
        user = auth_service.authenticate(username, password)
    if not user:
        return jsonify({'error': '用户名或密码错误'}), 401
    if not user.email_verified:
        return jsonify({'status': 'fail', 'msg': '请先完成邮箱验证'}), 403
        
    access_token = create_access_token(identity=str(user.id))
    refresh_token = create_refresh_token(identity=str(user.id))
    
    # 登录成功后可删除验证码
    session.pop('captcha_' + captcha_id, None)

    # 登录审计日志
    try:
        ip = request.headers.get('X-Forwarded-For', request.remote_addr)
        user_agent = request.headers.get('User-Agent', '')
        audit_log = AuditLog(
            user_id=user.id,
            action='login',
            resource_type='user',
            resource_id=user.id,
            details={
                'ip': ip,
                'user_agent': user_agent,
                'login_time': datetime.utcnow().isoformat()
            }
        )
        from backend import db
        db.session.add(audit_log)
        db.session.commit()
    except Exception as e:
        from backend import db
        db.session.rollback()
        # 日志记录失败不影响登录流程

    return jsonify({
        'status': 'success',
        'msg': '登录成功',
        'data': {
            'access_token': access_token,
            'refresh_token': refresh_token,
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'is_admin': user.is_admin,
                'role': user.role
            }
        }
    })

@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """刷新访问令牌"""
    current_user_id = get_jwt_identity()
    access_token = create_access_token(identity=str(current_user_id))
    return jsonify({'access_token': access_token})

@auth_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    """获取当前用户信息"""
    current_user_id = get_jwt_identity()
    user = User.query.get(int(current_user_id))
    if not user:
        return jsonify({'error': '用户不存在'}), 404
        
    return jsonify({
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'role': user.role,
        'created_at': user.created_at.isoformat()
    }) 

@auth_bp.route('/forgot_password', methods=['POST'])
def forgot_password():
    data = request.get_json()
    email = data.get('email')
    if not email:
        return jsonify({'status': 'fail', 'msg': '邮箱不能为空'}), 400
    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({'status': 'fail', 'msg': '该邮箱未注册'}), 404
    token = str(uuid.uuid4())
    user.reset_password_token = token
    user.reset_password_expire = datetime.utcnow() + timedelta(hours=1)
    from backend import db
    db.session.commit()
    frontend_url = os.environ.get('FRONTEND_URL', 'localhost:5173')
    reset_url = f"{frontend_url}/reset_password?token={token}"
    send_email(
        email,
        "重置密码",
        f"请点击以下链接重置您的密码（1小时内有效）：<a href='{reset_url}'>{reset_url}</a>"
    )
    return jsonify({'status': 'success', 'msg': '重置密码邮件已发送，请查收邮箱'})

@auth_bp.route('/reset_password', methods=['POST'])
def reset_password():
    data = request.get_json()
    token = data.get('token')
    new_password = data.get('password')
    if not token or not new_password:
        return jsonify({'status': 'fail', 'msg': '参数不完整'}), 400
    user = User.query.filter_by(reset_password_token=token).first()
    if not user or not user.reset_password_expire or user.reset_password_expire < datetime.utcnow():
        return jsonify({'status': 'fail', 'msg': '重置链接无效或已过期'}), 400
    user.set_password(new_password)
    user.reset_password_token = None
    user.reset_password_expire = None
    from backend import db
    db.session.commit()
    return jsonify({'status': 'success', 'msg': '密码重置成功'}) 

@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    """用户退出登录"""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    # 退出登录审计日志
    try:
        ip = request.headers.get('X-Forwarded-For', request.remote_addr)
        user_agent = request.headers.get('User-Agent', '')
        audit_log = AuditLog(
            user_id=user.id,
            action='logout',
            resource_type='user',
            resource_id=user.id,
            details={
                'ip': ip,
                'user_agent': user_agent,
                'logout_time': datetime.utcnow().isoformat()
            }
        )
        from backend import db
        db.session.add(audit_log)
        db.session.commit()
    except Exception as e:
        from backend import db
        db.session.rollback()
        # 日志记录失败不影响退出流程
    
    return jsonify({
        'status': 'success',
        'msg': '退出登录成功'
    })

@auth_bp.route('/audit-logs', methods=['GET'])
@jwt_required()
def get_audit_logs():
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 20))
    action = request.args.get('action', 'login')  # 支持筛选操作类型
    
    query = AuditLog.query
    if action != 'all':
        query = query.filter_by(action=action)
    
    if not user.is_admin:
        query = query.filter_by(user_id=current_user_id)
    
    query = query.order_by(AuditLog.created_at.desc())
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    logs = [log.to_dict() for log in pagination.items]
    
    return jsonify({
        'logs': logs,
        'total': pagination.total,
        'page': page,
        'per_page': per_page
    })