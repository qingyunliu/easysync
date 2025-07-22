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
from backend.app.models import User, NotificationSetting, TaskLog, Notification, NotificationConfig
from backend.app.utils.encryption import encrypt_data, decrypt_data
from typing import Dict, Any, List
from datetime import datetime

logger = logging.getLogger(__name__)

class NotificationService:
    """通知服务类"""
    
    def __init__(self):
        self.config_file = current_app.config['NOTIFICATION_CONFIG_FILE']
        self.system_settings_file = current_app.config['SYSTEM_NOTIFICATION_SETTINGS_FILE']
        self.settings = {}
        self._load_settings()
        self.notification_types = {
            'task_started': '任务开始执行',
            'task_completed': '任务执行完成',
            'task_failed': '任务执行失败',
            'storage_mounted': '存储节点已挂载',
            'storage_unmounted': '存储节点已卸载',
            'system_error': '系统错误'
        }
    
    def _load_settings(self):
        """加载用户通知设置"""
        settings = NotificationSetting.query.all()
        for setting in settings:
            self.settings[setting.user_id] = setting
    
    def get_config(self, user_id):
        """获取用户的通知配置"""
        config = NotificationConfig.query.filter_by(user_id=user_id).first()
        if not config:
            return self._get_default_config()
        
        # 解密敏感信息
        decrypted_config = json.loads(config.config_data)
        if decrypted_config.get('emailEnabled') and 'emailPassword' in decrypted_config:
            decrypted_config['emailPassword'] = decrypt_data(decrypted_config['emailPassword'])
        if decrypted_config.get('dingtalkEnabled') and 'dingtalkSecret' in decrypted_config:
            decrypted_config['dingtalkSecret'] = decrypt_data(decrypted_config['dingtalkSecret'])
        if decrypted_config.get('webhookEnabled') and 'webhookSecret' in decrypted_config:
            decrypted_config['webhookSecret'] = decrypt_data(decrypted_config['webhookSecret'])
        if decrypted_config.get('smsEnabled') and 'smsApiKey' in decrypted_config:
            decrypted_config['smsApiKey'] = decrypt_data(decrypted_config['smsApiKey'])
        
        return decrypted_config
    
    def save_config(self, user_id, config_data):
        """保存用户的通知配置"""
        # 加密敏感信息
        encrypted_config = config_data.copy()
        if encrypted_config.get('emailEnabled') and 'emailPassword' in encrypted_config:
            encrypted_config['emailPassword'] = encrypt_data(encrypted_config['emailPassword'])
        if encrypted_config.get('dingtalkEnabled') and 'dingtalkSecret' in encrypted_config:
            encrypted_config['dingtalkSecret'] = encrypt_data(encrypted_config['dingtalkSecret'])
        if encrypted_config.get('webhookEnabled') and 'webhookSecret' in encrypted_config:
            encrypted_config['webhookSecret'] = encrypt_data(encrypted_config['webhookSecret'])
        if encrypted_config.get('smsEnabled') and 'smsApiKey' in encrypted_config:
            encrypted_config['smsApiKey'] = encrypt_data(encrypted_config['smsApiKey'])
        
        config = NotificationConfig.query.filter_by(user_id=user_id).first()
        if not config:
            config = NotificationConfig(user_id=user_id)
        
        config.config_data = json.dumps(encrypted_config)
        db.session.add(config)
        db.session.commit()
    
    def test_notification(self, user_id, config):
        """测试通知发送"""
        if config.get('emailEnabled'):
            self._send_test_email(config)
        
        if config.get('dingtalkEnabled'):
            self._send_test_dingtalk(config)
            
        if config.get('webhookEnabled'):
            self._send_test_webhook(config)
            
        if config.get('smsEnabled'):
            self._send_test_sms(config)
    
    def get_system_settings(self):
        """获取系统通知设置"""
        try:
            with open(self.system_settings_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return self._get_default_system_settings()
    
    def save_system_settings(self, settings):
        """保存系统通知设置"""
        with open(self.system_settings_file, 'w') as f:
            json.dump(settings, f, indent=2)
    
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
    
    def _send_test_email(self, config):
        """发送测试邮件"""
        msg = MIMEMultipart()
        msg['From'] = config['senderEmail']
        msg['To'] = config['receiverEmail']
        msg['Subject'] = 'EasySync 通知测试'
        
        body = '这是一封测试邮件，用于验证邮件通知配置是否正确。'
        msg.attach(MIMEText(body, 'plain'))
        
        try:
            server = smtplib.SMTP(config['smtpServer'], config['smtpPort'])
            server.starttls()
            server.login(config['senderEmail'], config['emailPassword'])
            server.send_message(msg)
            server.quit()
        except Exception as e:
            current_app.logger.error(f"发送测试邮件失败: {str(e)}")
            raise Exception("发送测试邮件失败")
    
    def _send_test_dingtalk(self, config):
        """发送测试钉钉消息"""
        webhook = config['dingtalkWebhook']
        secret = config.get('dingtalkSecret', '')
        
        timestamp = str(round(time.time() * 1000))
        string_to_sign = f"{timestamp}\n{secret}"
        hmac_code = hmac.new(
            secret.encode('utf-8'),
            string_to_sign.encode('utf-8'),
            digestmod=hashlib.sha256
        ).digest()
        sign = urllib.parse.quote_plus(base64.b64encode(hmac_code))
        
        headers = {'Content-Type': 'application/json'}
        data = {
            "msgtype": "text",
            "text": {
                "content": "这是一条测试消息，用于验证钉钉通知配置是否正确。"
            }
        }
        
        try:
            url = f"{webhook}&timestamp={timestamp}&sign={sign}"
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
        except Exception as e:
            current_app.logger.error(f"发送测试钉钉消息失败: {str(e)}")
            raise Exception("发送测试钉钉消息失败")
            
    def _send_test_webhook(self, config):
        """发送测试Webhook通知"""
        webhook_url = config['webhookUrl']
        secret = config.get('webhookSecret', '')
        
        headers = {'Content-Type': 'application/json'}
        if secret:
            timestamp = str(round(time.time() * 1000))
            string_to_sign = f"{timestamp}\n{secret}"
            hmac_code = hmac.new(
                secret.encode('utf-8'),
                string_to_sign.encode('utf-8'),
                digestmod=hashlib.sha256
            ).digest()
            sign = base64.b64encode(hmac_code).decode('utf-8')
            headers['X-Webhook-Signature'] = sign
            headers['X-Webhook-Timestamp'] = timestamp
        
        data = {
            "type": "test",
            "message": "这是一条测试消息，用于验证Webhook通知配置是否正确。",
            "timestamp": int(time.time() * 1000)
        }
        
        try:
            response = requests.post(webhook_url, headers=headers, json=data)
            response.raise_for_status()
        except Exception as e:
            current_app.logger.error(f"发送测试Webhook通知失败: {str(e)}")
            raise Exception("发送测试Webhook通知失败")
            
    def _send_test_sms(self, config):
        """发送测试短信"""
        provider = config['smsProvider']
        api_key = config['smsApiKey']
        template_id = config['smsTemplateId']
        sign_name = config['smsSignName']
        
        if provider == 'aliyun':
            self._send_aliyun_sms(
                api_key,
                template_id,
                sign_name,
                config['receiverPhone'],
                {'code': '123456'}
            )
        elif provider == 'tencent':
            self._send_tencent_sms(
                api_key,
                template_id,
                sign_name,
                config['receiverPhone'],
                {'code': '123456'}
            )
        else:
            raise ValueError(f"不支持的短信服务提供商: {provider}")
    
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
    
    def _send_email_notification(self, email: str, subject: str, content: str):
        """
        发送邮件通知
        
        Args:
            email: 收件人邮箱
            subject: 邮件主题
            content: 邮件内容
        """
        try:
            msg = MIMEMultipart()
            msg['From'] = current_app.config['MAIL_USERNAME']
            msg['To'] = email
            msg['Subject'] = subject
            
            msg.attach(MIMEText(content, 'plain'))
            
            with smtplib.SMTP(
                current_app.config['MAIL_SERVER'],
                current_app.config['MAIL_PORT']
            ) as server:
                if current_app.config['MAIL_USE_TLS']:
                    server.starttls()
                server.login(
                    current_app.config['MAIL_USERNAME'],
                    current_app.config['MAIL_PASSWORD']
                )
                server.send_message(msg)
            
            logger.info(f"已发送邮件通知: {email}")
            
        except Exception as e:
            logger.error(f"发送邮件通知失败: {str(e)}")
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
            
            # 如果配置了密钥，添加签名
            config = self.get_config(data.get('user_id'))
            if config.get('webhookEnabled') and config.get('webhookSecret'):
                secret = config['webhookSecret']
                timestamp = str(round(time.time() * 1000))
                string_to_sign = f"{timestamp}\n{secret}"
                hmac_code = hmac.new(
                    secret.encode('utf-8'),
                    string_to_sign.encode('utf-8'),
                    digestmod=hashlib.sha256
                ).digest()
                sign = base64.b64encode(hmac_code).decode('utf-8')
                headers['X-Webhook-Signature'] = sign
                headers['X-Webhook-Timestamp'] = timestamp
            
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
            
    def _send_sms_notification(self, phone: str, template_type: str, params: Dict[str, Any]):
        """
        发送短信通知
        
        Args:
            phone: 手机号码
            template_type: 模板类型
            params: 模板参数
        """
        try:
            config = self.get_config(params.get('user_id'))
            if not config.get('smsEnabled'):
                return
                
            provider = config['smsProvider']
            api_key = config['smsApiKey']
            template_id = config['smsTemplateId']
            sign_name = config['smsSignName']
            
            if provider == 'aliyun':
                self._send_aliyun_sms(api_key, template_id, sign_name, phone, params)
            elif provider == 'tencent':
                self._send_tencent_sms(api_key, template_id, sign_name, phone, params)
            else:
                raise ValueError(f"不支持的短信服务提供商: {provider}")
                
            logger.info(f"已发送短信通知: {phone}")
            
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
        
        # 发送邮件通知
        self._send_email_notification(notification)
        
        return notification
        
    def get_user_notifications(self, user_id: int, limit: int = 100) -> List[Notification]:
        """获取用户通知"""
        return Notification.query.filter_by(user_id=user_id)\
            .order_by(Notification.created_at.desc())\
            .limit(limit)\
            .all()
            
    def mark_as_read(self, notification_id: int) -> None:
        """标记通知为已读"""
        notification = Notification.query.get_or_404(notification_id)
        notification.read = True
        notification.read_at = datetime.utcnow()
        db.session.commit()
        
    def delete_notification(self, notification_id: int) -> None:
        """删除通知"""
        notification = Notification.query.get_or_404(notification_id)
        db.session.delete(notification)
        db.session.commit()
        
    def _send_email_notification(self, notification: Notification) -> None:
        """发送邮件通知"""
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