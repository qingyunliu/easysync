<template>
  <div class="settings-container">
    <div class="header">
      <h2>系统设置</h2>
    </div>
    
    <el-tabs v-model="activeTab">
      <el-tab-pane label="基本设置" name="basic">
        <el-card class="settings-card">
          <template #header>
            <div class="card-header">
              <span>基本设置</span>
            </div>
          </template>
          
          <el-form
            ref="basicFormRef"
            :model="basicForm"
            :rules="basicRules"
            label-width="180px"
          >
            <el-form-item label="最大并发任务数" prop="max_concurrent_tasks">
              <el-input-number
                v-model="basicForm.max_concurrent_tasks"
                :min="1"
                :max="20"
              />
              <div class="form-tip">同时运行的最大任务数量</div>
            </el-form-item>
            
            <el-form-item label="默认重试次数" prop="default_retry_count">
              <el-input-number
                v-model="basicForm.default_retry_count"
                :min="0"
                :max="10"
              />
              <div class="form-tip">任务失败时的默认重试次数</div>
            </el-form-item>
            
            <el-form-item label="默认重试延迟(秒)" prop="default_retry_delay">
              <el-input-number
                v-model="basicForm.default_retry_delay"
                :min="1"
                :max="3600"
              />
              <div class="form-tip">任务失败后的重试等待时间(秒)</div>
            </el-form-item>
            
            <el-form-item label="启用通知" prop="notification_enabled">
              <el-switch v-model="basicForm.notification_enabled" />
              <div class="form-tip">是否启用系统通知功能</div>
            </el-form-item>
            
            <el-form-item>
              <el-button type="primary" @click="saveBasicSettings">保存设置</el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-tab-pane>
      
      <el-tab-pane label="日志设置" name="logs">
        <el-card class="settings-card">
          <template #header>
            <div class="card-header">
              <span>日志设置</span>
            </div>
          </template>
          
          <el-form
            ref="logsFormRef"
            :model="logsForm"
            :rules="logsRules"
            label-width="180px"
          >
            <el-form-item label="日志保留天数" prop="log_retention_days">
              <el-input-number
                v-model="logsForm.log_retention_days"
                :min="1"
                :max="365"
              />
              <div class="form-tip">系统日志保留的天数，超过此天数的日志将被自动删除</div>
            </el-form-item>
            
            <el-form-item label="日志级别" prop="log_level">
              <el-select v-model="logsForm.log_level">
                <el-option label="DEBUG" value="DEBUG" />
                <el-option label="INFO" value="INFO" />
                <el-option label="WARNING" value="WARNING" />
                <el-option label="ERROR" value="ERROR" />
                <el-option label="CRITICAL" value="CRITICAL" />
              </el-select>
              <div class="form-tip">系统日志记录的最低级别</div>
            </el-form-item>
            
            <el-form-item label="日志文件路径" prop="log_file_path">
              <el-input v-model="logsForm.log_file_path" />
              <div class="form-tip">系统日志文件的存储路径</div>
            </el-form-item>
            
            <el-form-item>
              <el-button type="primary" @click="saveLogsSettings">保存设置</el-button>
              <el-button @click="clearLogs">清理日志</el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-tab-pane>
      
      <el-tab-pane label="通知设置" name="notifications">
        <div class="notifications-container">
          <!-- 通知开关卡片 -->
          <el-card class="setting-card" shadow="never">
            <template #header>
              <div class="card-header">
                <el-icon><Switch /></el-icon>
                <span>总开关</span>
              </div>
            </template>
            <div class="main-switch">
              <el-switch 
                v-model="settings.enabled" 
                size="large"
                active-text="启用通知" 
                inactive-text="禁用通知"
              />
              <p class="switch-desc">关闭后将不会发送任何通知</p>
            </div>
          </el-card>
          <!-- 邮件通知卡片 -->
          <el-card class="setting-card" shadow="never" :class="{ disabled: !settings.enabled }">
            <template #header>
              <div class="card-header">
                <el-icon><Message /></el-icon>
                <span>邮件通知</span>
                <el-switch v-model="settings.email_enabled" :disabled="!settings.enabled" />
              </div>
            </template>
            <el-form 
              ref="emailForm"
              :model="settings"
              :rules="emailRules"
              label-position="top"
              v-show="settings.email_enabled && settings.enabled"
              class="form-content"
            >
              <el-row :gutter="20">
                <el-col :span="12">
                  <el-form-item label="邮件地址" prop="email">
                    <el-input v-model="settings.email" placeholder="请输入接收通知的邮箱" />
                  </el-form-item>
                </el-col>
                <el-col :span="12">
                  <el-form-item label="SMTP服务器" prop="smtp_host">
                    <el-input v-model="settings.smtp_host" placeholder="smtp.example.com" />
                  </el-form-item>
                </el-col>
              </el-row>
              <el-row :gutter="20">
                <el-col :span="8">
                  <el-form-item label="SMTP端口" prop="smtp_port">
                    <el-input-number v-model="settings.smtp_port" :min="1" :max="65535" style="width: 100%" />
                  </el-form-item>
                </el-col>
                <el-col :span="8">
                  <el-form-item label="用户名" prop="smtp_username">
                    <el-input v-model="settings.smtp_username" placeholder="SMTP用户名" />
                  </el-form-item>
                </el-col>
                <el-col :span="8">
                  <el-form-item label="密码" prop="smtp_password">
                    <el-input 
                      v-model="settings.smtp_password" 
                      type="password" 
                      show-password 
                      placeholder="SMTP密码"
                    />
                  </el-form-item>
                </el-col>
              </el-row>
            </el-form>
          </el-card>
          <!-- Webhook通知卡片 -->
          <el-card class="setting-card" shadow="never" :class="{ disabled: !settings.enabled }">
            <template #header>
              <div class="card-header">
                <el-icon><Link /></el-icon>
                <span>Webhook通知</span>
                <el-switch v-model="settings.webhook_enabled" :disabled="!settings.enabled" />
              </div>
            </template>
            <el-form 
              ref="webhookForm"
              :model="settings"
              :rules="webhookRules"
              label-position="top"
              v-show="settings.webhook_enabled && settings.enabled"
              class="form-content"
            >
              <el-form-item label="Webhook URL" prop="webhook_url">
                <el-input 
                  v-model="settings.webhook_url" 
                  placeholder="https://your-webhook-url.com/notify"
                />
              </el-form-item>
              <el-form-item label="安全密钥 (可选)" prop="webhook_secret">
                <el-input 
                  v-model="settings.webhook_secret" 
                  type="password" 
                  show-password 
                  placeholder="用于验证请求的密钥"
                />
              </el-form-item>
            </el-form>
          </el-card>
          <!-- 钉钉通知卡片 -->
          <el-card class="setting-card" shadow="never" :class="{ disabled: !settings.enabled }">
            <template #header>
              <div class="card-header">
                <el-icon><ChatDotRound /></el-icon>
                <span>钉钉通知</span>
                <el-switch v-model="settings.dingtalk_enabled" :disabled="!settings.enabled" />
              </div>
            </template>
            <el-form 
              ref="dingtalkForm"
              :model="settings"
              :rules="dingtalkRules"
              label-position="top"
              v-show="settings.dingtalk_enabled && settings.enabled"
              class="form-content"
            >
              <el-form-item label="钉钉机器人Webhook" prop="dingtalk_webhook">
                <el-input 
                  v-model="settings.dingtalk_webhook" 
                  placeholder="https://oapi.dingtalk.com/robot/send?access_token=..."
                />
              </el-form-item>
              <el-form-item label="密钥 (可选)" prop="dingtalk_secret">
                <el-input 
                  v-model="settings.dingtalk_secret" 
                  type="password" 
                  show-password 
                  placeholder="钉钉机器人密钥"
                />
              </el-form-item>
            </el-form>
          </el-card>
          <!-- 短信通知卡片 -->
          <el-card class="setting-card" shadow="never" :class="{ disabled: !settings.enabled }">
            <template #header>
              <div class="card-header">
                <el-icon><Iphone /></el-icon>
                <span>短信通知</span>
                <el-switch v-model="settings.sms_enabled" :disabled="!settings.enabled" />
              </div>
            </template>
            <el-form 
              ref="smsForm"
              :model="settings"
              :rules="smsRules"
              label-position="top"
              v-show="settings.sms_enabled && settings.enabled"
              class="form-content"
            >
              <el-row :gutter="20">
                <el-col :span="12">
                  <el-form-item label="服务商" prop="sms_provider">
                    <el-select v-model="settings.sms_provider" placeholder="选择短信服务商" style="width: 100%">
                      <el-option label="阿里云" value="aliyun" />
                      <el-option label="腾讯云" value="tencent" />
                    </el-select>
                  </el-form-item>
                </el-col>
                <el-col :span="12">
                  <el-form-item label="API Key" prop="sms_api_key">
                    <el-input 
                      v-model="settings.sms_api_key" 
                      type="password" 
                      show-password 
                      placeholder="短信服务API Key"
                    />
                  </el-form-item>
                </el-col>
              </el-row>
              <el-row :gutter="20">
                <el-col :span="12">
                  <el-form-item label="模板ID" prop="sms_template_id">
                    <el-input v-model="settings.sms_template_id" placeholder="短信模板ID" />
                  </el-form-item>
                </el-col>
                <el-col :span="12">
                  <el-form-item label="签名" prop="sms_sign_name">
                    <el-input v-model="settings.sms_sign_name" placeholder="短信签名" />
                  </el-form-item>
                </el-col>
              </el-row>
            </el-form>
          </el-card>
          <!-- 操作按钮 -->
          <div class="action-buttons">
            <el-button 
              type="primary" 
              @click="handleSubmit" 
              :loading="saving"
              :disabled="!settings.enabled"
            >
              保存设置
            </el-button>
            <el-button 
              @click="handleTest" 
              :loading="testing"
              :disabled="!settings.enabled || !hasEnabledNotification"
            >
              测试通知
            </el-button>
            <el-button @click="handleReset">
              重置
            </el-button>
          </div>
        </div>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Switch,
  Message,
  Link,
  ChatDotRound,
  Iphone
} from '@element-plus/icons-vue'
import axios from 'axios'

