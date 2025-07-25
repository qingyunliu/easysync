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
            :model="settings"
            :rules="basicRules"
            label-width="180px"
          >
            <el-form-item label="最大并发任务数" prop="max_concurrent_tasks">
              <el-input-number
                v-model="settings.max_concurrent_tasks"
                :min="1"
                :max="20"
              />
              <div class="form-tip">同时运行的最大任务数量</div>
            </el-form-item>
            
            <el-form-item label="默认重试次数" prop="default_retry_count">
              <el-input-number
                v-model="settings.default_retry_count"
                :min="0"
                :max="10"
              />
              <div class="form-tip">任务失败时的默认重试次数</div>
            </el-form-item>
            
            <el-form-item label="默认重试延迟(秒)" prop="default_retry_delay">
              <el-input-number
                v-model="settings.default_retry_delay"
                :min="1"
                :max="3600"
              />
              <div class="form-tip">任务失败后的重试等待时间(秒)</div>
            </el-form-item>
            
            <el-form-item>
              <el-button type="primary" @click="handleSubmit">保存设置</el-button>
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
            :model="settings"
            :rules="logsRules"
            label-width="180px"
          >
            <el-form-item label="日志保留天数" prop="log_retention_days">
              <el-input-number
                v-model="settings.log_retention_days"
                :min="1"
                :max="365"
              />
              <div class="form-tip">系统日志保留的天数，超过此天数的日志将被自动删除</div>
            </el-form-item>
            
            <el-form-item label="日志级别" prop="log_level">
              <el-select v-model="settings.log_level">
                <el-option label="DEBUG" value="DEBUG" />
                <el-option label="INFO" value="INFO" />
                <el-option label="WARNING" value="WARNING" />
                <el-option label="ERROR" value="ERROR" />
                <el-option label="CRITICAL" value="CRITICAL" />
              </el-select>
              <div class="form-tip">系统日志记录的最低级别</div>
            </el-form-item>
            
            <el-form-item label="日志文件路径" prop="log_file_path">
              <el-input v-model="settings.log_file_path" />
              <div class="form-tip">系统日志文件的存储路径</div>
            </el-form-item>
            
            <el-form-item>
              <el-button type="primary" @click="handleSubmit">保存设置</el-button>
              <el-button @click="clearLogs">清理日志</el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-tab-pane>
      
      <el-tab-pane label="通知设置" name="notifications">
        <div class="notify-section">
          <!-- 邮件通知分组 -->
          <div class="notify-group-title clickable" @click="toggleCollapse('email')">
            <span class="notify-bar email"></span>
            <el-icon><Message /></el-icon>
            <span class="notify-title">邮件通知</span>
            <span class="flex-spacer"></span>
            <el-button v-if="!notifyStates.email.editing" type="text" @click.stop="startEdit('email')">编辑</el-button>
            <template v-else>
              <el-button type="primary" size="small" @click.stop="saveEdit('email')" :loading="saving" :disabled="!notifyStates.email.testPassed || saving">保存</el-button>
              <el-button size="small" @click.stop="cancelEdit('email')">取消</el-button>
            </template>
            <el-icon :class="notifyStates.email.collapsed ? 'collapse-arrow collapsed' : 'collapse-arrow'">
              <ArrowDown />
            </el-icon>
          </div>
          <div class="notify-switch-row">
            <el-switch
              v-model="settings.email_enabled"
              :disabled="!notifyStates.email.editing"
              :class="{ 'switch-disabled': !notifyStates.email.editing }"
            />
            <span class="notify-switch-label">启用邮件通知</span>
          </div>
          <el-card v-show="!notifyStates.email.collapsed && settings.email_enabled">
            <el-form :model="settings" ref="emailForm" :rules="emailRules" label-width="120px" class="notify-form-col" :disabled="!notifyStates.email.editing">
              <el-form-item label="SMTP服务器" prop="smtp_host">
                <el-input v-model="settings.smtp_host" placeholder="smtp.example.com" />
              </el-form-item>
              <el-form-item label="端口" prop="smtp_port">
                <el-input-number v-model="settings.smtp_port" :min="1" :max="65535" style="width: 100%" />
              </el-form-item>
              <el-form-item label="SMTP用户名" prop="smtp_username">
                <el-input v-model="settings.smtp_username" placeholder="用户名" />
              </el-form-item>
              <el-form-item label="SMTP密码" prop="smtp_password">
                <el-input v-model="settings.smtp_password" type="password" show-password placeholder="密码" />
              </el-form-item>
              <el-form-item label="发件人邮箱" prop="email">
                <el-input v-model="settings.email" placeholder="support@email.example.com" />
              </el-form-item>
            </el-form>
            <div class="notify-actions-bar">
              <el-button @click="handleTest('email')" :disabled="saving">测试发送</el-button>
            </div>
          </el-card>
          <!-- 短信通知分组 -->
          <div class="notify-group-title clickable" @click="toggleCollapse('sms')">
            <span class="notify-bar sms"></span>
            <el-icon><Iphone /></el-icon>
            <span class="notify-title">短信通知</span>
            <span class="flex-spacer"></span>
            <el-button v-if="!notifyStates.sms.editing" type="text" @click.stop="startEdit('sms')">编辑</el-button>
            <template v-else>
              <el-button type="primary" size="small" @click.stop="saveEdit('sms')" :loading="saving" :disabled="!notifyStates.sms.testPassed || saving">保存</el-button>
              <el-button size="small" @click.stop="cancelEdit('sms')">取消</el-button>
            </template>
            <el-icon :class="notifyStates.sms.collapsed ? 'collapse-arrow collapsed' : 'collapse-arrow'">
              <ArrowDown />
            </el-icon>
          </div>
          <div class="notify-switch-row">
            <el-switch 
              v-model="settings.sms_enabled"
              :disabled="!notifyStates.sms.editing"
              :class="{ 'switch-disabled': !notifyStates.sms.editing }"
            />
            <span class="notify-switch-label">启用短信通知</span>
          </div>
          <el-card v-show="!notifyStates.sms.collapsed && settings.sms_enabled">
            <el-form :model="settings" ref="smsForm" :rules="smsRules" label-width="120px" class="notify-form-col" :disabled="!notifyStates.sms.editing">
              <el-form-item label="服务商" prop="sms_provider">
                <el-select v-model="settings.sms_provider" placeholder="选择服务商" style="width: 100%">
                  <el-option label="阿里云" value="aliyun" />
                  <el-option label="腾讯云" value="tencent" />
                </el-select>
              </el-form-item>
              <el-form-item label="API Key" prop="sms_api_key">
                <el-input v-model="settings.sms_api_key" type="password" show-password placeholder="API Key" />
              </el-form-item>
              <el-form-item label="模板ID" prop="sms_template_id">
                <el-input v-model="settings.sms_template_id" placeholder="短信模板ID" />
              </el-form-item>
              <el-form-item label="签名" prop="sms_sign_name">
                <el-input v-model="settings.sms_sign_name" placeholder="短信签名" />
              </el-form-item>
            </el-form>
            <div class="notify-actions-bar">
              <el-button @click="handleTest('sms')" :disabled="saving">测试发送</el-button>
            </div>
          </el-card>
          <!-- 钉钉通知分组 -->
          <div class="notify-group-title clickable" @click="toggleCollapse('dingtalk')">
            <span class="notify-bar dingtalk"></span>
            <el-icon><ChatDotRound /></el-icon>
            <span class="notify-title">钉钉通知</span>
            <span class="flex-spacer"></span>
            <el-button v-if="!notifyStates.dingtalk.editing" type="text" @click.stop="startEdit('dingtalk')">编辑</el-button>
            <template v-else>
              <el-button type="primary" size="small" @click.stop="saveEdit('dingtalk')" :loading="saving" :disabled="!notifyStates.dingtalk.testPassed || saving">保存</el-button>
              <el-button size="small" @click.stop="cancelEdit('dingtalk')">取消</el-button>
            </template>
            <el-icon :class="notifyStates.dingtalk.collapsed ? 'collapse-arrow collapsed' : 'collapse-arrow'">
              <ArrowDown />
            </el-icon>
          </div>
          <div class="notify-switch-row">
            <el-switch 
              v-model="settings.dingtalk_enabled"
              :disabled="!notifyStates.dingtalk.editing"
              :class="{ 'switch-disabled': !notifyStates.dingtalk.editing }"
            />
            <span class="notify-switch-label">启用钉钉通知</span>
          </div>
          <el-card v-show="!notifyStates.dingtalk.collapsed && settings.dingtalk_enabled">
            <el-form :model="settings" ref="dingtalkForm" :rules="dingtalkRules" label-width="120px" class="notify-form-col" :disabled="!notifyStates.dingtalk.editing">
              <el-form-item label="Webhook" prop="dingtalk_webhook">
                <el-input v-model="settings.dingtalk_webhook" placeholder="https://oapi.dingtalk.com/robot/send?access_token=..." />
              </el-form-item>
              <el-form-item label="密钥" prop="dingtalk_secret">
                <el-input v-model="settings.dingtalk_secret" type="password" show-password placeholder="机器人密钥(可选)" />
              </el-form-item>
            </el-form>
            <div class="notify-actions-bar">
              <el-button @click="handleTest('dingtalk')" :disabled="saving">测试发送</el-button>
            </div>
          </el-card>
          <!-- Webhook通知分组 -->
          <div class="notify-group-title clickable" @click="toggleCollapse('webhook')">
            <span class="notify-bar webhook"></span>
            <el-icon><Link /></el-icon>
            <span class="notify-title">Webhook通知</span>
            <span class="flex-spacer"></span>
            <el-button v-if="!notifyStates.webhook.editing" type="text" @click.stop="startEdit('webhook')">编辑</el-button>
            <template v-else>
              <el-button type="primary" size="small" @click.stop="saveEdit('webhook')" :loading="saving" :disabled="!notifyStates.webhook.testPassed || saving">保存</el-button>
              <el-button size="small" @click.stop="cancelEdit('webhook')">取消</el-button>
            </template>
            <el-icon :class="notifyStates.webhook.collapsed ? 'collapse-arrow collapsed' : 'collapse-arrow'">
              <ArrowDown />
            </el-icon>
          </div>
          <div class="notify-switch-row">
            <el-switch 
              v-model="settings.webhook_enabled"
              :disabled="!notifyStates.webhook.editing"
              :class="{ 'switch-disabled': !notifyStates.webhook.editing }"
            />
            <span class="notify-switch-label">启用Webhook通知</span>
          </div>
          <el-card v-show="!notifyStates.webhook.collapsed && settings.webhook_enabled">
            <el-form :model="settings" ref="webhookForm" :rules="webhookRules" label-width="120px" class="notify-form-col" :disabled="!notifyStates.webhook.editing">
              <el-form-item label="Webhook URL" prop="webhook_url">
                <el-input v-model="settings.webhook_url" placeholder="https://your-webhook-url.com/notify" />
              </el-form-item>
              <el-form-item label="安全密钥" prop="webhook_secret">
                <el-input v-model="settings.webhook_secret" type="password" show-password placeholder="Webhook密钥(可选)" />
              </el-form-item>
            </el-form>
            <div class="notify-actions-bar">
              <el-button @click="handleTest('webhook')" :disabled="saving">测试发送</el-button>
            </div>
          </el-card>
        </div>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, reactive, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Switch,
  Message,
  Link,
  ChatDotRound,
  Iphone,
  Bell,
  ArrowDown
} from '@element-plus/icons-vue'
import axios from 'axios'

