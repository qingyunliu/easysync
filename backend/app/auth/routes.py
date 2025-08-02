from flask import Blueprint, request, jsonify, session, send_file
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity
from . import auth_bp
from .services import AuthService, AuditService
from backend.app.models import User, AuditLog
from captcha.image import ImageCaptcha
import io
import random
import string
import uuid
from backend.app.utils.email_utils import send_email
from datetime import datetime, timedelta
import os
from backend.app.notifications.services import NotificationService

auth_service = AuthService()
notification_service = NotificationService()

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
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    captcha = data.get('captcha', '').lower()
    captcha_id = data.get('captcha_id')
    # 校验验证码
    if not captcha_id or not captcha:
        AuditService.log_operation(
            user_id=None,
            action='login',
            resource_type='user',
            details={'error': '验证码不能为空', 'username': username},
            result='failed'
        )
        return jsonify({'status': 'fail', 'msg': '验证码不能为空'}), 400
    real_code = session.get('captcha_' + captcha_id)
    if not real_code or captcha != real_code:
        AuditService.log_operation(
            user_id=None,
            action='login',
            resource_type='user',
            details={'error': '验证码错误', 'username': username},
            result='failed'
        )
        return jsonify({'status': 'fail', 'msg': '验证码错误'}), 400
    
    if not username or not password:
        AuditService.log_operation(
            user_id=None,
            action='login',
            resource_type='user',
            details={'error': '用户名和密码不能为空', 'username': username},
            result='failed'
        )
        return jsonify({'error': '用户名和密码不能为空'}), 400
        
    # 支持用户名或邮箱登录
    user = None
    if '@' in username:
        user = auth_service.authenticate_by_email(email=username, password=password)
    else:
        user = auth_service.authenticate(username, password)
    if not user:
        AuditService.log_operation(
            user_id=None,
            action='login',
            resource_type='user',
            details={'error': '用户名或密码错误', 'username': username},
            result='failed'
        )
        return jsonify({'error': '用户名或密码错误'}), 401
    if not user.email_verified:
        AuditService.log_operation(
            user_id=user.id,
            action='login',
            resource_type='user',
            resource_id=user.id,
            details={'error': '邮箱未验证', 'username': username},
            result='failed'
        )
        return jsonify({'status': 'fail', 'msg': '请先完成邮箱验证'}), 403
        
    access_token = create_access_token(identity=str(user.id))
    refresh_token = create_refresh_token(identity=str(user.id))
    # 登录成功后可删除验证码
    session.pop('captcha_' + captcha_id, None)
    
    # 更新登录信息
    user.last_login = datetime.utcnow()
    user.last_login_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    user.login_count += 1
    from backend import db
    db.session.commit()
    
    # 生成令牌
    access_token = create_access_token(identity=user.id)
    refresh_token = create_refresh_token(identity=user.id)
    
    # 发送用户登录通知
    notification_service.create_notification(
        user_id=user.id,
        type='user_login',
        title=f'用户登录: {user.username}',
        content=f'用户 {user.username} 已成功登录。\n登录时间: {datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")}\nIP地址: {request.headers.get("X-Forwarded-For", request.remote_addr)}',
        level='info'
    )
    
    # 登录审计日志
    try:
        ip = request.headers.get('X-Forwarded-For', request.remote_addr)
        user_agent = request.headers.get('User-Agent', '')
        AuditService.log_login(user.id, ip, user_agent)
    except Exception as e:
        from backend import db
        db.session.rollback()
        AuditService.log_operation(
            user_id=user.id,
            action='login',
            resource_type='user',
            resource_id=user.id,
            details={'error': str(e)},
            result='failed'
        )
        # 日志记录失败不影响登录流程

    AuditService.log_operation(
        user_id=user.id,
        action='login',
        resource_type='user',
        resource_id=user.id,
        details={'msg': '登录成功', 'username': user.username},
        result='success'
    )

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
    try:
        current_user_id = get_jwt_identity()
        
        # 验证用户是否仍然存在且有效
        user = User.query.get(current_user_id)
        if not user:
            return jsonify({
                'status': 'error',
                'error_code': 'REFRESH_TOKEN_INVALID',
                'message': '用户不存在，请重新登录'
            }), 401
            
        if not user.email_verified:
            return jsonify({
                'status': 'error', 
                'error_code': 'REFRESH_TOKEN_INVALID',
                'message': '用户邮箱未验证，请重新登录'
            }), 401
        
        # 创建新的access token
        access_token = create_access_token(identity=str(current_user_id))
        
        # 记录token刷新日志
        AuditService.log_operation(
            user_id=current_user_id,
            action='refresh_token',
            resource_type='user',
            resource_id=current_user_id,
            details={'msg': 'token刷新成功'},
            result='success'
        )
        
        return jsonify({
            'status': 'success',
            'access_token': access_token
        })
        
    except Exception as e:
        # 处理refresh token过期或无效的情况
        error_msg = str(e)
        
        if 'expired' in error_msg.lower() or 'invalid' in error_msg.lower():
            # refresh token过期或无效
            AuditService.log_operation(
                user_id=None,
                action='refresh_token',
                resource_type='user',
                details={'error': 'refresh token过期或无效'},
                result='failed'
            )
            
            return jsonify({
                'status': 'error',
                'error_code': 'REFRESH_TOKEN_EXPIRED',
                'message': 'refresh token已过期，请重新登录'
            }), 401
        else:
            # 其他错误
            AuditService.log_operation(
                user_id=None,
                action='refresh_token',
                resource_type='user',
                details={'error': error_msg},
                result='failed'
            )
            
            return jsonify({
                'status': 'error',
                'error_code': 'REFRESH_TOKEN_ERROR',
                'message': 'token刷新失败，请重新登录'
            }), 401

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
        AuditService.log_operation(
            user_id=None,
            action='forgot_password',
            resource_type='user',
            details={'error': '邮箱不能为空'},
            result='failed'
        )
        return jsonify({'status': 'fail', 'msg': '邮箱不能为空'}), 400
    user = User.query.filter_by(email=email).first()
    if not user:
        AuditService.log_operation(
            user_id=None,
            action='forgot_password',
            resource_type='user',
            details={'error': '该邮箱未注册', 'email': email},
            result='failed'
        )
        return jsonify({'status': 'fail', 'msg': '该邮箱未注册'}), 404
    token = str(uuid.uuid4())
    user.reset_password_token = token
    user.reset_password_expire = datetime.utcnow() + timedelta(hours=1)
    from backend import db
    db.session.commit()
    frontend_url = os.environ.get('FRONTEND_URL', 'localhost:5173')
    reset_url = f"{frontend_url}/reset_password?token={token}"
    try:
        send_email(
            email,
            "重置密码",
            f"请点击以下链接重置您的密码（1小时内有效）：<a href='{reset_url}'>{reset_url}</a>"
        )
        
        # 发送密码重置请求通知
        notification_service.create_notification(
            user_id=user.id,
            type='security_password_reset',
            title=f'密码重置请求: {user.username}',
            content=f'用户 {user.username} 已请求重置密码。\n重置链接已发送到邮箱: {email}',
            level='warning'
        )
        
        AuditService.log_operation(
            user_id=user.id,
            action='forgot_password',
            resource_type='user',
            resource_id=user.id,
            details={'msg': '重置密码邮件已发送', 'email': email},
            result='success'
        )
    except Exception as e:
        AuditService.log_operation(
            user_id=user.id,
            action='forgot_password',
            resource_type='user',
            resource_id=user.id,
            details={'error': str(e), 'email': email},
            result='failed'
        )
        return jsonify({'status': 'fail', 'msg': '邮件发送失败'}), 500
    return jsonify({'status': 'success', 'msg': '重置密码邮件已发送，请查收邮箱'})

