<template>
  <div class="notifications-container">
    <div class="page-header">
      <h1>通知设置</h1>
      <p class="page-description">配置系统通知方式，及时获取重要信息</p>
    </div>

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
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Bell,
  MuteNotification,
  Switch,
  Message,
  Connection,
  Link,
  Key,
  ChatDotRound,
  Iphone,
  Check,
  Notification,
  RefreshLeft
} from '@element-plus/icons-vue'
import axios from 'axios'

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

// 计算属性
const hasEnabledNotification = computed(() => {
  return settings.value.email_enabled || 
         settings.value.webhook_enabled || 
         settings.value.dingtalk_enabled || 
         settings.value.sms_enabled
})

// 邮件验证规则
const emailRules = {
  email: [
    { required: true, message: '请输入邮件地址', trigger: 'blur' },
    { type: 'email', message: '请输入正确的邮件地址', trigger: 'blur' }
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

// Webhook验证规则
const webhookRules = {
  webhook_url: [
    { required: true, message: '请输入Webhook URL', trigger: 'blur' },
    { type: 'url', message: '请输入正确的URL地址', trigger: 'blur' }
  ]
}

// 钉钉验证规则
const dingtalkRules = {
  dingtalk_webhook: [
    { required: true, message: '请输入钉钉Webhook URL', trigger: 'blur' },
    { type: 'url', message: '请输入正确的URL地址', trigger: 'blur' }
  ]
}

// 短信验证规则
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

const rules = {
}

// 获取通知设置
const fetchSettings = async () => {
  try {
    const response = await axios.get('/api/notifications/settings')
    settings.value = response.data
  } catch (error) {
    ElMessage.error('获取通知设置失败')
  }
}

// 保存设置
const handleSubmit = async () => {
  saving.value = true
  try {
    // 验证启用的表单
    const formPromises = []
    if (settings.value.email_enabled && emailForm.value) {
      formPromises.push(emailForm.value.validate())
    }
    if (settings.value.webhook_enabled && webhookForm.value) {
      formPromises.push(webhookForm.value.validate())
    }
    if (settings.value.dingtalk_enabled && dingtalkForm.value) {
      formPromises.push(dingtalkForm.value.validate())
    }
    if (settings.value.sms_enabled && smsForm.value) {
      formPromises.push(smsForm.value.validate())
    }
    
    if (formPromises.length > 0) {
      await Promise.all(formPromises)
    }
    
    await axios.put('/api/notifications/settings', settings.value)
    ElMessage.success('保存设置成功')
  } catch (error) {
    if (error.response?.data?.error) {
      ElMessage.error(error.response.data.error)
    } else {
      ElMessage.error('保存设置失败')
    }
  } finally {
    saving.value = false
  }
}

// 测试通知
const handleTest = async () => {
  testing.value = true
  try {
    await axios.post('/api/notifications/test')
    ElMessage.success('测试通知发送成功')
  } catch (error) {
    ElMessage.error(error.response?.data?.error || '测试通知发送失败')
  } finally {
    testing.value = false
  }
}

// 重置设置
const handleReset = async () => {
  try {
    await ElMessageBox.confirm(
      '这将重置所有通知设置，是否继续？',
      '确认重置',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )
    await fetchSettings()
    ElMessage.success('重置成功')
  } catch {
    // 取消操作
  }
}

onMounted(() => {
  fetchSettings()
})
</script>

<style scoped>
.notifications-container {
  padding: 20px;
  max-width: 1000px;
  margin: 0 auto;
  background: var(--bg-color);
  color: var(--text-color);
}

.page-header {
  margin-bottom: 20px;
}

.page-header h1 {
  margin: 0 0 8px 0;
  color: var(--text-color);
  font-size: 24px;
  font-weight: 600;
}

.page-description {
  margin: 0;
  color: var(--text-secondary);
  font-size: 14px;
}

.setting-card {
  margin-bottom: 20px;
  background: var(--card-bg);
  border-radius: 8px;
  box-shadow: var(--card-shadow);
  border: 1px solid var(--border-color);
}

.setting-card.disabled {
  opacity: 0.6;
  pointer-events: none;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-weight: 600;
  color: var(--text-color);
}

.card-header .el-icon {
  margin-right: 8px;
  color: #409eff;
}

.main-switch {
  padding: 20px;
  text-align: center;
}

.main-switch .el-switch {
  margin-bottom: 12px;
}

.switch-desc {
  margin: 0;
  color: var(--text-secondary);
  font-size: 14px;
}

.form-content {
  padding: 20px;
  padding-top: 0;
}

.action-buttons {
  text-align: center;
  padding: 20px 0;
}

.action-buttons .el-button {
  margin: 0 8px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .notifications-container {
    padding: 16px;
  }
  
  .action-buttons {
    text-align: center;
  }
  
  .action-buttons .el-button {
    margin: 4px 2px;
  }
}
</style> 