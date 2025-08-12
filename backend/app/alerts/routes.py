from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
from flask_jwt_extended import jwt_required, get_jwt_identity
from backend import db
from backend.app.alerts.services import AlertService
from backend.app.utils.decorators import handle_errors, require_user
from . import alerts_bp
import logging
from backend.app.models.user import User

logger = logging.getLogger(__name__)

alert_service = AlertService()

@alerts_bp.route('/policies', methods=['GET'])
@jwt_required()
@handle_errors
def get_alert_policies():
    """获取告警策略列表"""
    user_id = get_jwt_identity()
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 12, type=int)
    policy_type = request.args.get('policy_type', '')
    level = request.args.get('level', '')
    enabled = request.args.get('enabled', '')
    keyword = request.args.get('keyword', '')
    
    policies = alert_service.get_policies(
        user_id=user_id,
        page=page,
        per_page=per_page,
        policy_type=policy_type,
        level=level,
        enabled=enabled,
        keyword=keyword
    )
    
    return jsonify(policies)

@alerts_bp.route('/policies', methods=['POST'])
@jwt_required()
@handle_errors
def create_alert_policy():
    """创建告警策略"""
    data = request.get_json()
    user_id = get_jwt_identity()
    
    policy = alert_service.create_policy(data, user_id)
    return jsonify({
        'message': '告警策略创建成功',
        'policy': policy.to_dict()
    })

@alerts_bp.route('/policies/<policy_id>', methods=['GET'])
@jwt_required()
@handle_errors
def get_alert_policy(policy_id):
    """获取告警策略详情"""
    user_id = get_jwt_identity()
    policy = alert_service.get_policy(policy_id, user_id)
    return jsonify(policy.to_dict())

@alerts_bp.route('/policies/<policy_id>', methods=['PUT'])
@jwt_required()
@handle_errors
def update_alert_policy(policy_id):
    """更新告警策略"""
    data = request.get_json()
    user_id = get_jwt_identity()
    
    policy = alert_service.update_policy(policy_id, data, user_id)
    return jsonify({
        'message': '告警策略更新成功',
        'policy': policy.to_dict()
    })

@alerts_bp.route('/policies/<policy_id>', methods=['DELETE'])
@jwt_required()
@handle_errors
def delete_alert_policy(policy_id):
    """删除告警策略"""
    user_id = get_jwt_identity()
    alert_service.delete_policy(policy_id, user_id)
    return jsonify({'message': '告警策略删除成功'})


@alerts_bp.route('/policies/<policy_id>/toggle', methods=['PUT'])
@jwt_required()
@handle_errors
def toggle_alert_policy(policy_id):
    """切换告警策略启用状态"""
    user_id = get_jwt_identity()
    policy = alert_service.toggle_policy(policy_id, user_id)
    return jsonify({
        'message': f'告警策略已{"启用" if policy.enabled else "禁用"}',
        'policy': policy.to_dict()
    })

@alerts_bp.route('/policies/<policy_id>/test', methods=['POST'])
@jwt_required()
@handle_errors
def test_alert_policy(policy_id):
    """测试告警策略"""
    user_id = get_jwt_identity()
    result = alert_service.test_policy(policy_id, user_id)
    return jsonify({
        'message': '告警策略测试完成',
        'result': result
    })

@alerts_bp.route('/statistics', methods=['GET'])
@jwt_required()
@handle_errors
def get_alert_statistics():
    """获取告警统计信息"""
    try:
        time_range = request.args.get('range', '24h')
        stats = alert_service.get_alert_statistics(time_range)
        
        return jsonify(stats)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@alerts_bp.route('/instances', methods=['GET'])
@jwt_required()
@handle_errors
def get_alert_instances():
    """获取告警实例列表"""
    user_id = get_jwt_identity()
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    status = request.args.get('status', '')
    severity = request.args.get('severity', '')
    
    instances = alert_service.get_instances(
        user_id=user_id,
        page=page,
        per_page=per_page,
        status=status,
        severity=severity
    )
    
    return jsonify(instances)