// 新增表单ref和数据
const basicFormRef = ref(null)
const logsFormRef = ref(null)

const activeTab = ref('basic')

const basicForm = ref({
  max_concurrent_tasks: 5,
  default_retry_count: 3,
  default_retry_delay: 60,
  notification_enabled: false
})

const logsForm = ref({
  log_retention_days: 30,
  log_level: 'INFO',
  log_file_path: ''
})

const basicRules = {
  max_concurrent_tasks: [
    { required: true, message: '请输入最大并发任务数', trigger: 'blur' }
  ],
  default_retry_count: [
    { required: true, message: '请输入默认重试次数', trigger: 'blur' }
  ],
  default_retry_delay: [
    { required: true, message: '请输入默认重试延迟', trigger: 'blur' }
  ]
}

const logsRules = {
  log_retention_days: [
    { required: true, message: '请输入日志保留天数', trigger: 'blur' }
  ],
  log_level: [
    { required: true, message: '请选择日志级别', trigger: 'change' }
  ],
  log_file_path: [
    { required: true, message: '请输入日志文件路径', trigger: 'blur' }
  ]
}

const emailForm = ref(null)
const webhookForm = ref(null)
const dingtalkForm = ref(null)
const smsForm = ref(null)
const saving = ref(false)
const testing = ref(false)