@auth_bp.route('/reset_password', methods=['POST'])
def reset_password():
    data = request.get_json()
    token = data.get('token')
    new_password = data.get('password')
    if not token or not new_password:
        AuditService.log_operation(
            user_id=None,
            action='reset_password',
            resource_type='user',
            details={'error': '参数不完整'},
            result='failed'
        )
        return jsonify({'status': 'fail', 'msg': '参数不完整'}), 400
    user = User.query.filter_by(reset_password_token=token).first()
    if not user or not user.reset_password_expire or user.reset_password_expire < datetime.utcnow():
        AuditService.log_operation(
            user_id=None,
            action='reset_password',
            resource_type='user',
            details={'error': '重置链接无效或已过期'},
            result='failed'
        )
        return jsonify({'status': 'fail', 'msg': '重置链接无效或已过期'}), 400
    try:
        user.set_password(new_password)
        user.reset_password_token = None
        user.reset_password_expire = None
        from backend import db
        db.session.commit()
        
        # 发送密码重置成功通知
        notification_service.create_notification(
            user_id=user.id,
            type='user_password_changed',
            title=f'密码已重置: {user.username}',
            content=f'用户 {user.username} 的密码已成功重置。\n重置时间: {datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")}',
            level='success'
        )
        
        AuditService.log_operation(
            user_id=user.id,
            action='reset_password',
            resource_type='user',
            resource_id=user.id,
            details={'msg': '密码重置成功'},
            result='success'
        )
    except Exception as e:
        AuditService.log_operation(
            user_id=user.id,
            action='reset_password',
            resource_type='user',
            resource_id=user.id,
            details={'error': str(e)},
            result='failed'
        )
        return jsonify({'status': 'fail', 'msg': '密码重置失败'}), 500
    return jsonify({'status': 'success', 'msg': '密码重置成功'}) 