@alerts_bp.route('/instances/<instance_id>/resolve', methods=['PUT'])
@jwt_required()
@handle_errors
def resolve_alert_instance(instance_id):
    """解决告警实例"""
    user_id = get_jwt_identity()
    alert_service.resolve_instance(instance_id, user_id)
    return jsonify({'message': '告警已解决'})

@alerts_bp.route('/resources', methods=['GET'])
@jwt_required()
@handle_errors
def get_monitorable_resources():
    """获取可监控的资源列表"""
    user_id = get_jwt_identity()
    resources = alert_service.get_monitorable_resources(user_id)
    return jsonify({'resources': resources})

@alerts_bp.route('/events', methods=['GET'])
@jwt_required()
@handle_errors
def get_monitorable_events():
    """获取可监控的事件列表"""
    user_id = get_jwt_identity()
    events = alert_service.get_monitorable_events()
    return jsonify({'events': events})

@alerts_bp.route('/templates', methods=['GET'])
@jwt_required()
@handle_errors
def get_alert_templates():
    """获取告警策略模板"""
    user_id = get_jwt_identity()
    category = request.args.get('category', '')
    template_type = request.args.get('template_type', '')
    
    templates = alert_service.get_templates(
        user_id=user_id,
        category=category,
        template_type=template_type
    )
    return jsonify({'templates': templates})

@alerts_bp.route('/templates', methods=['POST'])
@jwt_required()
@handle_errors
def create_alert_template():
    """创建告警模板"""
    data = request.get_json()
    user_id = get_jwt_identity()
    data['user_id'] = user_id
    
    template = alert_service.create_template(data)
    return jsonify({
        'message': '告警模板创建成功',
        'template': template.to_dict()
    }), 201

@alerts_bp.route('/templates/<template_id>', methods=['GET'])
@jwt_required()
@handle_errors
def get_alert_template(template_id):
    """获取告警模板详情"""
    user_id = get_jwt_identity()
    template = alert_service.get_template(template_id, user_id)
    return jsonify({'template': template.to_dict()})

@alerts_bp.route('/templates/<template_id>', methods=['PUT'])
@jwt_required()
@handle_errors
def update_alert_template(template_id):
    """更新告警模板"""
    data = request.get_json()
    user_id = get_jwt_identity()
    template = alert_service.update_template(template_id, user_id, data)
    return jsonify({
        'message': '告警模板更新成功',
        'template': template.to_dict()
    })

@alerts_bp.route('/templates/<template_id>', methods=['DELETE'])
@jwt_required()
@handle_errors
def delete_alert_template(template_id):
    """删除告警模板"""
    user_id = get_jwt_identity()
    alert_service.delete_template(template_id, user_id)
    return jsonify({'message': '告警模板删除成功'})

@alerts_bp.route('/templates/<template_id>/use', methods=['POST'])
@jwt_required()
@handle_errors
def use_alert_template(template_id):
    """使用告警模板"""
    user_id = get_jwt_identity()
    result = alert_service.use_template(template_id, user_id)
    return jsonify({
        'message': '模板使用成功',
        'data': result
    })

@alerts_bp.route('/templates/categories', methods=['GET'])
@jwt_required()
@handle_errors
def get_template_categories():
    """获取模板分类列表"""
    categories = alert_service.get_template_categories()
    return jsonify({'categories': categories})

@alerts_bp.route('/templates/init', methods=['POST'])
@jwt_required()
@handle_errors
def init_system_templates():
    """初始化系统模板"""
    user_id = get_jwt_identity()
    # 检查是否为管理员
    user = User.query.get(user_id)
    if not user or user.role != 'admin':
        return jsonify({'message': '只有管理员可以初始化系统模板'}), 403
    
    alert_service._init_system_templates()
    return jsonify({'message': '系统模板初始化成功'})