const settings = ref({
  enabled: false,
  email_enabled: false,
  email: '',
  smtp_host: '',
  smtp_port: 587,
  smtp_username: '',
  smtp_password: '',
  webhook_enabled: false,
  webhook_url: '',
  webhook_secret: '',
  dingtalk_enabled: false,
  dingtalk_webhook: '',
  dingtalk_secret: '',
  sms_enabled: false,
  sms_provider: '',
  sms_api_key: '',
  sms_template_id: '',
  sms_sign_name: ''
})

const hasEnabledNotification = computed(() => {
  return settings.value.email_enabled || 
         settings.value.webhook_enabled || 
         settings.value.dingtalk_enabled || 
         settings.value.sms_enabled
})

const emailRules = {
  email: [
    { required: true, message: '请输入邮件地址', trigger: 'blur' },
    { type: 'email', message: '请输入正确的邮箱格式', trigger: 'blur' }
  ],
  smtp_host: [
    { required: true, message: '请输入SMTP服务器地址', trigger: 'blur' }
  ],
  smtp_port: [
    { required: true, message: '请输入SMTP端口', trigger: 'blur' }
  ],
  smtp_username: [
    { required: true, message: '请输入SMTP用户名', trigger: 'blur' }
  ],
  smtp_password: [
    { required: true, message: '请输入SMTP密码', trigger: 'blur' }
  ]
}