@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    """用户退出登录"""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    # 发送用户登出通知
    notification_service.create_notification(
        user_id=user.id,
        type='user_logout',
        title=f'用户登出: {user.username}',
        content=f'用户 {user.username} 已退出登录。\n登出时间: {datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")}',
        level='info'
    )
    
    # 退出登录审计日志
    try:
        ip = request.headers.get('X-Forwarded-For', request.remote_addr)
        user_agent = request.headers.get('User-Agent', '')
        AuditService.log_logout(user.id, ip, user_agent)
        AuditService.log_operation(
            user_id=user.id,
            action='logout',
            resource_type='user',
            resource_id=user.id,
            details={'msg': '退出登录成功', 'username': user.username},
            result='success'
        )
    except Exception as e:
        from backend import db
        db.session.rollback()
        AuditService.log_operation(
            user_id=user.id,
            action='logout',
            resource_type='user',
            resource_id=user.id,
            details={'error': str(e)},
            result='failed'
        )
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
    action = request.args.get('action', 'all')  # 支持筛选操作类型
    
    query = AuditLog.query
    
    # 只查询登录和登出操作
    query = query.filter(AuditLog.action.in_(['login', 'logout']))
    
    # 如果指定了具体操作类型，进一步过滤
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

@auth_bp.route('/operation-logs', methods=['GET'])
@jwt_required()
def get_operation_logs():
    """获取操作审计日志"""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 20))
    action = request.args.get('action', 'all')
    resource_type = request.args.get('resource_type', 'all')
    
    query = AuditLog.query
    
    # 过滤非登录/登出操作
    query = query.filter(~AuditLog.action.in_(['login', 'logout']))
    
    # 按操作类型过滤
    if action != 'all':
        query = query.filter_by(action=action)
    
    # 按资源类型过滤
    if resource_type != 'all':
        query = query.filter_by(resource_type=resource_type)
    
    # 权限控制：非管理员只能看到自己的操作
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