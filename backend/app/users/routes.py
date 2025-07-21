from flask import request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from . import users_bp
from .services import UserService
from backend.app.models import User
import os
from werkzeug.utils import secure_filename
import uuid
import imghdr
from PIL import Image
import io
from backend import db
from backend.app.utils.email_utils import send_email

user_service = UserService()

def allowed_file(filename):
    """检查文件类型是否允许"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

def validate_image(file):
    """验证图片文件的有效性"""
    # 检查文件头
    header = file.read(512)
    file.seek(0)  # 重置文件指针
    image_type = imghdr.what(None, header)
    if image_type not in ['jpeg', 'png', 'gif']:
        return False
    
    # 使用PIL验证图片
    try:
        img = Image.open(file)
        img.verify()  # 验证图片完整性
        file.seek(0)  # 重置文件指针
        return True
    except Exception:
        return False

@users_bp.route('', methods=['POST'])
def create_user():
    """创建新用户"""
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    email = data.get('email')
    role = data.get('role', 'user')
    
    if not all([username, password, email]):
        return jsonify({'error': '缺少必要字段'}), 400
        
    if User.query.filter_by(username=username).first():
        return jsonify({'error': '用户名已存在'}), 400
        
    if User.query.filter_by(email=email).first():
        return jsonify({'error': '邮箱已存在'}), 400
    
    # 生成邮箱验证token
    email_token = str(uuid.uuid4())
    try:
        user = user_service.create_user(username, password, email, role)
        user.email_verification_token = email_token
        user.email_verified = False

        verify_url = f"{os.environ.get('FRONTEND_URL')}/verify_email?token={email_token}"
        send_email(
            email,
            "邮箱验证",
            f"请点击以下链接验证您的邮箱：<a href='{verify_url}'>{verify_url}</a>"
        )
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"注册或发送验证邮件失败: {str(e)}")
        return jsonify({'error': '注册或发送验证邮件失败'}), 502

    return jsonify({
        'status': 'success',
        'msg': '用户注册成功，请前往邮箱验证',
        'data': {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'role': user.role,
            'created_at': user.created_at.isoformat()
        }
    }), 201

@users_bp.route('', methods=['GET'])
@jwt_required()
def get_users():
    """获取用户列表"""
    users = user_service.get_users()
    return jsonify([{
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'role': user.role,
        'created_at': user.created_at.isoformat()
    } for user in users])

@users_bp.route('/<string:user_id>', methods=['GET'])
@jwt_required()
def get_user(user_id):
    """获取用户详情"""
    user = user_service.get_user(user_id)
    if not user:
        return jsonify({'error': '用户不存在'}), 404
        
    return jsonify({
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'role': user.role,
        'created_at': user.created_at.isoformat()
    })

@users_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    """获取用户详情"""
    current_user_id = get_jwt_identity()
    user = user_service.get_user(current_user_id)
    if not user:
        return jsonify({'error': '用户不存在'}), 404
        
    return jsonify({
        'status': "success",
        'id': user.id,
        'data': user.to_dict()
    })

@users_bp.route('/<string:user_id>', methods=['PUT'])
@jwt_required()
def update_user(user_id):
    """更新用户信息"""
    data = request.get_json()
    email = data.get('email')
    role = data.get('role')
    
    user = user_service.update_user(user_id, email, role)
    if not user:
        return jsonify({'error': '用户不存在'}), 404
        
    return jsonify({
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'role': user.role,
        'created_at': user.created_at.isoformat()
    })

@users_bp.route('/<string:user_id>', methods=['DELETE'])
@jwt_required()
def delete_user(user_id):
    """删除用户"""
    if not user_service.delete_user(user_id):
        return jsonify({'error': '用户不存在'}), 404
    return '', 204

@users_bp.route('/<string:user_id>/avatar', methods=['POST'])
@jwt_required()
def upload_avatar(user_id):
    """上传用户头像"""
    # 验证当前用户是否有权限修改
    current_user_id = get_jwt_identity()
    if str(current_user_id) != str(user_id):
        return jsonify({'error': '没有权限修改其他用户的头像'}), 403
    
    if 'avatar' not in request.files:
        return jsonify({'error': '没有上传文件'}), 400
        
    file = request.files['avatar']
    if file.filename == '':
        return jsonify({'error': '没有选择文件'}), 400
    
    # 验证文件类型
    if not allowed_file(file.filename):
        return jsonify({'error': '不支持的文件类型'}), 400
    
    # 验证文件大小
    if len(file.read()) > current_app.config['MAX_CONTENT_LENGTH']:
        return jsonify({'error': '文件大小超过限制'}), 400
    file.seek(0)  # 重置文件指针
    
    # 验证图片有效性
    if not validate_image(file):
        return jsonify({'error': '无效的图片文件'}), 400
    file.seek(0)  # 重置文件指针
    
    try:
        # 生成安全的文件名
        filename = secure_filename(file.filename)
        # 生成唯一的文件名
        ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
        unique_filename = f"{uuid.uuid4()}.{ext}"
        
        # 确保上传目录存在
        upload_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], 'avatars')
        os.makedirs(upload_folder, exist_ok=True)
        
        # 处理图片
        img = Image.open(file)
        # 转换为RGB模式（如果是RGBA，去除透明通道）
        if img.mode in ('RGBA', 'LA'):
            background = Image.new('RGB', img.size, (255, 255, 255))
            background.paste(img, mask=img.split()[-1])
            img = background
        elif img.mode != 'RGB':
            img = img.convert('RGB')
        
        # 调整图片大小
        max_size = (800, 800)  # 最大尺寸
        img.thumbnail(max_size, Image.Resampling.LANCZOS)
        
        # 保存处理后的图片
        file_path = os.path.join(upload_folder, unique_filename)
        img.save(file_path, 'JPEG', quality=85, optimize=True)
        
        # 更新用户头像URL
        avatar_url = f"/uploads/avatars/{unique_filename}"
        user = user_service.update_user_avatar(user_id, avatar_url)
        
        if not user:
            return jsonify({'error': '用户不存在'}), 404
            
        return jsonify({
            'status': 'success',
            'message': '头像上传成功',
            'avatar_url': avatar_url
        })
        
    except Exception as e:
        current_app.logger.error(f"头像上传失败: {str(e)}")
        return jsonify({'error': '头像上传失败'}), 500 

@users_bp.route('/verify_email', methods=['GET'])
def verify_email():
    token = request.args.get('token')
    user = User.query.filter_by(email_verification_token=token).first()
    if not user:
        return jsonify({'status': 'fail', 'msg': '无效的验证链接'}), 400
    user.email_verified = True
    user.email_verification_token = None
    db.session.commit()
    return jsonify({'status': 'success', 'msg': '邮箱验证成功'}) 