const webhookRules = {
  webhook_url: [
    { required: true, message: '请输入Webhook URL', trigger: 'blur' },
    { type: 'url', message: '请输入正确的URL格式', trigger: 'blur' }
  ],
  webhook_secret: [
    { required: true, message: '请输入Webhook密钥', trigger: 'blur' }
  ]
}

const dingtalkRules = {
  dingtalk_webhook: [
    { required: true, message: '请输入钉钉机器人Webhook', trigger: 'blur' },
    { type: 'url', message: '请输入正确的URL格式', trigger: 'blur' }
  ],
  dingtalk_secret: [
    { required: true, message: '请输入钉钉机器人密钥', trigger: 'blur' }
  ]
}

const smsRules = {
  sms_provider: [
    { required: true, message: '请选择短信服务商', trigger: 'change' }
  ],
  sms_api_key: [
    { required: true, message: '请输入API Key', trigger: 'blur' }
  ],
  sms_template_id: [
    { required: true, message: '请输入模板ID', trigger: 'blur' }
  ],
  sms_sign_name: [
    { required: true, message: '请输入签名', trigger: 'blur' }
  ]
}

const fetchSettings = async () => {
  try {
    const response = await axios.get('/api/settings')
    const data = response.data.data

    // 更新基本设置
    basicForm.value.max_concurrent_tasks = data.max_concurrent_tasks
    basicForm.value.default_retry_count = data.default_retry_count
    basicForm.value.default_retry_delay = data.default_retry_delay
    basicForm.value.notification_enabled = data.notification_enabled

    // 更新日志设置
    logsForm.value.log_retention_days = data.log_retention_days
    logsForm.value.log_level = data.log_level
    logsForm.value.log_file_path = data.log_file_path

    // 更新通知设置
    settings.value.enabled = data.notification_enabled
    settings.value.email_enabled = data.email_enabled
    settings.value.email = data.email
    settings.value.smtp_host = data.smtp_host
    settings.value.smtp_port = data.smtp_port
    settings.value.smtp_username = data.smtp_username
    settings.value.smtp_password = data.smtp_password
    settings.value.webhook_enabled = data.webhook_enabled
    settings.value.webhook_url = data.webhook_url
    settings.value.webhook_secret = data.webhook_secret
    settings.value.dingtalk_enabled = data.dingtalk_enabled
    settings.value.dingtalk_webhook = data.dingtalk_webhook
    settings.value.dingtalk_secret = data.dingtalk_secret
    settings.value.sms_enabled = data.sms_enabled
    settings.value.sms_provider = data.sms_provider
    settings.value.sms_api_key = data.sms_api_key
    settings.value.sms_template_id = data.sms_template_id
    settings.value.sms_sign_name = data.sms_sign_name
  } catch (error) {
    ElMessage.error('获取系统设置失败')
  }
}

const handleSubmit = async () => {
  if (!emailForm.value || !webhookForm.value || !dingtalkForm.value || !smsForm.value) return
  
  try {
    await emailForm.value.validate()
    await webhookForm.value.validate()
    await dingtalkForm.value.validate()
    await smsForm.value.validate()

    saving.value = true
    await axios.put('/api/settings/notifications', settings.value)
    ElMessage.success('通知设置保存成功')
  } catch (error) {
    if (error.response?.data?.error) {
      ElMessage.error(error.response.data.error)
    } else {
      ElMessage.error('保存通知设置失败')
    }
  } finally {
    saving.value = false
  }
}

