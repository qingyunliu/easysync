# 在 routes.py 文件末尾添加以下接口

@nodes_bp.route('/rclone/upload-package', methods=['POST'])
@jwt_required()
def upload_rclone_package():
    """
    上传 rclone 安装包到服务器
    
    上传的文件必须是 .zip 格式的 rclone 安装包
    """
    try:
        from backend.app.utils.rclone_manager import (
            RCLONE_BASE_DIR, 
            RCLONE_PACKAGE_NAME
        )
        
        # 检查是否有文件上传
        if 'file' not in request.files:
            return jsonify({
                'status': 'error',
                'message': '未找到上传文件'
            }), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({
                'status': 'error',
                'message': '未选择文件'
            }), 400
        
        # 检查文件扩展名
        if not file.filename.endswith('.zip'):
            return jsonify({
                'status': 'error',
                'message': '只支持 .zip 格式的安装包'
            }), 400
        
        # 确保目录存在
        import os
        os.makedirs(RCLONE_BASE_DIR, exist_ok=True)
        
        # 保存文件
        package_path = os.path.join(RCLONE_BASE_DIR, RCLONE_PACKAGE_NAME)
        file.save(package_path)
        
        # 验证文件
        file_size = os.path.getsize(package_path)
        
        if file_size < 1024 * 1024:  # 小于 1MB
            return jsonify({
                'status': 'error',
                'message': '文件太小，可能不是有效的安装包'
            }), 400
        
        # 记录审计日志
        user_id = get_jwt_identity()
        AuditService.log_node_operation(
            user_id=user_id,
            action='upload_rclone_package',
            node_id=None,
            node_name='system',
            details={
                'filename': RCLONE_PACKAGE_NAME,
                'size': file_size
            },
            result='success'
        )
        
        return jsonify({
            'status': 'success',
            'message': f'rclone 安装包上传成功',
            'data': {
                'filename': RCLONE_PACKAGE_NAME,
                'size': file_size,
                'path': package_path
            }
        }), 200
        
    except Exception as e:
        logger.error(f"上传 rclone 安装包失败: {e}")
        return jsonify({
            'status': 'error',
            'message': f'上传失败: {str(e)}'
        }), 500


@nodes_bp.route('/rclone/package-info', methods=['GET'])
@jwt_required()
def get_rclone_package_info():
    """
    获取 rclone 安装包信息
    """
    try:
        from backend.app.utils.rclone_manager import get_rclone_manager
        
        rclone_manager = get_rclone_manager()
        package_info = rclone_manager.get_package_info()
        
        return jsonify({
            'status': 'success',
            'message': '获取 rclone 安装包信息成功',
            'data': package_info
        }), 200
        
    except Exception as e:
        logger.error(f"获取 rclone 安装包信息失败: {e}")
        return jsonify({
            'status': 'error',
            'message': f'获取失败: {str(e)}'
        }), 500