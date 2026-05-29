import json
import logging
import smtplib
import requests
import hmac
import hashlib
import base64
import time
import urllib.parse
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import current_app
from backend import db
from backend.app.models import (
    User, NotificationSetting, TaskLog, Notification, NotificationChannel, NotificationTarget, SystemSetting
)
from backend.app.utils.encryption import encrypt_data, decrypt_data
from typing import Dict, Any, List
from datetime import datetime
from sqlalchemy import and_

logger = logging.getLogger(__name__)

class NotificationService:
    """通知服务类"""
    
    def __init__(self):
        self.settings = {}
        # 延迟加载设置，避免在应用上下文外执行数据库查询
        self._settings_loaded = False
        self.notification_types = {
            # 任务相关
            'task_started': '任务开始执行',
            'task_completed': '任务执行完成',
            'task_failed': '任务执行失败',
            'task_paused': '任务已暂停',
            'task_resumed': '任务已恢复',
            'task_cancelled': '任务已取消',
            'task_retry': '任务重试执行',
            
            # 存储相关
            'storage_mounted': '存储已挂载',
            'storage_unmounted': '存储已卸载',
            'storage_connected': '存储连接成功',
            'storage_disconnected': '存储连接中断',
            'storage_error': '存储访问错误',
            'storage_quota_warning': '存储空间不足警告',
            'storage_created': '存储创建成功',
            'storage_updated': '存储配置更新',
            'storage_deleted': '存储已删除',
            
            # 节点相关
            'node_online': '节点上线',
            'node_offline': '节点离线',
            'node_connected': '节点连接成功',
            'node_disconnected': '节点连接断开',
            'node_error': '节点运行错误',
            'node_status_changed': '节点状态变更',
            'node_created': '节点创建成功',
            'node_updated': '节点配置更新',
            'node_deleted': '节点已删除',
            'node_heartbeat_timeout': '节点心跳超时',
            'node_resource_warning': '节点资源使用警告',
            
            # 客户端相关
            'client_connected': '客户端连接成功',
            'client_disconnected': '客户端连接断开',
            'client_registered': '客户端注册成功',
            'client_unregistered': '客户端注销',
            'client_error': '客户端运行错误',
            'client_status_changed': '客户端状态变更',
            'client_version_updated': '客户端版本更新',
            'client_config_updated': '客户端配置更新',
            
            # 系统相关
            'system_error': '系统错误',
            'system_warning': '系统警告',
            'system_maintenance': '系统维护',
            'system_backup_completed': '系统备份完成',
            'system_backup_failed': '系统备份失败',
            'system_update_available': '系统更新可用',
            'system_resource_warning': '系统资源警告',
            
            # 用户相关
            'user_login': '用户登录',
            'user_logout': '用户登出',
            'user_registered': '用户注册',
            'user_password_changed': '密码已修改',
            'user_profile_updated': '用户资料更新',
            'user_permission_changed': '用户权限变更',
            
            # 安全相关
            'security_login_failed': '登录失败',
            'security_suspicious_activity': '可疑活动检测',
            'security_token_expired': '访问令牌过期',
            'security_unauthorized_access': '未授权访问',
            'security_password_reset': '密码重置请求',
            
            # 数据同步相关
            'sync_started': '数据同步开始',
            'sync_completed': '数据同步完成',
            'sync_failed': '数据同步失败',
            'sync_conflict': '数据同步冲突',
            'sync_progress_update': '同步进度更新'
        }
    
    def _load_settings(self):
        """加载用户通知设置"""
        if self._settings_loaded:
            return
            
        try:
            settings = NotificationSetting.query.all()
            for setting in settings:
                self.settings[setting.user_id] = setting
            self._settings_loaded = True
        except Exception as e:
            # 如果在应用上下文外，记录警告但不抛出异常
            logger.warning(f"无法加载通知设置: {e}")
            self._settings_loaded = True  # 标记为已加载，避免重复尝试
    
    def get_user_setting(self, user_id):
        return NotificationSetting.query.filter_by(user_id=user_id).first()

    def get_channels(self, user_id: str) -> List[Dict[str, Any]]:
        """获取通知渠道列表"""
        channels = NotificationChannel.query.filter(NotificationChannel.user_id == user_id).all()
        return [channel.to_dict() for channel in channels]

    def create_channel(self, data: Dict[str, Any]) -> NotificationChannel:
        """创建通知渠道"""
        # 验证数据
        self._validate_channel_data(data)
        
        # 如果设置为默认，先取消其他默认渠道
        if data.get('is_default', False):
            NotificationChannel.query.filter(
                and_(NotificationChannel.user_id == data['user_id'], NotificationChannel.is_default == True)
            ).update({'is_default': False})
        
        # 创建新渠道
        channel = NotificationChannel(
            name=data['name'],
            channel_type=data['channel_type'],
            enabled=data.get('enabled', True),
            config=data['config'],
            retry_count=data.get('retry_count', 3),
            rate_limit=data.get('rate_limit', 100),
            timeout=data.get('timeout', 30),
            is_default=data.get('is_default', False),
            user_id=data['user_id']
        )
        
        db.session.add(channel)
        db.session.commit()
        
        logger.info(f"Notification channel created: {channel.id}")
        return channel
        
            
    def update_channel(self, channel_id: str, user_id: str, data: Dict[str, Any]) -> NotificationChannel:
        """更新通知渠道"""
        channel = NotificationChannel.query.filter(
            and_(NotificationChannel.id == channel_id, NotificationChannel.user_id == user_id)
        ).first()
        
        if not channel:
            raise ValueError("通知渠道不存在")
        
        # 更新字段
        for key, value in data.items():
            if hasattr(channel, key):
                setattr(channel, key, value)
        
        # 如果设置为默认，先取消其他默认渠道
        if data.get('is_default', False):
            NotificationChannel.query.filter(
                and_(
                    NotificationChannel.user_id == user_id,
                    NotificationChannel.is_default == True,
                    NotificationChannel.id != channel_id
                )
            ).update({'is_default': False})
        
        channel.updated_at = datetime.utcnow()
        db.session.commit()
        
        logger.info(f"Notification channel updated: {channel_id}")
        return channel
    
    def delete_channel(self, channel_id: str, user_id: str) -> None:
        """删除通知渠道"""
        channel = NotificationChannel.query.filter(
            and_(NotificationChannel.id == channel_id, NotificationChannel.user_id == user_id)
        ).first()
        
        if not channel:
            raise ValueError("通知渠道不存在")
        
        db.session.delete(channel)
        db.session.commit()
        
        logger.info(f"Notification channel deleted: {channel_id}")
    
    def get_targets(self, user_id: str) -> List[Dict[str, Any]]:
        """获取通知对象列表"""
        targets = NotificationTarget.query.filter(NotificationTarget.user_id == user_id).all()
        return [target.to_dict() for target in targets]
    
    def create_target(self, data: Dict[str, Any]) -> NotificationTarget:
        """创建通知对象"""

        self._validate_target_data(data)
        
        target = NotificationTarget(
            name=data['name'],
            enabled=data.get('enabled', True),
            description=data.get('description', ''),
            alert_policies=data.get('alert_policies', []),
            channels=data.get('channels', []),
            target_type=data['target_type'],
            target_config=data['target_config'],
            user_id=data['user_id']
        )
            
        db.session.add(target)
        db.session.commit()
        
        # 处理双向绑定：更新告警策略中的通知对象关联
        if data.get('alert_policies'):
            self._update_alert_policies_binding(target.id, data['alert_policies'], data['user_id'])
            
        logger.info(f"Notification target created: {target.id}")
        return target
            
    def update_target(self, target_id: str, user_id: str, data: Dict[str, Any]) -> NotificationTarget:
        """更新通知对象"""
        target = NotificationTarget.query.filter(
            and_(NotificationTarget.id == target_id, NotificationTarget.user_id == user_id)
        ).first()
        
        if not target:
            raise ValueError("通知对象不存在")
        
        # 更新字段
        for key, value in data.items():
            if hasattr(target, key):
                setattr(target, key, value)
        
        target.updated_at = datetime.utcnow()
        db.session.commit()
        
        # 处理双向绑定：更新告警策略中的通知对象关联
        if 'alert_policies' in data:
            self._update_alert_policies_binding(target_id, data['alert_policies'], user_id)
        
        logger.info(f"Notification target updated: {target_id}")
        return target
    
    def delete_target(self, target_id: str, user_id: str) -> None:
        """删除通知对象"""
        target = NotificationTarget.query.filter(
            and_(NotificationTarget.id == target_id, NotificationTarget.user_id == user_id)
        ).first()
        
        if not target:
            raise ValueError("通知对象不存在")
        
        db.session.delete(target)
        db.session.commit()
        
        logger.info(f"Notification target deleted: {target_id}")

    def test_notification_channel(self, channel_id: str, user_id: str) -> None:
        """测试通知渠道"""
        channel = NotificationChannel.query.filter(
            and_(NotificationChannel.id == channel_id, NotificationChannel.user_id == user_id)
        ).first()

        user_email = User.query.filter(User.id == user_id).first().email
        
        if not channel:
            raise ValueError("通知渠道不存在")
        
        if channel.channel_type == 'email':
            self._send_test_email(channel.config, 
                                  email_from=channel.config.get('username'),
                                  email_to=user_email,
                                  username=channel.config.get('username'),
                                  password=channel.config.get('password'),
                                  smtp_server=channel.config.get('smtp_server'),
                                  smtp_port=channel.config.get('smtp_port'))
        elif channel.channel_type == 'dingtalk':
            self._send_test_dingtalk(channel.config)
        elif channel.channel_type == 'webhook':
            self._send_test_webhook(channel.config)
        elif channel.channel_type == 'sms':
            self._send_test_sms(channel.config)
        
        logger.info(f"Notification channel tested: {channel_id}")
        return True
    
    def _update_alert_policies_binding(self, target_id: str, alert_policies: list, user_id: str):
        """更新告警策略与通知对象的双向绑定"""
        try:
            from backend.app.models.alert import AlertPolicy
            
            # 获取所有属于该用户的告警策略
            all_policies = AlertPolicy.query.filter_by(user_id=user_id).all()
            
            # 更新每个告警策略的通知对象关联
            for policy in all_policies:
                current_targets = policy.notification_targets or []
                
                if policy.id in alert_policies:
                    # 如果当前通知对象不在关联列表中，添加它
                    if target_id not in current_targets:
                        current_targets.append(target_id)
                else:
                    # 如果当前通知对象在关联列表中，移除它
                    if target_id in current_targets:
                        current_targets.remove(target_id)
                
                policy.notification_targets = current_targets
                policy.updated_at = datetime.utcnow()
            
            db.session.commit()
            logger.info(f"Updated alert policies binding for target: {target_id}")
            
        except Exception as e:
            logger.error(f"Error updating alert policies binding: {e}")
            # 不抛出异常，避免影响主流程
        
    def test_notification(self, user_id, type=None):
        """测试通知发送"""
        setting = self.get_user_setting(user_id)
        if not setting:
            raise Exception('未找到通知设置')
        if (type is None or type == 'email') and setting.email_enabled:
            self._send_test_email(setting)
        if (type is None or type == 'dingtalk') and setting.dingtalk_enabled:
            self._send_test_dingtalk(setting)
        if (type is None or type == 'webhook') and setting.webhook_enabled:
            self._send_test_webhook(setting)
        if (type is None or type == 'sms') and setting.sms_enabled:
            self._send_test_sms(setting)
    
    def test_notification_config(self, config, to_email=None):
        """直接用前端传递的配置内容测试指定通道，不查数据库"""
        type = config.get('type')
        if (type == 'email' and config.get('email_enabled')):
            self._send_test_email(config, to_email)
        if (type == 'dingtalk' and config.get('dingtalk_enabled')):
            self._send_test_dingtalk(config)
        if (type == 'webhook' and config.get('webhook_enabled')):
            self._send_test_webhook(config)
        if (type == 'sms' and config.get('sms_enabled')):
            self._send_test_sms(config)
    
    def get_system_settings(self):
        """获取系统通知策略（从数据库）"""
        return SystemSetting.get_json('system_notification_settings', self._get_default_system_settings())

    def save_system_settings(self, settings):
        """保存系统通知策略（到数据库）"""
        from backend import db
        import json
        s = SystemSetting.query.filter_by(key='system_notification_settings').first()
        if not s:
            s = SystemSetting(key='system_notification_settings', value=json.dumps(settings, ensure_ascii=False))
            db.session.add(s)
        else:
            s.value = json.dumps(settings, ensure_ascii=False)
        db.session.commit()
    
    def _get_default_config(self):
        """获取默认通知配置"""
        return {
            'emailEnabled': False,
            'smtpServer': '',
            'smtpPort': 587,
            'senderEmail': '',
            'emailPassword': '',
            'receiverEmail': '',
            'dingtalkEnabled': False,
            'dingtalkWebhook': '',
            'dingtalkSecret': '',
            'webhookEnabled': False,
            'webhookUrl': '',
            'webhookSecret': '',
            'smsEnabled': False,
            'smsProvider': '',
            'smsApiKey': '',
            'smsTemplateId': '',
            'smsSignName': ''
        }
    
    def _get_default_system_settings(self):
        """获取默认系统通知设置"""
        return {
            'taskCompletion': True,
            'taskFailure': True,
            'storageError': True,
            'systemError': True,
            'notificationInterval': 300  # 5分钟
        }
    
    def _send_test_email(self, email_config, email_from=None, email_to=None, username=None, 
                         password=None, smtp_server=None, smtp_port=None, to_email=None):
        """发送测试邮件，兼容 dict/config 和 ORM setting"""
        get = email_config.get if isinstance(email_config, dict) else lambda k: getattr(email_config, k, None)
        msg = MIMEMultipart()
        msg['Subject'] = 'EasySync 通知测试'
        msg['From'] = email_from or get('email')
        msg['To'] = email_to or get('email')
        body = '这是一封测试邮件，用于验证邮件通知配置是否正确。'
        msg.attach(MIMEText(body, 'plain'))
        smtp_server = smtp_server or get('smtp_host')
        smtp_port = smtp_port or get('smtp_port')
        username = username or get('smtp_username')
        password = password or get('smtp_password')
        try:
            server = smtplib.SMTP_SSL(smtp_server, smtp_port)
            server.login(username, password)
            server.send_message(msg)
            server.quit()
        except Exception as e:
            raise Exception(f"发送测试邮件失败: {str(e)}")
    
    def _send_test_dingtalk(self, setting):
        get = setting.get if isinstance(setting, dict) else lambda k: getattr(setting, k, None)
        webhook = get('dingtalk_webhook')
        secret = get('dingtalk_secret') or ''
        timestamp = str(round(time.time() * 1000))
        string_to_sign = f"{timestamp}\n{secret}"
        hmac_code = hmac.new(secret.encode('utf-8'), string_to_sign.encode('utf-8'), digestmod=hashlib.sha256).digest()
        sign = urllib.parse.quote_plus(base64.b64encode(hmac_code))
        headers = {'Content-Type': 'application/json'}
        data = {"msgtype": "text", "text": {"content": "这是一条测试消息，用于验证钉钉通知配置是否正确。"}}
        try:
            url = f"{webhook}&timestamp={timestamp}&sign={sign}"
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
        except Exception as e:
            raise Exception(f"发送测试钉钉消息失败: {str(e)}")
            
    def _send_test_webhook(self, setting):
        get = setting.get if isinstance(setting, dict) else lambda k: getattr(setting, k, None)
        webhook_url = get('webhook_url')
        secret = get('webhook_secret') or ''
        headers = {'Content-Type': 'application/json'}
        if secret:
            timestamp = str(round(time.time() * 1000))
            string_to_sign = f"{timestamp}\n{secret}"
            hmac_code = hmac.new(secret.encode('utf-8'), string_to_sign.encode('utf-8'), digestmod=hashlib.sha256).digest()
            sign = base64.b64encode(hmac_code).decode('utf-8')
            headers['X-Webhook-Signature'] = sign
            headers['X-Webhook-Timestamp'] = timestamp
        data = {"type": "test", "message": "这是一条测试消息，用于验证Webhook通知配置是否正确。", "timestamp": int(time.time() * 1000)}
        try:
            response = requests.post(webhook_url, headers=headers, json=data)
            response.raise_for_status()
        except Exception as e:
            raise Exception(f"发送测试Webhook通知失败: {str(e)}")
            
    def _send_test_sms(self, setting):
        get = setting.get if isinstance(setting, dict) else lambda k: getattr(setting, k, None)
        if not get('sms_provider') or not get('sms_api_key'):
            raise Exception('未配置短信服务商或API Key')
        if get('sms_provider') == 'aliyun':
            try:
                from aliyunsdkcore.client import AcsClient
                from aliyunsdkcore.request import CommonRequest
                access_key_id, access_key_secret = get('sms_api_key').split(',')[:2]
                client = AcsClient(access_key_id, access_key_secret, 'cn-hangzhou')
                request = CommonRequest()
                request.set_accept_format('json')
                request.set_domain('dysmsapi.aliyuncs.com')
                request.set_method('POST')
                request.set_protocol_type('https')
                request.set_version('2017-05-25')
                request.set_action_name('SendSms')
                request.add_query_param('PhoneNumbers', get('sms_sign_name'))  # 这里应为目标手机号
                request.add_query_param('SignName', get('sms_sign_name'))
                request.add_query_param('TemplateCode', get('sms_template_id'))
                request.add_query_param('TemplateParam', '{"code":"123456"}')
                response = client.do_action_with_exception(request)
                import json as _json
                resp_data = _json.loads(response)
                if resp_data.get('Code') != 'OK':
                    raise Exception(f"发送阿里云短信失败: {resp_data.get('Message')}")
            except Exception as e:
                raise Exception(f"发送阿里云短信失败: {str(e)}")
        elif get('sms_provider') == 'tencent':
            try:
                from tencentcloud.common import credential
                from tencentcloud.common.profile.client_profile import ClientProfile
                from tencentcloud.common.profile.http_profile import HttpProfile
                from tencentcloud.sms.v20210111 import sms_client, models
                access_key_id, access_key_secret, sdk_app_id = get('sms_api_key').split(',')[:3]
                cred = credential.Credential(access_key_id, access_key_secret)
                httpProfile = HttpProfile()
                httpProfile.endpoint = "sms.tencentcloudapi.com"
                clientProfile = ClientProfile()
                clientProfile.httpProfile = httpProfile
                client = sms_client.SmsClient(cred, "ap-guangzhou", clientProfile)
                req = models.SendSmsRequest()
                req.SmsSdkAppId = sdk_app_id
                req.SignName = get('sms_sign_name')
                req.TemplateId = get('sms_template_id')
                req.TemplateParamSet = ["123456"]
                req.PhoneNumberSet = [f"+86{get('sms_sign_name')}"]  # 这里应为目标手机号
                response = client.SendSms(req)
                if response.SendStatusSet[0].Code != "Ok":
                    raise Exception(f"发送腾讯云短信失败: {response.SendStatusSet[0].Message}")
            except Exception as e:
                raise Exception(f"发送腾讯云短信失败: {str(e)}")
        else:
            raise Exception('不支持的短信服务商')
    
    def notify_task_completion(self, task_log: TaskLog):
        """
        发送任务完成通知
        
        Args:
            task_log: 任务日志
        """
        try:
            # 获取任务所有者
            task = task_log.task
            user = User.query.get(task.user_id)
            
            # 获取用户通知设置
            self._load_settings()
            setting = self.settings.get(user.id)
            if not setting or not setting.enabled:
                return
            
            # 准备通知内容
            subject = f"任务执行完成: {task.name}"
            content = self._format_task_notification(task_log)
            
            # 发送通知
            if setting.email_enabled:
                self._send_email_notification(user.email, subject, content)
            
            if setting.webhook_enabled and setting.webhook_url:
                self._send_webhook_notification(setting.webhook_url, {
                    'type': 'task_completion',
                    'task_id': task.id,
                    'task_name': task.name,
                    'status': task_log.status,
                    'message': content
                })
                
            if setting.sms_enabled:
                self._send_sms_notification(
                    user.phone,
                    'task_completion',
                    {
                        'task_name': task.name,
                        'status': task_log.status,
                        'files_processed': task_log.files_processed,
                        'bytes_processed': self._format_bytes(task_log.bytes_processed)
                    }
                )
            
            logger.info(f"已发送任务完成通知: {task.id}")
            
        except Exception as e:
            logger.error(f"发送任务完成通知失败: {str(e)}")
    
    def notify_task_failure(self, task_log: TaskLog):
        """
        发送任务失败通知
        
        Args:
            task_log: 任务日志
        """
        try:
            # 获取任务所有者
            task = task_log.task
            user = User.query.get(task.user_id)
            
            # 获取用户通知设置
            self._load_settings()
            setting = self.settings.get(user.id)
            if not setting or not setting.enabled:
                return
            
            # 准备通知内容
            subject = f"任务执行失败: {task.name}"
            content = self._format_task_notification(task_log)
            
            # 发送通知
            if setting.email_enabled:
                self._send_email_notification(user.email, subject, content)
            
            if setting.webhook_enabled and setting.webhook_url:
                self._send_webhook_notification(setting.webhook_url, {
                    'type': 'task_failure',
                    'task_id': task.id,
                    'task_name': task.name,
                    'status': task_log.status,
                    'error': task_log.error_message,
                    'message': content
                })
                
            if setting.sms_enabled:
                self._send_sms_notification(
                    user.phone,
                    'task_failure',
                    {
                        'task_name': task.name,
                        'error': task_log.error_message
                    }
                )
            
            logger.info(f"已发送任务失败通知: {task.id}")
            
        except Exception as e:
            logger.error(f"发送任务失败通知失败: {str(e)}")
    
    def _format_task_notification(self, task_log: TaskLog) -> str:
        """
        格式化任务通知内容
        
        Args:
            task_log: 任务日志
            
        Returns:
            格式化后的通知内容
        """
        task = task_log.task
        content = [
            f"任务名称: {task.name}",
            f"执行状态: {task_log.status}",
            f"开始时间: {task_log.start_time}",
            f"结束时间: {task_log.end_time}",
            f"处理文件数: {task_log.files_processed}",
            f"处理字节数: {task_log.bytes_processed}"
        ]
        
        if task_log.error_message:
            content.append(f"错误信息: {task_log.error_message}")
        
        return "\n".join(content)
    
    def _send_email_notification_with_params(self, email: str, subject: str, content: str):
        """
        发送邮件通知
        
        Args:
            email: 收件人邮箱
            subject: 邮件主题
            content: 邮件内容
        """
        try:
            msg = MIMEMultipart()
            msg['From'] = current_app.config['SMTP_FROM']
            msg['To'] = email
            msg['Subject'] = subject
            
            msg.attach(MIMEText(content, 'plain'))
            
            with smtplib.SMTP(
                current_app.config['SMTP_SERVER'],
                current_app.config['SMTP_PORT']
            ) as server:
                if current_app.config['SMTP_USE_TLS']:
                    server.starttls()
                server.login(
                    current_app.config['SMTP_USER'],
                    current_app.config['SMTP_PASSWORD']
                )
                server.send_message(msg)
            
            logger.info(f"已发送邮件通知: {email}")
            
        except Exception as e:
            logger.error(f"发送邮件通知失败: {str(e)}")
            raise
    
    def _send_email_with_smtp_config(self, smtp_config: dict, email: str, subject: str, content: str):
        """
        使用指定的SMTP配置发送邮件通知
        
        Args:
            smtp_config: SMTP配置字典
            email: 收件人邮箱
            subject: 邮件主题
            content: 邮件内容
        """
        try:
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            
            smtp_server = smtp_config.get('smtp_server', 'localhost')
            smtp_port = smtp_config.get('smtp_port', 587)
            smtp_user = smtp_config.get('username', '')
            smtp_password = smtp_config.get('password', '')
            smtp_use_tls = smtp_config.get('smtp_use_tls', False)
            smtp_from = smtp_config.get('username', 'noreply@easysync.com')
            to_email = email

            msg = MIMEMultipart()
            msg['From'] = smtp_from
            msg['To'] = to_email
            msg['Subject'] = subject + ' [EasySync]_' + str(datetime.now().timestamp())
            msg.attach(MIMEText(content, 'plain'))

            if smtp_use_tls:
                with smtplib.SMTP(smtp_server, smtp_port) as server:
                    server.starttls()
                    server.login(smtp_user, smtp_password)
                    server.sendmail(smtp_from, [to_email], msg.as_string()) 
            else:
                with smtplib.SMTP_SSL(smtp_server, smtp_port) as server:
                    server.login(smtp_user, smtp_password)
                    server.sendmail(smtp_from, [to_email], msg.as_string()) 
            
            logger.info(f"已发送邮件通知: {email}")
            
        except Exception as e:
            logger.error(f"发送邮件通知失败: {e}")
            raise
    
    def _send_sms_with_config(self, sms_config: dict, phone: str, content: str):
        """
        使用指定的短信配置发送短信通知
        
        Args:
            sms_config: 短信配置字典
            phone: 手机号码
            content: 短信内容
        """
        try:
            # 这里可以根据不同的短信提供商实现
            # 目前使用默认的短信发送方法
            self._send_sms_notification({'phone': phone}, {'content': content})
            logger.info(f"已发送短信通知: {phone}")
            
        except Exception as e:
            logger.error(f"发送短信通知失败: {e}")
            raise
    
    def _send_dingtalk_with_config(self, webhook_url: str, secret: str, title: str, content: str):
        """
        使用指定的钉钉配置发送钉钉通知
        
        Args:
            webhook_url: 钉钉Webhook URL
            secret: 钉钉签名密钥
            title: 消息标题
            content: 消息内容
        """
        try:
            # 使用现有的钉钉发送方法
            self._send_dingtalk_notification({'webhook_url': webhook_url, 'secret': secret}, {'title': title, 'content': content})
            logger.info(f"已发送钉钉通知")
            
        except Exception as e:
            logger.error(f"发送钉钉通知失败: {e}")
            raise
    
    def _send_webhook_with_config(self, webhook_url: str, secret: str, content: dict):
        """
        使用指定的Webhook配置发送Webhook通知
        
        Args:
            webhook_url: Webhook URL
            secret: 签名密钥
            content: 通知内容
        """
        try:
            # 使用现有的Webhook发送方法
            self._send_webhook_notification(webhook_url, content)
            logger.info(f"已发送Webhook通知")
            
        except Exception as e:
            logger.error(f"发送Webhook通知失败: {e}")
            raise
    
    def _send_webhook_notification(self, webhook_url: str, data: Dict[str, Any]):
        """
        发送Webhook通知
        
        Args:
            webhook_url: Webhook URL
            data: 通知数据
        """
        try:
            headers = {'Content-Type': 'application/json'}
            
            response = requests.post(
                webhook_url,
                json=data,
                headers=headers
            )
            response.raise_for_status()
            
            logger.info(f"已发送Webhook通知: {webhook_url}")
            
        except Exception as e:
            logger.error(f"发送Webhook通知失败: {str(e)}")
            raise
            
    def _send_sms_notification(self, phone: str, params: Dict[str, Any]):
        """
        发送短信通知
        Args:
            phone: 手机号码
            params: 模板参数
        """
        try:
            # 获取全局短信配置（假设只用第一个管理员的 NotificationSetting，或可扩展为系统级配置）
            setting = NotificationSetting.query.first()
            if not setting or not setting.sms_enabled:
                return
            provider = setting.sms_provider
            api_key = setting.sms_api_key
            template_id = setting.sms_template_id
            sign_name = setting.sms_sign_name
            if provider == 'aliyun':
                self._send_aliyun_sms(api_key, template_id, sign_name, phone, params)
            elif provider == 'tencent':
                self._send_tencent_sms(api_key, template_id, sign_name, phone, params)
            else:
                raise ValueError(f"不支持的短信服务提供商: {provider}")
        except Exception as e:
            logger.error(f"发送短信通知失败: {str(e)}")
            raise
            
    def _send_aliyun_sms(self, api_key: str, template_id: str, sign_name: str, 
                        phone: str, params: Dict[str, Any]):
        """发送阿里云短信"""
        from aliyunsdkcore.client import AcsClient
        from aliyunsdkcore.request import CommonRequest
        
        client = AcsClient(api_key.split(',')[0], api_key.split(',')[1], 'cn-hangzhou')
        request = CommonRequest()
        request.set_accept_format('json')
        request.set_domain('dysmsapi.aliyuncs.com')
        request.set_method('POST')
        request.set_protocol_type('https')
        request.set_version('2017-05-25')
        request.set_action_name('SendSms')
        
        request.add_query_param('PhoneNumbers', phone)
        request.add_query_param('SignName', sign_name)
        request.add_query_param('TemplateCode', template_id)
        request.add_query_param('TemplateParam', json.dumps(params))
        
        response = client.do_action_with_exception(request)
        response_data = json.loads(response)
        
        if response_data['Code'] != 'OK':
            raise Exception(f"发送阿里云短信失败: {response_data['Message']}")
            
    def _send_tencent_sms(self, api_key: str, template_id: str, sign_name: str, 
                         phone: str, params: Dict[str, Any]):
        """发送腾讯云短信"""
        from tencentcloud.common import credential
        from tencentcloud.common.profile.client_profile import ClientProfile
        from tencentcloud.common.profile.http_profile import HttpProfile
        from tencentcloud.sms.v20210111 import sms_client, models
        
        cred = credential.Credential(api_key.split(',')[0], api_key.split(',')[1])
        httpProfile = HttpProfile()
        httpProfile.endpoint = "sms.tencentcloudapi.com"
        
        clientProfile = ClientProfile()
        clientProfile.httpProfile = httpProfile
        client = sms_client.SmsClient(cred, "ap-guangzhou", clientProfile)
        
        req = models.SendSmsRequest()
        req.SmsSdkAppId = api_key.split(',')[2]
        req.SignName = sign_name
        req.TemplateId = template_id
        req.TemplateParamSet = list(params.values())
        req.PhoneNumberSet = [f"+86{phone}"]
        
        response = client.SendSms(req)
        if response.SendStatusSet[0].Code != "Ok":
            raise Exception(f"发送腾讯云短信失败: {response.SendStatusSet[0].Message}")
    
    def create_notification(self, user_id: int, type: str, title: str, 
                          content: str, level: str = 'info') -> Notification:
        """创建通知"""
        notification = Notification(
            user_id=user_id,
            type=type,
            title=title,
            content=content,
            level=level,
            created_at=datetime.utcnow()
        )
        db.session.add(notification)
        db.session.commit()
        
        # 根据用户设置发送通知
        self._send_notification_by_user_settings(notification)
        
        return notification
        
    def get_user_notifications(self, user_id: int, limit: int = 100, offset: int = 0) -> List[Notification]:
        """获取用户通知"""
        return Notification.query.filter_by(user_id=user_id)\
            .order_by(Notification.created_at.desc())\
            .offset(offset)\
            .limit(limit)\
            .all()
            
    def mark_as_read(self, notification_id: int, user_id: str) -> bool:
        """标记通知为已读"""
        notification = Notification.query.get_or_404(notification_id)
        if notification.user_id != user_id:
            raise ValueError("您没有权限标记此通知为已读")
        notification.is_read = True
        db.session.commit()
        return True
    
    def mark_all_as_read(self, user_id: str) -> bool:
        """标记所有通知为已读"""
        notifications = Notification.query.filter_by(user_id=user_id).all()
        for notification in notifications:
            notification.is_read = True
        db.session.commit()
        return len(notifications)
    
    def mark_as_unread(self, notification_id: int, user_id: str) -> bool:
        """标记通知为未读"""
        notification = Notification.query.get_or_404(notification_id)
        if notification.user_id != user_id:
            raise ValueError("您没有权限标记此通知为未读")
        notification.is_read = False
        db.session.commit()
        return True
        
    def delete_notification(self, notification_id: int, user_id: str) -> bool:
        """删除通知"""
        notification = Notification.query.get_or_404(notification_id)
        if notification.user_id != user_id:
            raise ValueError("您没有权限删除此通知")
        db.session.delete(notification)
        db.session.commit()
        return True
        
    def _send_notification_by_user_settings(self, notification: Notification) -> None:
        """根据用户设置发送通知"""
        try:
            user = User.query.get(notification.user_id)
            if not user:
                return
                
            # 加载用户通知设置
            self._load_settings()
            setting = self.settings.get(user.id)
            
            if not setting or not setting.enabled:
                return
                
            # 发送邮件通知
            if setting.email_enabled and user.email:
                self._send_email_notification_with_settings(notification, setting, user.email)
                
            # 发送钉钉通知
            if setting.dingtalk_enabled and setting.dingtalk_webhook:
                self._send_dingtalk_notification_with_settings(notification, setting)
                
            # 发送Webhook通知
            if setting.webhook_enabled and setting.webhook_url:
                self._send_webhook_notification_with_settings(notification, setting)
                
            # 发送短信通知
            if setting.sms_enabled and user.phone:
                self._send_sms_notification_with_settings(notification, setting, user.phone)
                
        except Exception as e:
            logger.error(f"发送通知失败: {str(e)}")
            
    def _send_email_notification_with_settings(self, notification: Notification, setting, user_email: str) -> None:
        """使用用户设置发送邮件通知"""
        try:
            # 创建邮件
            msg = MIMEMultipart()
            msg['From'] = setting.smtp_username or 'noreply@easysync.com'
            msg['To'] = user_email
            msg['Subject'] = f'[EasySync] {notification.title}'
            
            # 邮件内容
            body = f"""
            <html>
            <body>
                <h2>{notification.title}</h2>
                <p>{notification.content}</p>
                <p>时间: {notification.created_at.strftime('%Y-%m-%d %H:%M:%S')}</p>
                <hr>
                <p>此邮件由系统自动发送，请勿回复。</p>
            </body>
            </html>
            """
            msg.attach(MIMEText(body, 'html'))
            
            # 发送邮件
            if setting.smtp_port == 465:
                server = smtplib.SMTP_SSL(setting.smtp_host, setting.smtp_port)
            else:
                server = smtplib.SMTP(setting.smtp_host, setting.smtp_port)
                server.starttls()
                
            server.login(setting.smtp_username, setting.smtp_password)
            server.send_message(msg)
            server.quit()
                
        except Exception as e:
            logger.error(f"发送邮件通知失败: {str(e)}")
            
    def _send_dingtalk_notification_with_settings(self, notification: Notification, setting) -> None:
        """使用用户设置发送钉钉通知"""
        try:
            webhook = setting.dingtalk_webhook
            secret = setting.dingtalk_secret or ''
            timestamp = str(round(time.time() * 1000))
            string_to_sign = f"{timestamp}\n{secret}"
            
            if secret:
                sign = base64.b64encode(
                    hmac.new(secret.encode('utf-8'), string_to_sign.encode('utf-8'), digestmod=hashlib.sha256).digest()
                ).decode('utf-8')
                webhook = f"{webhook}&timestamp={timestamp}&sign={urllib.parse.quote(sign)}"
            
            data = {
                "msgtype": "text",
                "text": {
                    "content": f"[EasySync] {notification.title}\n{notification.content}"
                }
            }
            
            response = requests.post(webhook, json=data, timeout=10)
            response.raise_for_status()
                
        except Exception as e:
            logger.error(f"发送钉钉通知失败: {str(e)}")
            
    def _send_webhook_notification_with_settings(self, notification: Notification, setting) -> None:
        """使用用户设置发送Webhook通知"""
        try:
            data = {
                'type': notification.type,
                'title': notification.title,
                'content': notification.content,
                'level': notification.level,
                'timestamp': notification.created_at.isoformat(),
                'user_id': notification.user_id
            }
            
            headers = {'Content-Type': 'application/json'}
            if setting.webhook_secret:
                # 可以添加签名验证
                pass
                
            response = requests.post(setting.webhook_url, json=data, headers=headers, timeout=10)
            response.raise_for_status()
                
        except Exception as e:
            logger.error(f"发送Webhook通知失败: {str(e)}")
            
    def _send_sms_notification_with_settings(self, notification: Notification, setting, user_phone: str) -> None:
        """使用用户设置发送短信通知"""
        try:
            params = {
                'title': notification.title,
                'content': notification.content,
                'level': notification.level
            }
            
            if setting.sms_provider == 'aliyun':
                self._send_aliyun_sms(
                    setting.sms_api_key,
                    setting.sms_template_id,
                    setting.sms_sign_name,
                    user_phone,
                    params
                )
            elif setting.sms_provider == 'tencent':
                self._send_tencent_sms(
                    setting.sms_api_key,
                    setting.sms_template_id,
                    setting.sms_sign_name,
                    user_phone,
                    params
                )
                
        except Exception as e:
            logger.error(f"发送短信通知失败: {str(e)}")
            
    def _send_email_notification(self, notification: Notification) -> None:
        """发送邮件通知（兼容旧版本）"""
        try:
            user = User.query.get(notification.user_id)
            if not user or not user.email:
                return
                
            # 创建邮件
            msg = MIMEMultipart()
            msg['From'] = 'noreply@easysync.com'
            msg['To'] = user.email
            msg['Subject'] = f'[EasySync] {notification.title}'
            
            # 邮件内容
            body = f"""
            <html>
            <body>
                <h2>{notification.title}</h2>
                <p>{notification.content}</p>
                <p>时间: {notification.created_at.strftime('%Y-%m-%d %H:%M:%S')}</p>
                <hr>
                <p>此邮件由系统自动发送，请勿回复。</p>
            </body>
            </html>
            """
            msg.attach(MIMEText(body, 'html'))
            
            # 发送邮件
            with smtplib.SMTP('smtp.example.com', 587) as server:
                server.starttls()
                server.login('noreply@easysync.com', 'your-password')
                server.send_message(msg)
                
        except Exception as e:
            logger.error(f"发送邮件通知失败: {str(e)}")
            
    def notify_task_started(self, user_id: int, task_name: str) -> None:
        """通知任务开始执行"""
        self.create_notification(
            user_id=user_id,
            type='task_started',
            title=f'任务开始执行: {task_name}',
            content=f'同步任务 {task_name} 已开始执行。',
            level='info'
        )
        
    def notify_task_completed(self, user_id: int, task_name: str, 
                            files_processed: int, bytes_processed: int) -> None:
        """通知任务执行完成"""
        self.create_notification(
            user_id=user_id,
            type='task_completed',
            title=f'任务执行完成: {task_name}',
            content=f'同步任务 {task_name} 已执行完成。\n'
                   f'处理文件数: {files_processed}\n'
                   f'处理数据量: {self._format_bytes(bytes_processed)}',
            level='success'
        )
        
    def notify_task_failed(self, user_id: int, task_name: str, error: str) -> None:
        """通知任务执行失败"""
        self.create_notification(
            user_id=user_id,
            type='task_failed',
            title=f'任务执行失败: {task_name}',
            content=f'同步任务 {task_name} 执行失败。\n错误信息: {error}',
            level='error'
        )
        
    def _format_bytes(self, bytes: int) -> str:
        """格式化字节大小"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes < 1024:
                return f"{bytes:.2f} {unit}"
            bytes /= 1024
        return f"{bytes:.2f} PB"
    
    def notify_node_online(self, user_id: int, node_name: str, node_ip: str = None) -> None:
        """通知节点上线"""
        content = f'节点 {node_name} 已成功上线。'
        if node_ip:
            content += f'\nIP地址: {node_ip}'
        
        self.create_notification(
            user_id=user_id,
            type='node_online',
            title=f'节点上线: {node_name}',
            content=content,
            level='success'
        )
    
    def notify_node_offline(self, user_id: int, node_name: str, reason: str = None) -> None:
        """通知节点离线"""
        content = f'节点 {node_name} 已离线。'
        if reason:
            content += f'\n原因: {reason}'
        
        self.create_notification(
            user_id=user_id,
            type='node_offline',
            title=f'节点离线: {node_name}',
            content=content,
            level='warning'
        )
    
    def notify_node_error(self, user_id: int, node_name: str, error_message: str) -> None:
        """通知节点错误"""
        self.create_notification(
            user_id=user_id,
            type='node_error',
            title=f'节点错误: {node_name}',
            content=f'节点 {node_name} 发生错误。\n错误信息: {error_message}',
            level='error'
        )
    
    def notify_node_heartbeat_timeout(self, user_id: int, node_name: str, last_heartbeat: str) -> None:
        """通知节点心跳超时"""
        self.create_notification(
            user_id=user_id,
            type='node_heartbeat_timeout',
            title=f'节点心跳超时: {node_name}',
            content=f'节点 {node_name} 心跳超时，可能已断开连接。\n最后心跳时间: {last_heartbeat}',
            level='warning'
        )
    
    def notify_node_resource_warning(self, user_id: int, node_name: str, resource_type: str, usage: float) -> None:
        """通知节点资源使用警告"""
        self.create_notification(
            user_id=user_id,
            type='node_resource_warning',
            title=f'节点资源警告: {node_name}',
            content=f'节点 {node_name} 的{resource_type}使用率已达到 {usage:.1f}%，请及时处理。',
            level='warning'
        )
    
    def notify_storage_connected(self, user_id: int, storage_name: str, storage_type: str) -> None:
        """通知存储连接成功"""
        self.create_notification(
            user_id=user_id,
            type='storage_connected',
            title=f'存储连接成功: {storage_name}',
            content=f'{storage_type}存储 {storage_name} 连接成功，可以正常使用。',
            level='success'
        )
    
    def notify_storage_disconnected(self, user_id: int, storage_name: str, reason: str = None) -> None:
        """通知存储连接中断"""
        content = f'存储 {storage_name} 连接中断。'
        if reason:
            content += f'\n原因: {reason}'
        
        self.create_notification(
            user_id=user_id,
            type='storage_disconnected',
            title=f'存储连接中断: {storage_name}',
            content=content,
            level='error'
        )
    
    def notify_storage_error(self, user_id: int, storage_name: str, error_message: str) -> None:
        """通知存储访问错误"""
        self.create_notification(
            user_id=user_id,
            type='storage_error',
            title=f'存储访问错误: {storage_name}',
            content=f'访问存储 {storage_name} 时发生错误。\n错误信息: {error_message}',
            level='error'
        )
    
    def notify_storage_quota_warning(self, user_id: int, storage_name: str, used_space: int, total_space: int) -> None:
        """通知存储空间不足"""
        usage_percent = (used_space / total_space) * 100 if total_space > 0 else 0
        
        self.create_notification(
            user_id=user_id,
            type='storage_quota_warning',
            title=f'存储空间不足: {storage_name}',
            content=f'存储 {storage_name} 空间使用率已达到 {usage_percent:.1f}%。\n'
                   f'已用空间: {self._format_bytes(used_space)}\n'
                   f'总空间: {self._format_bytes(total_space)}',
            level='warning'
        )
    
    def notify_storage_created(self, user_id: int, storage_name: str, storage_type: str) -> None:
        """通知存储创建成功"""
        self.create_notification(
            user_id=user_id,
            type='storage_created',
            title=f'存储创建成功: {storage_name}',
            content=f'{storage_type}存储 {storage_name} 已成功创建并配置。',
            level='success'
        )
    
    def notify_storage_deleted(self, user_id: int, storage_name: str, storage_type: str) -> None:
        """通知存储删除"""
        self.create_notification(
            user_id=user_id,
            type='storage_deleted',
            title=f'存储已删除: {storage_name}',
            content=f'{storage_type}存储 {storage_name} 已被删除，相关数据已清理。',
            level='info'
        )
    
    def notify_storage_updated(self, user_id: int, storage_name: str, storage_type: str) -> None:
        """通知存储更新"""
        self.create_notification(
            user_id=user_id,
            type='storage_updated',
            title=f'存储更新: {storage_name}',
            content=f'{storage_type}存储 {storage_name} 已更新，相关配置已保存。',
            level='info'
        )

    def notify_client_connected(self, user_id: int, client_name: str, client_ip: str = None) -> None:
        """通知客户端连接成功"""
        content = f'客户端 {client_name} 已成功连接。'
        if client_ip:
            content += f'\nIP地址: {client_ip}'
        
        self.create_notification(
            user_id=user_id,
            type='client_connected',
            title=f'客户端连接: {client_name}',
            content=content,
            level='success'
        )
    
    def notify_client_disconnected(self, user_id: int, client_name: str, reason: str = None) -> None:
        """通知客户端断开连接"""
        content = f'客户端 {client_name} 已断开连接。'
        if reason:
            content += f'\n原因: {reason}'
        
        self.create_notification(
            user_id=user_id,
            type='client_disconnected',
            title=f'客户端断开: {client_name}',
            content=content,
            level='warning'
        )
    
    def notify_client_registered(self, user_id: int, client_name: str, version: str = None) -> None:
        """通知客户端注册成功"""
        content = f'客户端 {client_name} 已成功注册。'
        if version:
            content += f'\n版本: {version}'
        
        self.create_notification(
            user_id=user_id,
            type='client_registered',
            title=f'客户端注册: {client_name}',
            content=content,
            level='success'
        )
    
    def notify_client_error(self, user_id: int, client_name: str, error_message: str) -> None:
        """通知客户端运行错误"""
        self.create_notification(
            user_id=user_id,
            type='client_error',
            title=f'客户端错误: {client_name}',
            content=f'客户端 {client_name} 运行异常。\n错误信息: {error_message}',
            level='error'
        )
    
    def notify_client_version_updated(self, user_id: int, client_name: str, old_version: str, new_version: str) -> None:
        """通知客户端版本更新"""
        self.create_notification(
            user_id=user_id,
            type='client_version_updated',
            title=f'客户端版本更新: {client_name}',
            content=f'客户端 {client_name} 版本已更新。\n旧版本: {old_version}\n新版本: {new_version}',
            level='info'
        )
    
    def notify_task_paused(self, user_id: int, task_name: str, reason: str = None) -> None:
        """通知任务暂停"""
        content = f'同步任务 {task_name} 已暂停。'
        if reason:
            content += f'\n原因: {reason}'
        
        self.create_notification(
            user_id=user_id,
            type='task_paused',
            title=f'任务已暂停: {task_name}',
            content=content,
            level='warning'
        )
    
    def notify_task_resumed(self, user_id: int, task_name: str) -> None:
        """通知任务恢复"""
        self.create_notification(
            user_id=user_id,
            type='task_resumed',
            title=f'任务已恢复: {task_name}',
            content=f'同步任务 {task_name} 已恢复执行。',
            level='info'
        )

    def notify_task_stopped(self, user_id: int, task_name: str, reason: str = None) -> None:
        """通知任务停止"""
        content = f'同步任务 {task_name} 已停止。'
        if reason:
            content += f'\n原因: {reason}'

        self.create_notification(
            user_id=user_id,
            type='task_stopped',
            title=f'任务已停止: {task_name}',
            content=content,
            level='warning'
        )

    def notify_task_cancelled(self, user_id: int, task_name: str, reason: str = None) -> None:
        """通知任务取消"""
        content = f'同步任务 {task_name} 已被取消。'
        if reason:
            content += f'\n原因: {reason}'
        
        self.create_notification(
            user_id=user_id,
            type='task_cancelled',
            title=f'任务已取消: {task_name}',
            content=content,
            level='warning'
        )
    
    def notify_task_retry(self, user_id: int, task_name: str, retry_count: int, max_retries: int) -> None:
        """通知任务重试"""
        self.create_notification(
            user_id=user_id,
            type='task_retry',
            title=f'任务重试执行: {task_name}',
            content=f'同步任务 {task_name} 正在进行第 {retry_count} 次重试（最多 {max_retries} 次）。',
            level='info'
        )
    
    def notify_system_error(self, user_id: int, component: str, error_message: str) -> None:
        """通知系统错误"""
        self.create_notification(
            user_id=user_id,
            type='system_error',
            title=f'系统错误: {component}',
            content=f'系统组件 {component} 发生错误。\n错误信息: {error_message}',
            level='error'
        )
    
    def notify_system_warning(self, user_id: int, component: str, warning_message: str) -> None:
        """通知系统警告"""
        self.create_notification(
            user_id=user_id,
            type='system_warning',
            title=f'系统警告: {component}',
            content=f'系统组件 {component} 发出警告。\n警告信息: {warning_message}',
            level='warning'
        )
    
    def notify_system_backup_completed(self, user_id: int, backup_size: int, backup_path: str) -> None:
        """通知系统备份完成"""
        self.create_notification(
            user_id=user_id,
            type='system_backup_completed',
            title='系统备份完成',
            content=f'系统备份已成功完成。\n备份大小: {self._format_bytes(backup_size)}\n备份路径: {backup_path}',
            level='success'
        )
    
    def notify_system_backup_failed(self, user_id: int, error_message: str) -> None:
        """通知系统备份失败"""
        self.create_notification(
            user_id=user_id,
            type='system_backup_failed',
            title='系统备份失败',
            content=f'系统备份执行失败。\n错误信息: {error_message}',
            level='error'
        )
    
    def notify_system_resource_warning(self, user_id: int, resource_type: str, usage: float, threshold: float) -> None:
        """通知系统资源警告"""
        self.create_notification(
            user_id=user_id,
            type='system_resource_warning',
            title=f'系统资源警告: {resource_type}',
            content=f'系统{resource_type}使用率已达到 {usage:.1f}%，超过阈值 {threshold:.1f}%。',
            level='warning'
        )
    
    def notify_security_login_failed(self, user_id: int, ip_address: str, attempts: int) -> None:
        """通知登录失败"""
        self.create_notification(
            user_id=user_id,
            type='security_login_failed',
            title='登录失败警告',
            content=f'检测到来自 {ip_address} 的多次登录失败尝试（{attempts} 次）。',
            level='warning'
        )
    
    def notify_security_suspicious_activity(self, user_id: int, activity: str, ip_address: str) -> None:
        """通知可疑活动"""
        self.create_notification(
            user_id=user_id,
            type='security_suspicious_activity',
            title='可疑活动检测',
            content=f'检测到可疑活动: {activity}\nIP地址: {ip_address}',
            level='error'
        )
    
    def notify_security_unauthorized_access(self, user_id: int, resource: str, ip_address: str) -> None:
        """通知未授权访问"""
        self.create_notification(
            user_id=user_id,
            type='security_unauthorized_access',
            title='未授权访问警告',
            content=f'检测到未授权访问尝试。\n目标资源: {resource}\nIP地址: {ip_address}',
            level='error'
        )
    
    def notify_sync_started(self, user_id: int, source: str, destination: str) -> None:
        """通知数据同步开始"""
        self.create_notification(
            user_id=user_id,
            type='sync_started',
            title='数据同步开始',
            content=f'数据同步已开始。\n源: {source}\n目标: {destination}',
            level='info'
        )
    
    def notify_sync_completed(self, user_id: int, source: str, destination: str, 
                            files_synced: int, data_size: int, duration: int) -> None:
        """通知数据同步完成"""
        self.create_notification(
            user_id=user_id,
            type='sync_completed',
            title='数据同步完成',
            content=f'数据同步已成功完成。\n'
                   f'源: {source}\n目标: {destination}\n'
                   f'同步文件数: {files_synced}\n'
                   f'数据大小: {self._format_bytes(data_size)}\n'
                   f'耗时: {duration} 秒',
            level='success'
        )
    
    def notify_sync_failed(self, user_id: int, source: str, destination: str, error_message: str) -> None:
        """通知数据同步失败"""
        self.create_notification(
            user_id=user_id,
            type='sync_failed',
            title='数据同步失败',
            content=f'数据同步执行失败。\n'
                   f'源: {source}\n目标: {destination}\n'
                   f'错误信息: {error_message}',
            level='error'
        )
    
    def notify_sync_conflict(self, user_id: int, file_path: str, conflict_type: str) -> None:
        """通知数据同步冲突"""
        self.create_notification(
            user_id=user_id,
            type='sync_conflict',
            title='数据同步冲突',
            content=f'文件同步过程中发生冲突。\n文件路径: {file_path}\n冲突类型: {conflict_type}',
            level='warning'
        )
    
    def send_notification(self, level: str, title: str, content: str, 
                         user_id: int = None, metadata: Dict[str, Any] = None) -> None:
        """发送通用通知
        
        Args:
            level: 通知级别 (info, success, warning, error)
            title: 通知标题
            content: 通知内容
            user_id: 用户ID（可选，默认发送给所有管理员）
            metadata: 额外的元数据
        """
        try:
            # 检查用户通知策略配置
            if user_id and not self._should_send_notification(user_id, level, metadata):
                logger.info(f"Notification filtered by user policy: user_id={user_id}, level={level}")
                return
            
            # 如果没有指定用户ID，发送给所有管理员
            if user_id is None:
                self.notify_all_admins(
                    notification_type='system_notification',
                    title=title,
                    content=content,
                    level=level
                )
            else:
                # 发送给指定用户
                notification = Notification(
                    user_id=user_id,
                    type='general_notification',
                    title=title,
                    content=content,
                    level=level,
                    metadata=metadata or {},
                    created_at=datetime.utcnow()
                )
                db.session.add(notification)
                db.session.commit()
                
                # 检查是否需要发送外部通知（邮件、webhook等）
                self._send_external_notifications(user_id, notification, metadata)
                
                # 记录日志
                logger.info(f"Notification sent to user {user_id}: {title}")
                
        except Exception as e:
            logger.error(f"Failed to send notification: {str(e)}")
    
    def _should_send_notification(self, user_id: int, level: str, metadata: Dict[str, Any] = None) -> bool:
        """检查是否应该发送通知"""
        try:
            # 获取用户通知设置
            setting = NotificationSetting.query.filter_by(user_id=user_id).first()
            if not setting or not setting.enabled:
                return False
            
            # 检查通知策略配置
            policies = setting.notification_policies or {}
            
            # 根据元数据确定通知类型
            notification_type = self._determine_notification_type(metadata)
            
            # 检查该类型的通知是否启用
            if notification_type in policies:
                policy = policies[notification_type]
                
                # 检查是否启用
                if not policy.get('enabled', True):
                    return False
                
                # 检查严重级别
                allowed_severities = policy.get('severity', ['info', 'success', 'warning', 'error'])
                if level not in allowed_severities:
                    return False
            
            # 检查免打扰时间
            if self._is_in_quiet_hours(setting):
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking notification policy: {str(e)}")
            return True  # 默认发送
    
    def _determine_notification_type(self, metadata: Dict[str, Any] = None) -> str:
        """根据元数据确定通知类型"""
        if not metadata:
            return 'general'
        
        # 根据元数据中的信息判断通知类型
        if 'task_id' in metadata or 'task_name' in metadata:
            return 'task_completion'
        elif 'storage_id' in metadata or 'storage_name' in metadata:
            return 'storage_error'
        elif 'node_id' in metadata or 'node_name' in metadata:
            return 'node_status'
        elif 'client_id' in metadata or 'client_name' in metadata:
            return 'client_status'
        elif 'error' in metadata or 'alert_id' in metadata:
            return 'system_alert'
        else:
            return 'general'
    
    def _is_in_quiet_hours(self, setting: NotificationSetting) -> bool:
        """检查是否在免打扰时间内"""
        try:
            quiet_hours = setting.quiet_hours or {}
            if not quiet_hours.get('enabled', False):
                return False
            
            from datetime import datetime, timezone
            import pytz
            
            # 获取时区
            tz_name = quiet_hours.get('timezone', 'Asia/Shanghai')
            tz = pytz.timezone(tz_name)
            
            # 获取当前时间
            now = datetime.now(tz)
            current_time = now.time()
            current_weekday = now.weekday()  # 0=Monday, 6=Sunday
            
            # 检查是否仅在周末生效
            if quiet_hours.get('weekends_only', False):
                if current_weekday < 5:  # Monday-Friday
                    return False
            
            # 检查时间范围
            start_time_str = quiet_hours.get('start_time', '22:00')
            end_time_str = quiet_hours.get('end_time', '08:00')
            
            start_time = datetime.strptime(start_time_str, '%H:%M').time()
            end_time = datetime.strptime(end_time_str, '%H:%M').time()
            
            if start_time <= end_time:
                # 同一天内的时间范围
                return start_time <= current_time <= end_time
            else:
                # 跨天的时间范围
                return current_time >= start_time or current_time <= end_time
                
        except Exception as e:
            logger.error(f"Error checking quiet hours: {str(e)}")
            return False
    
    def _send_external_notifications(self, user_id: int, notification: Notification, metadata: Dict[str, Any] = None):
        """发送外部通知（邮件、webhook等）"""
        try:
            setting = NotificationSetting.query.filter_by(user_id=user_id).first()
            if not setting:
                return
            
            # 确定需要发送的渠道
            notification_type = self._determine_notification_type(metadata)
            policies = setting.notification_policies or {}
            
            channels = []
            if notification_type in policies:
                channels = policies[notification_type].get('channels', [])
            
            # 如果没有配置策略，使用默认渠道配置
            if not channels:
                if setting.email_enabled:
                    channels.append('email')
                if setting.webhook_enabled:
                    channels.append('webhook')
                if setting.dingtalk_enabled:
                    channels.append('dingtalk')
                if setting.sms_enabled:
                    channels.append('sms')
            
            # 发送通知
            for channel in channels:
                try:
                    if channel == 'email' and setting.email_enabled:
                        self._send_email_notification_external(setting, notification)
                    elif channel == 'webhook' and setting.webhook_enabled:
                        self._send_webhook_notification_external(setting, notification)
                    elif channel == 'dingtalk' and setting.dingtalk_enabled:
                        self._send_dingtalk_notification_external(setting, notification)
                    elif channel == 'sms' and setting.sms_enabled:
                        self._send_sms_notification_external(setting, notification)
                except Exception as e:
                    logger.error(f"Failed to send {channel} notification: {str(e)}")
                    
        except Exception as e:
            logger.error(f"Failed to send external notifications: {str(e)}")
    
    def _send_email_notification_external(self, setting: NotificationSetting, notification: Notification):
        """发送外部邮件通知"""
        try:
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            
            msg = MIMEMultipart()
            msg['From'] = setting.smtp_username
            msg['To'] = setting.email
            msg['Subject'] = f'[EasySync] {notification.title}'
            
            # 邮件内容
            body = f"""
            <html>
            <body>
                <h2>{notification.title}</h2>
                <p>{notification.content}</p>
                <p><strong>级别:</strong> {notification.level}</p>
                <p><strong>时间:</strong> {notification.created_at.strftime('%Y-%m-%d %H:%M:%S')}</p>
                <hr>
                <p>此邮件由 EasySync 系统自动发送，请勿回复。</p>
            </body>
            </html>
            """
            msg.attach(MIMEText(body, 'html'))
            
            # 发送邮件
            with smtplib.SMTP(setting.smtp_host, setting.smtp_port) as server:
                if setting.smtp_port == 587:
                    server.starttls()
                server.login(setting.smtp_username, setting.smtp_password)
                server.send_message(msg)
                
            logger.info(f"Email notification sent to {setting.email}")
            
        except Exception as e:
            logger.error(f"Failed to send email notification: {str(e)}")
            raise
    
    def _send_webhook_notification_external(self, setting: NotificationSetting, notification: Notification):
        """发送外部Webhook通知"""
        try:
            import requests
            import hmac
            import hashlib
            import time
            
            # 准备数据
            data = {
                'id': notification.id,
                'title': notification.title,
                'content': notification.content,
                'level': notification.level,
                'type': notification.type,
                'user_id': notification.user_id,
                'timestamp': notification.created_at.isoformat(),
                'metadata': notification.metadata or {}
            }
            
            headers = {'Content-Type': 'application/json'}
            
            # 如果配置了密钥，添加签名
            if setting.webhook_secret:
                timestamp = str(int(time.time()))
                payload = f"{timestamp}\n{setting.webhook_secret}"
                signature = hmac.new(
                    setting.webhook_secret.encode(),
                    payload.encode(),
                    hashlib.sha256
                ).hexdigest()
                
                headers['X-Webhook-Signature'] = signature
                headers['X-Webhook-Timestamp'] = timestamp
            
            # 发送请求
            response = requests.post(
                setting.webhook_url,
                json=data,
                headers=headers,
                timeout=30
            )
            response.raise_for_status()
            
            logger.info(f"Webhook notification sent to {setting.webhook_url}")
            
        except Exception as e:
            logger.error(f"Failed to send webhook notification: {str(e)}")
            raise
    
    def notify_all_admins(self, notification_type: str, title: str, content: str, level: str = 'info') -> None:
        """向所有管理员发送通知"""
        from backend.app.models.user import User
        
        admin_users = User.query.filter_by(is_admin=True).all()
        for admin in admin_users:
            self.create_notification(
                user_id=admin.id,
                type=notification_type,
                title=title,
                content=content,
                level=level
            )
    
    def notify_users_by_role(self, role: str, notification_type: str, title: str, content: str, level: str = 'info') -> None:
        """向特定角色的用户发送通知"""
        from backend.app.models.user import User
        
        users = User.query.filter_by(role=role).all()
        for user in users:
            self.create_notification(
                user_id=user.id,
                type=notification_type,
                title=title,
                content=content,
                level=level
            )
    
    def create_notification_from_event(self, event):
        """从事件创建用户友好的通知"""
        try:
            # 事件到通知的映射
            notification_mapping = {
                'storage_connect_failed': {
                    'title': '存储连接失败',
                    'content': '您的存储设备连接失败，请检查网络连接和配置',
                    'level': 'error'
                },
                'storage_sync_error': {
                    'title': '同步错误',
                    'content': '数据同步过程中发生错误，请检查存储配置和网络状态',
                    'level': 'error'
                },
                'storage_disk_full': {
                    'title': '磁盘空间不足',
                    'content': '存储设备磁盘空间不足，请清理空间或扩容',
                    'level': 'warning'
                },
                'storage_sync_complete': {
                    'title': '同步完成',
                    'content': '数据同步任务已完成',
                    'level': 'success'
                },
                'client_offline': {
                    'title': '客户端离线',
                    'content': '检测到客户端离线，请检查网络连接',
                    'level': 'warning'
                },
                'client_error': {
                    'title': '客户端错误',
                    'content': '客户端发生错误，请检查客户端状态',
                    'level': 'error'
                },
                'agent_task_error': {
                    'title': '任务执行错误',
                    'content': '任务执行过程中发生错误，请检查任务配置',
                    'level': 'error'
                },
                'agent_service_down': {
                    'title': '代理服务异常',
                    'content': '代理服务异常，请检查代理节点状态',
                    'level': 'error'
                },
                'agent_task_complete': {
                    'title': '任务完成',
                    'content': '任务执行完成',
                    'level': 'success'
                },
                'system_resource_high': {
                    'title': '系统资源告警',
                    'content': '系统资源使用率较高，建议检查系统状态',
                    'level': 'warning'
                },
                'system_network_error': {
                    'title': '网络错误',
                    'content': '检测到网络连接异常，请检查网络配置',
                    'level': 'error'
                },
                'system_security_alert': {
                    'title': '安全告警',
                    'content': '检测到安全相关事件，请及时处理',
                    'level': 'warning'
                }
            }
            
            event_key = f"{event.event_type}_{event.event_action}"
            if event_key in notification_mapping:
                mapping = notification_mapping[event_key]
                
                # 创建通知
                notification = self.create_notification(
                    user_id=event.user_id,
                    type='system_alert',
                    title=mapping['title'],
                    content=mapping['content'],
                    level=mapping['level']
                )
                
                logger.info(f"Notification created from event: {event_key}")
                return notification
            
            return None
            
        except Exception as e:
            logger.error(f"Error creating notification from event: {e}")
            return None

    def _validate_policy_data(self, data: Dict[str, Any]) -> None:
        """验证告警策略数据"""
        required_fields = ['name', 'policy_type', 'user_id']
        for field in required_fields:
            if field not in data or not data[field]:
                raise ValueError(f"缺少必填字段: {field}")
        
        if data['policy_type'] == 'resource':
            if not data.get('resource_type'):
                raise ValueError("资源告警必须指定资源类型")
            if not data.get('alert_items'):
                raise ValueError("资源告警必须指定报警条目")
            if not data.get('trigger_rules'):
                raise ValueError("资源告警必须指定触发规则")
        elif data['policy_type'] == 'event':
            if not data.get('event_type'):
                raise ValueError("事件告警必须指定事件类型")
            if not data.get('event_actions'):
                raise ValueError("事件告警必须指定事件动作")
            if not data.get('event_results'):
                raise ValueError("事件告警必须指定事件结果")
    
    def _validate_channel_data(self, data: Dict[str, Any]) -> None:
        """验证通知渠道数据"""
        required_fields = ['name', 'channel_type', 'config', 'user_id']
        for field in required_fields:
            if field not in data or not data[field]:
                raise ValueError(f"缺少必填字段: {field}")
        
        # 验证渠道配置
        channel_type = data['channel_type']
        config = data['config']
        
        if channel_type == 'email':
            if not config.get('smtp_server') or not config.get('smtp_port'):
                raise ValueError("邮件渠道必须配置SMTP服务器")
            if not config.get('username') or not config.get('password'):
                raise ValueError("邮件渠道必须配置用户名和密码")
        elif channel_type == 'sms':
            if not config.get('api_key') or not config.get('secret'):
                raise ValueError("短信渠道必须配置API密钥")
        elif channel_type == 'webhook':
            if not config.get('url'):
                raise ValueError("WebHook渠道必须配置URL")
        elif channel_type in ['dingtalk', 'slack']:
            if not config.get('webhook_url'):
                raise ValueError(f"{channel_type}渠道必须配置WebHook URL")
    
    def _validate_target_data(self, data: Dict[str, Any]) -> None:
        """验证通知对象数据"""
        required_fields = ['name', 'target_type', 'target_config', 'user_id']
        for field in required_fields:
            if field not in data or not data[field]:
                raise ValueError(f"缺少必填字段: {field}")
        
        # 验证目标配置
        target_type = data['target_type']
        config = data['target_config']
        
        if target_type == 'email':
            if not config.get('email'):
                raise ValueError("邮件通知对象必须配置邮箱地址")
        elif target_type == 'sms':
            if not config.get('phone'):
                raise ValueError("短信通知对象必须配置手机号码")
        elif target_type == 'webhook':
            if not config.get('url'):
                raise ValueError("WebHook通知对象必须配置URL")