const handleTest = async () => {
  if (!settings.value.enabled) {
    ElMessage.warning('请先启用通知总开关')
    return
  }
  try {
    testing.value = true
    await axios.post('/api/notifications/test')
    ElMessage.success('测试通知发送成功')
  } catch (error) {
    ElMessage.error(error.response?.data?.error || '测试通知发送失败')
  } finally {
    testing.value = false
  }
}

const handleReset = async () => {
  try {
    await ElMessageBox.confirm(
      '确定要重置所有通知设置吗？此操作不可恢复。',
      '警告',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    settings.value = {
      enabled: false,
      email_enabled: false,
      email: '',
      smtp_host: '',
      smtp_port: 587,
      smtp_username: '',
      smtp_password: '',
      webhook_enabled: false,
      webhook_url: '',
      webhook_secret: '',
      dingtalk_enabled: false,
      dingtalk_webhook: '',
      dingtalk_secret: '',
      sms_enabled: false,
      sms_provider: '',
      sms_api_key: '',
      sms_template_id: '',
      sms_sign_name: ''
    }
    ElMessage.success('通知设置已重置')
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('重置通知设置失败')
    }
  }
}

onMounted(() => {
  fetchSettings()
})
</script>

<style scoped>
.settings-container {
  padding: 20px;
  background: var(--bg-color);
  min-height: 100vh;
  color: var(--text-color);
}

.header {
  margin-bottom: 20px;
}

.header h2 {
  margin: 0;
  color: var(--text-color);
}

.settings-card {
  margin-bottom: 20px;
  border-radius: 12px;
  border: 1px solid var(--border-color);
  background: var(--card-bg);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: 600;
  color: var(--text-color);
}

.card-header .el-icon {
  color: #667eea;
  margin-right: 8px;
}

.form-tip {
  font-size: 12px;
  color: var(--text-secondary);
  margin-top: 5px;
}

/* 通知设置样式 */
.notification-settings {
  max-width: 1000px;
}

.settings-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding: 20px;
  background: var(--bg-secondary);
  border-radius: 8px;
  border: 1px solid var(--border-color);
}

.settings-info h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: var(--text-color);
}

.settings-info p {
  margin: 4px 0 0 0;
  color: var(--text-secondary);
  font-size: 14px;
}

.switch-content {
  padding: 20px;
  text-align: center;
}

.switch-content .el-switch {
  margin-bottom: 12px;
}

.switch-desc {
  margin: 0;
  color: var(--text-secondary);
  font-size: 14px;
}

.notification-type-card {
  border: 1px solid var(--border-color);
  border-radius: 8px;
  margin-bottom: 20px;
}

.notification-type-card.disabled {
  opacity: 0.6;
  pointer-events: none;
}

.type-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  border-bottom: 1px solid var(--bg-color);
}

.type-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.type-icon {
  color: #409eff;
  font-size: 18px;
}

.type-title {
  font-weight: 600;
  color: var(--text-color);
  font-size: 16px;
}

.type-description {
  padding: 0 20px 20px 20px;
}

.type-description p {
  margin: 0;
  color: var(--text-secondary);
  font-size: 14px;
  line-height: 1.5;
}

.notification-actions {
  text-align: center;
  padding: 20px 0;
}

.notification-actions .el-button {
  margin: 0 8px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .settings-container {
    padding: 16px;
  }
  
  .settings-header {
    flex-direction: column;
    gap: 16px;
    text-align: center;
  }
  
  .action-section {
    flex-direction: column;
  }
  
  .action-section .el-button {
    width: 100%;
  }
}

/* 动画效果 */
@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.notification-card {
  animation: fadeInUp 0.5s ease-out;
}

.notification-card:nth-child(1) { animation-delay: 0.1s; }
.notification-card:nth-child(2) { animation-delay: 0.2s; }
.notification-card:nth-child(3) { animation-delay: 0.3s; }
.notification-card:nth-child(4) { animation-delay: 0.4s; }
.notification-card:nth-child(5) { animation-delay: 0.5s; }
</style> 