@alerts_bp.route('/templates/<template_id>/render', methods=['POST'])
@jwt_required()
@handle_errors
def render_alert_template(template_id):
    """渲染告警模板"""
    data = request.get_json()
    variables = data.get('variables', {})
    
    result = alert_service.render_template(template_id, variables)
    return jsonify({
        'status': 'success',
        'data': result
    })

@alerts_bp.route('/templates/<template_id>/variables', methods=['GET'])
@jwt_required()
@handle_errors
def get_template_variables(template_id):
    """获取模板支持的变量"""
    result = alert_service.get_template_variables(template_id)
    return jsonify({
        'status': 'success',
        'data': result
    })

@alerts_bp.route('/templates/preview', methods=['POST'])
@jwt_required()
@handle_errors
def preview_template():
    """预览模板效果"""
    data = request.get_json()
    template_data = data.get('template', {})
    variables = data.get('variables', {})
    
    # 创建临时模板进行预览
    title = template_data.get('title_template', '')
    content = template_data.get('content_template', '')
    
    # 替换变量
    for key, value in variables.items():
        placeholder = f"{{{key}}}"
        title = title.replace(placeholder, str(value))
        content = content.replace(placeholder, str(value))
    
    return jsonify({
        'status': 'success',
        'data': {
            'title': title,
            'content': content
        }
    })

@alerts_bp.route('/policies/with-templates', methods=['GET'])
@jwt_required()
@handle_errors
def get_policies_with_templates():
    """获取告警策略列表（包含模板信息）"""
    user_id = get_jwt_identity()
    policy_type = request.args.get('policy_type', '')
    enabled = request.args.get('enabled')
    if enabled is not None:
        enabled = enabled.lower() == 'true'
    
    policies = alert_service.get_policies_with_templates(user_id, policy_type, enabled)
    return jsonify({
        'status': 'success',
        'data': policies
    })

@alerts_bp.route('/categories', methods=['GET'])
@jwt_required()
@handle_errors
def get_alert_categories():
    """获取告警分类信息"""
    user_id = get_jwt_identity()
    categories = alert_service.get_alert_categories()
    return jsonify({'categories': categories})

@alerts_bp.route('/resource-types', methods=['GET'])
@jwt_required()
@handle_errors
def get_resource_types():
    """获取资源类型列表"""
    resource_types = alert_service.get_resource_types()
    return jsonify({'resource_types': resource_types})

@alerts_bp.route('/resource-items', methods=['GET'])
@jwt_required()
@handle_errors
def get_resource_items():
    """获取资源条目列表"""
    resource_type_code = request.args.get('resource_type_code', '')
    resource_items = alert_service.get_resource_items(resource_type_code)
    return jsonify({'resource_items': resource_items})

@alerts_bp.route('/event-types', methods=['GET'])
@jwt_required()
@handle_errors
def get_event_types():
    """获取事件类型列表"""
    event_types = alert_service.get_event_types()
    return jsonify({'event_types': event_types})

@alerts_bp.route('/event-actions', methods=['GET'])
@jwt_required()
@handle_errors
def get_event_actions():
    """获取事件动作列表"""
    event_type_code = request.args.get('event_type_code', '')
    event_actions = alert_service.get_event_actions(event_type_code)
    return jsonify({'event_actions': event_actions})

@alerts_bp.route('/event-results', methods=['GET'])
@jwt_required()
@handle_errors
def get_event_results():
    """获取事件结果列表"""
    event_results = alert_service.get_event_results()
    return jsonify({'event_results': event_results})

@alerts_bp.route('/init-data', methods=['POST'])
@jwt_required()
@handle_errors
def init_alert_data():
    """初始化告警系统数据"""
    user_id = get_jwt_identity()
    # 检查是否为管理员
    user = User.query.get(user_id)
    if not user or user.role != 'admin':
        return jsonify({'message': '只有管理员可以初始化系统数据'}), 403
    
    try:
        from backend.app.alerts.init_data import init_all_alert_data
        init_all_alert_data()
        return jsonify({'message': '告警系统数据初始化成功'})
    except Exception as e:
        return jsonify({'error': f'初始化失败: {str(e)}'}), 500