// 新增表单ref和数据
const basicFormRef = ref(null)
const logsFormRef = ref(null)

const activeTab = ref('basic')
const saving = ref(false)
const testing = ref(false)

// 折叠与编辑状态
const notifyStates = reactive({
  email: { collapsed: false, editing: false, backup: {}, testPassed: false },
  sms: { collapsed: false, editing: false, backup: {}, testPassed: false },
  dingtalk: { collapsed: false, editing: false, backup: {}, testPassed: false },
  webhook: { collapsed: false, editing: false, backup: {}, testPassed: false }
})

function toggleCollapse(type) {
  notifyStates[type].collapsed = !notifyStates[type].collapsed
}
function startEdit(type) {
  notifyStates[type].editing = true
  notifyStates[type].testPassed = false
  // 备份当前配置
  notifyStates[type].backup = JSON.parse(JSON.stringify(settings.value))
}
function cancelEdit(type) {
  ElMessageBox.confirm('确定要取消编辑并还原为之前的配置吗？', '确认取消', {
    confirmButtonText: '确定',
    cancelButtonText: '继续编辑',
    type: 'warning',
  }).then(() => {
    // 还原备份
    Object.assign(settings.value, notifyStates[type].backup)
    notifyStates[type].editing = false
    notifyStates[type].testPassed = false
  }).catch(() => {
    // 用户点击“继续编辑”，无需处理
  })
}
async function saveEdit(type) {
  // 只校验当前分组
  let formRef = null
  if (type === 'email') formRef = emailForm
  if (type === 'sms') formRef = smsForm
  if (type === 'dingtalk') formRef = dingtalkForm
  if (type === 'webhook') formRef = webhookForm
  if (!formRef.value) return
  formRef.value.validate(async (valid) => {
    if (!valid) return
    if (!notifyStates[type].testPassed) {
      ElMessage.warning('请先测试通过后再保存！')
      return
    }
    saving.value = true
    try {
      await axios.put('/api/settings', settings.value)
      ElMessage.success('设置保存成功')
      notifyStates[type].editing = false
      notifyStates[type].testPassed = false
    } catch (error) {
      ElMessage.error('保存通知设置失败')
    } finally {
      saving.value = false
    }
  })
}

