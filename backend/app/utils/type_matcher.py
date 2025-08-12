"""
类型匹配工具模块
用于处理告警策略、告警模板、通知渠道、通知对象之间的类型匹配关系
"""

from typing import List, Dict, Any, Optional
from backend.app.models.alert import AlertTemplate
from backend.app.models.notification import NotificationChannel, NotificationTarget


class TypeMatcher:
    """类型匹配器"""
    
    # 渠道类型 -> 模板类型 -> 对象类型的映射关系
    TYPE_MAPPING = {
        'email': {
            'template_type': 'email',
            'target_type': 'email'
        },
        'sms': {
            'template_type': 'sms', 
            'target_type': 'sms'
        },
        'webhook': {
            'template_type': 'webhook',
            'target_type': 'webhook'
        },
        'dingtalk': {
            'template_type': 'dingtalk',
            'target_type': 'dingtalk'
        },
        'slack': {
            'template_type': 'slack',
            'target_type': 'slack'
        }
    }
    
    @classmethod
    def get_compatible_types(cls, channel_types: List[str]) -> Dict[str, List[str]]:
        """
        根据渠道类型获取兼容的模板类型和对象类型
        
        Args:
            channel_types: 渠道类型列表，如 ['email', 'sms']
            
        Returns:
            包含兼容类型的字典
        """
        compatible_templates = []
        compatible_targets = []
        
        for channel_type in channel_types:
            if channel_type in cls.TYPE_MAPPING:
                mapping = cls.TYPE_MAPPING[channel_type]
                compatible_templates.append(mapping['template_type'])
                compatible_targets.append(mapping['target_type'])
        
        return {
            'template_types': list(set(compatible_templates)),  # 去重
            'target_types': list(set(compatible_targets))       # 去重
        }
    
    @classmethod
    def get_compatible_templates(cls, channel_types: List[str], user_id: str) -> List[Dict[str, Any]]:
        """
        根据渠道类型获取兼容的模板列表
        
        Args:
            channel_types: 渠道类型列表
            user_id: 用户ID
            
        Returns:
            兼容的模板列表
        """
        compatible_types = cls.get_compatible_types(channel_types)
        template_types = compatible_types['template_types']
        
        if not template_types:
            return []
        
        # 查询兼容的模板（系统模板 + 用户模板）
        templates = AlertTemplate.query.filter(
            AlertTemplate.template_type.in_(template_types),
            (AlertTemplate.user_id == user_id) | (AlertTemplate.is_system == True)
        ).all()
        
        return [template.to_dict() for template in templates]
    
    @classmethod
    def get_compatible_targets(cls, channel_types: List[str], user_id: str) -> List[Dict[str, Any]]:
        """
        根据渠道类型获取兼容的通知对象列表
        
        Args:
            channel_types: 渠道类型列表
            user_id: 用户ID
            
        Returns:
            兼容的通知对象列表
        """
        compatible_types = cls.get_compatible_types(channel_types)
        target_types = compatible_types['target_types']
        
        if not target_types:
            return []
        
        # 查询兼容的通知对象
        targets = NotificationTarget.query.filter(
            NotificationTarget.target_type.in_(target_types),
            NotificationTarget.user_id == user_id
        ).all()
        
        return [target.to_dict() for target in targets]
    
    @classmethod
    def get_compatible_channels(cls, template_type: str, user_id: str) -> List[Dict[str, Any]]:
        """
        根据模板类型获取兼容的渠道列表
        
        Args:
            template_type: 模板类型
            user_id: 用户ID
            
        Returns:
            兼容的渠道列表
        """
        # 反向查找：模板类型 -> 渠道类型
        compatible_channels = []
        for channel_type, mapping in cls.TYPE_MAPPING.items():
            if mapping['template_type'] == template_type:
                compatible_channels.append(channel_type)
        
        if not compatible_channels:
            return []
        
        # 查询兼容的渠道
        channels = NotificationChannel.query.filter(
            NotificationChannel.channel_type.in_(compatible_channels),
            NotificationChannel.user_id == user_id
        ).all()
        
        return [channel.to_dict() for channel in channels]
    
    @classmethod
    def validate_policy_configuration(cls, 
                                    notification_channels: List[str], 
                                    template_id: Optional[str], 
                                    notification_targets: List[str],
                                    user_id: str) -> Dict[str, Any]:
        """
        验证告警策略配置的类型匹配性
        
        Args:
            notification_channels: 通知渠道ID列表
            template_id: 模板ID
            notification_targets: 通知对象ID列表
            user_id: 用户ID
            
        Returns:
            验证结果字典
        """
        result = {
            'valid': True,
            'errors': [],
            'warnings': []
        }
        
        # 1. 获取选择的渠道类型
        if not notification_channels:
            result['errors'].append('必须选择至少一个通知渠道')
            result['valid'] = False
            return result
        
        # 查询渠道信息
        channels = NotificationChannel.query.filter(
            NotificationChannel.id.in_(notification_channels),
            NotificationChannel.user_id == user_id
        ).all()
        
        if len(channels) != len(notification_channels):
            result['errors'].append('部分通知渠道不存在或无权限访问')
            result['valid'] = False
            return result
        
        channel_types = [channel.channel_type for channel in channels]
        compatible_types = cls.get_compatible_types(channel_types)
        
        # 2. 验证模板类型
        if template_id:
            template = AlertTemplate.query.filter(
                (AlertTemplate.id == template_id) & 
                ((AlertTemplate.user_id == user_id) | (AlertTemplate.is_system == True))
            ).first()
            
            if not template:
                result['errors'].append('选择的模板不存在或无权限访问')
                result['valid'] = False
            elif template.template_type not in compatible_types['template_types']:
                result['errors'].append(f'模板类型 "{template.template_type}" 与选择的渠道类型不匹配')
                result['valid'] = False
        
        # 3. 验证通知对象类型
        if notification_targets:
            targets = NotificationTarget.query.filter(
                NotificationTarget.id.in_(notification_targets),
                NotificationTarget.user_id == user_id
            ).all()
            
            if len(targets) != len(notification_targets):
                result['errors'].append('部分通知对象不存在或无权限访问')
                result['valid'] = False
                return result
            
            for target in targets:
                if target.target_type not in compatible_types['target_types']:
                    result['warnings'].append(f'通知对象 "{target.name}" 的类型 "{target.target_type}" 与选择的渠道类型不匹配')
        
        return result
    
    @classmethod
    def get_type_display_name(cls, type_code: str) -> str:
        """
        获取类型的显示名称
        
        Args:
            type_code: 类型代码
            
        Returns:
            显示名称
        """
        display_names = {
            'email': '邮件',
            'sms': '短信',
            'webhook': 'WebHook',
            'dingtalk': '钉钉',
            'slack': 'Slack'
        }
        
        return display_names.get(type_code, type_code)
    
    @classmethod
    def get_all_supported_types(cls) -> List[Dict[str, str]]:
        """
        获取所有支持的类型
        
        Returns:
            支持的类型列表
        """
        return [
            {
                'code': code,
                'name': cls.get_type_display_name(code)
            }
            for code in cls.TYPE_MAPPING.keys()
        ]
    
    @classmethod
    def get_multi_channel_compatibility(cls, channel_types: List[str]) -> Dict[str, Any]:
        """
        获取多渠道配置的兼容性信息
        
        Args:
            channel_types: 渠道类型列表
            
        Returns:
            兼容性信息字典
        """
        if not channel_types:
            return {
                'compatible': False,
                'message': '未选择任何渠道类型',
                'template_strategy': 'none',
                'target_strategy': 'none'
            }
        
        if len(channel_types) == 1:
            return {
                'compatible': True,
                'message': '单渠道配置',
                'template_strategy': 'exact_match',
                'target_strategy': 'exact_match',
                'required_template_types': [cls.TYPE_MAPPING[channel_types[0]]['template_type']],
                'required_target_types': [cls.TYPE_MAPPING[channel_types[0]]['target_type']]
            }
        
        # 多渠道配置
        template_types = []
        target_types = []
        
        for channel_type in channel_types:
            if channel_type in cls.TYPE_MAPPING:
                mapping = cls.TYPE_MAPPING[channel_type]
                template_types.append(mapping['template_type'])
                target_types.append(mapping['target_type'])
        
        # 检查是否有重复类型
        unique_template_types = list(set(template_types))
        unique_target_types = list(set(target_types))
        
        if len(unique_template_types) == 1:
            template_strategy = 'single_type'
            template_message = f'所有渠道使用相同的模板类型: {unique_template_types[0]}'
        else:
            template_strategy = 'multi_type'
            template_message = f'需要多种模板类型: {", ".join(unique_template_types)}'
        
        if len(unique_target_types) == 1:
            target_strategy = 'single_type'
            target_message = f'所有渠道使用相同的对象类型: {unique_target_types[0]}'
        else:
            target_strategy = 'multi_type'
            target_message = f'需要多种对象类型: {", ".join(unique_target_types)}'
        
        return {
            'compatible': True,
            'message': f'多渠道配置 - {template_message}, {target_message}',
            'template_strategy': template_strategy,
            'target_strategy': target_strategy,
            'required_template_types': unique_template_types,
            'required_target_types': unique_target_types,
            'channel_type_mapping': {
                channel_type: {
                    'template_type': cls.TYPE_MAPPING[channel_type]['template_type'],
                    'target_type': cls.TYPE_MAPPING[channel_type]['target_type']
                }
                for channel_type in channel_types
                if channel_type in cls.TYPE_MAPPING
            }
        }
    
    @classmethod
    def validate_multi_channel_configuration(cls, 
                                           notification_channels: List[str], 
                                           template_id: Optional[str], 
                                           notification_targets: List[str],
                                           user_id: str) -> Dict[str, Any]:
        """
        验证多渠道配置
        
        Args:
            notification_channels: 通知渠道ID列表
            template_id: 模板ID
            notification_targets: 通知对象ID列表
            user_id: 用户ID
            
        Returns:
            验证结果字典
        """
        result = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'compatibility_info': {}
        }
        
        # 1. 获取选择的渠道类型
        if not notification_channels:
            result['errors'].append('必须选择至少一个通知渠道')
            result['valid'] = False
            return result
        
        # 查询渠道信息
        channels = NotificationChannel.query.filter(
            NotificationChannel.id.in_(notification_channels),
            NotificationChannel.user_id == user_id
        ).all()
        
        if len(channels) != len(notification_channels):
            result['errors'].append('部分通知渠道不存在或无权限访问')
            result['valid'] = False
            return result
        
        channel_types = [channel.channel_type for channel in channels]
        
        # 2. 获取兼容性信息
        compatibility_info = cls.get_multi_channel_compatibility(channel_types)
        result['compatibility_info'] = compatibility_info
        
        if not compatibility_info['compatible']:
            result['errors'].append(compatibility_info['message'])
            result['valid'] = False
            return result
        
        # 3. 验证模板配置
        if template_id:
            template = AlertTemplate.query.filter(
                (AlertTemplate.id == template_id) & 
                ((AlertTemplate.user_id == user_id) | (AlertTemplate.is_system == True))
            ).first()
            
            if not template:
                result['errors'].append('选择的模板不存在或无权限访问')
                result['valid'] = False
            else:
                # 检查模板类型是否兼容
                if compatibility_info['template_strategy'] == 'single_type':
                    if template.template_type not in compatibility_info['required_template_types']:
                        result['errors'].append(f'模板类型 "{template.template_type}" 与选择的渠道类型不匹配')
                        result['valid'] = False
                else:
                    # 多渠道需要多种模板类型
                    result['warnings'].append(f'多渠道配置建议为每种渠道类型选择对应的模板')
        
        # 4. 验证通知对象配置
        if notification_targets:
            targets = NotificationTarget.query.filter(
                NotificationTarget.id.in_(notification_targets),
                NotificationTarget.user_id == user_id
            ).all()
            
            if len(targets) != len(notification_targets):
                result['errors'].append('部分通知对象不存在或无权限访问')
                result['valid'] = False
                return result
            
            # 检查对象类型覆盖
            target_types = [target.target_type for target in targets]
            missing_types = set(compatibility_info['required_target_types']) - set(target_types)
            
            if missing_types:
                result['warnings'].append(f'缺少以下类型的通知对象: {", ".join(missing_types)}')
            
            # 检查不兼容的对象
            for target in targets:
                if target.target_type not in compatibility_info['required_target_types']:
                    result['warnings'].append(f'通知对象 "{target.name}" 的类型 "{target.target_type}" 与选择的渠道类型不匹配')
        
        return result 