// 统一 settings 对象，包含所有设置
const settings = ref({
  // 基本设置
  max_concurrent_tasks: 5,
  default_retry_count: 3,
  default_retry_delay: 60,
  // 日志设置
  log_retention_days: 30,
  log_level: 'INFO',
  log_file_path: '',
  // 通知设置
  enabled: false,
  email_enabled: false,
  smtp_host: '',
  smtp_port: 587,
  smtp_username: '',
  smtp_password: '',
  email: '',
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
  sms_sign_name: '',
  // 通知事件
  event_scan_success: true,
  event_scan_error: true
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

const notifyForm = ref(null)
const notifyRules = computed(() => {
  const rules = {}
  if (settings.value.email_enabled) {
    rules.email = [
      { required: true, message: '请输入收件邮箱', trigger: 'blur' },
      { type: 'email', message: '请输入正确的邮箱格式', trigger: 'blur' }
    ]
    rules.smtp_host = [
      { required: true, message: '请输入SMTP服务器', trigger: 'blur' }
    ]
    rules.smtp_port = [
      { required: true, message: '请输入SMTP端口', trigger: 'blur' }
    ]
    rules.smtp_username = [
      { required: true, message: '请输入SMTP用户名', trigger: 'blur' }
    ]
    rules.smtp_password = [
      { required: true, message: '请输入SMTP密码', trigger: 'blur' }
    ]
  }
  if (settings.value.webhook_enabled) {
    rules.webhook_url = [
      { required: true, message: '请输入Webhook URL', trigger: 'blur' },
      { type: 'url', message: '请输入正确的URL格式', trigger: 'blur' }
    ]
  }
  if (settings.value.dingtalk_enabled) {
    rules.dingtalk_webhook = [
      { required: true, message: '请输入钉钉Webhook', trigger: 'blur' },
      { type: 'url', message: '请输入正确的URL格式', trigger: 'blur' }
    ]
  }
  if (settings.value.sms_enabled) {
    rules.sms_provider = [
      { required: true, message: '请选择服务商', trigger: 'change' }
    ]
    rules.sms_api_key = [
      { required: true, message: '请输入API Key', trigger: 'blur' }
    ]
    rules.sms_template_id = [
      { required: true, message: '请输入模板ID', trigger: 'blur' }
    ]
    rules.sms_sign_name = [
      { required: true, message: '请输入签名', trigger: 'blur' }
    ]
  }
  return rules
})

const fetchSettings = async () => {
  try {
    const response = await axios.get('/api/settings')
    const data = response.data.data
    Object.assign(settings.value, data)
  } catch (error) {
    ElMessage.error('获取系统设置失败')
  }
}

const handleSubmit = async () => {
  try {
    saving.value = true
    await axios.put('/api/settings', settings.value)
    ElMessage.success('设置保存成功')
  } catch (error) {
    ElMessage.error('保存设置失败')
  } finally {
    saving.value = false
    }
  }

function handleTest(type) {
  let formRef = null
  if (type === 'email') formRef = emailForm
  if (type === 'sms') formRef = smsForm
  if (type === 'dingtalk') formRef = dingtalkForm
  if (type === 'webhook') formRef = webhookForm
  if (!formRef.value) return
  formRef.value.validate(async (valid) => {
    if (!valid) return
    testing.value = true
    // 只传当前分组的配置
    const config = { type }
    if (type === 'email') {
      config.email_enabled = settings.value.email_enabled
      config.smtp_host = settings.value.smtp_host
      config.smtp_port = settings.value.smtp_port
      config.smtp_username = settings.value.smtp_username
      config.smtp_password = settings.value.smtp_password
      config.email = settings.value.email
    }
    if (type === 'sms') {
      config.sms_enabled = settings.value.sms_enabled
      config.sms_provider = settings.value.sms_provider
      config.sms_api_key = settings.value.sms_api_key
      config.sms_template_id = settings.value.sms_template_id
      config.sms_sign_name = settings.value.sms_sign_name
    }
    if (type === 'dingtalk') {
      config.dingtalk_enabled = settings.value.dingtalk_enabled
      config.dingtalk_webhook = settings.value.dingtalk_webhook
      config.dingtalk_secret = settings.value.dingtalk_secret
    }
    if (type === 'webhook') {
      config.webhook_enabled = settings.value.webhook_enabled
      config.webhook_url = settings.value.webhook_url
      config.webhook_secret = settings.value.webhook_secret
    }
    axios.post('/api/notifications/test', config)
      .then(() => {
        ElMessage.success('测试通知已发送，请检查对应通道')
        notifyStates[type].testPassed = true
      })
      .catch(error => {
        ElMessage.error(error.response?.data?.message || error.response?.data?.msg || '测试通知发送失败')
        notifyStates[type].testPassed = false
      })
      .finally(() => {
        testing.value = false
      })
  })
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
      sms_sign_name: '',
      // 通知事件
      event_scan_success: true,
      event_scan_error: true
    }
    ElMessage.success('通知设置已重置')
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('重置通知设置失败')
    }
  }
}

const handleNotifySubmit = () => {
  notifyForm.value.validate(async (valid) => {
    if (!valid) return
    saving.value = true
    try {
      await axios.put('/api/settings', settings.value)
    ElMessage.success('通知设置保存成功')
  } catch (error) {
      ElMessage.error('保存通知设置失败')
    } finally {
      saving.value = false
    }
  })
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
.notify-form {
  max-width: 1100px;
  margin: 0 auto;
}
.notify-card {
  border-radius: 16px;
  box-shadow: 0 2px 16px 0 rgba(64,158,255,0.06);
  margin-bottom: 18px;
  transition: box-shadow 0.2s, opacity 0.2s;
  min-height: 260px;
  background: var(--card-bg);
  border: 1px solid var(--border-color);
  position: relative;
}
.notify-card.disabled {
  opacity: 0.5;
  pointer-events: none;
}
.card-header {
  display: flex;
  align-items: center;
  gap: 10px;
  font-weight: 600;
  font-size: 16px;
  color: var(--text-color);
}
.notify-actions {
  display: flex;
  justify-content: center;
  gap: 24px;
  margin: 32px 0 0 0;
}
.notify-section {
  background: var(--card-bg);
  border-radius: 16px;
  box-shadow: 0 2px 16px 0 rgba(64,158,255,0.06);
  padding: 32px 32px 24px 32px;
  margin-bottom: 32px;
}
.notify-group-title {
  display: flex;
  align-items: center;
  font-size: 18px;
  font-weight: 600;
  margin: 32px 0 12px 0;
  gap: 10px;
}
.notify-bar {
  width: 4px;
  height: 22px;
  border-radius: 2px;
  display: inline-block;
  margin-right: 8px;
}
.notify-bar.email { background: #409EFF; }
.notify-bar.wechat { background: #07c160; }
.notify-bar.event { background: #faad14; }
.notify-bar.sms { background: #ff9800; }
.notify-bar.dingtalk { background: #409EFF; }
.notify-bar.webhook { background: #13c2c2; }
.notify-title {
  margin-right: 16px;
}
.notify-switch {
  margin-left: auto;
}
.notify-switch-label {
  margin-left: 8px;
  color: #888;
  font-size: 14px;
}
.notify-card {
  border-radius: 12px;
  box-shadow: 0 2px 8px 0 rgba(64,158,255,0.06);
  margin-bottom: 18px;
  border: 1px solid #f0f0f0;
  background: #fff;
  transition: box-shadow 0.2s, opacity 0.2s;
}
.notify-card.disabled {
  opacity: 0.5;
  pointer-events: none;
}
.notify-form-row {
  padding: 12px 0 0 0;
}
.event-card {
  background: #fafbfc;
  border: 1px solid #f0f0f0;
}
.event-row {
  padding: 12px 0 0 0;
}
.event-label {
  font-size: 15px;
  color: #333;
  margin-right: 12px;
}
.notify-actions-bar {
  display: flex;
  justify-content: flex-end;
  gap: 24px;
  margin: 32px 0 0 0;
  padding-bottom: 8px;
}
.notify-form-col {
  padding: 12px 0 0 0;
  display: flex;
  flex-direction: column;
  gap: 0;
}
.flex-spacer { flex: 1; }
.clickable { cursor: pointer; user-select: none; }
.collapse-arrow { transition: transform 0.2s; margin-left: 8px; }
.collapse-arrow.collapsed { transform: rotate(-90deg); }
.notify-switch-row {
  display: flex;
  align-items: center;
  gap: 12px;
  margin: 8px 0 16px 0;
}
.switch-disabled {
  opacity: 0.5;
  pointer-events: none;
}
</style> 