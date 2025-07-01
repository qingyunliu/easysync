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
        <el-card class="settings-card">
          <template #header>
            <div class="card-header">
              <span>通知设置</span>
            </div>
          </template>
          
          <el-form
            ref="notificationsFormRef"
            :model="notificationsForm"
            :rules="notificationsRules"
            label-width="180px"
          >
            <el-form-item label="启用邮件通知" prop="email_enabled">
              <el-switch v-model="notificationsForm.email_enabled" />
              <div class="form-tip">是否启用邮件通知功能</div>
            </el-form-item>
            
            <template v-if="notificationsForm.email_enabled">
              <el-form-item label="SMTP服务器" prop="smtp_host">
                <el-input v-model="notificationsForm.smtp_host" />
              </el-form-item>
              
              <el-form-item label="SMTP端口" prop="smtp_port">
                <el-input-number v-model="notificationsForm.smtp_port" :min="1" :max="65535" />
              </el-form-item>
              
              <el-form-item label="SMTP用户名" prop="smtp_username">
                <el-input v-model="notificationsForm.smtp_username" />
              </el-form-item>
              
              <el-form-item label="SMTP密码" prop="smtp_password">
                <el-input v-model="notificationsForm.smtp_password" type="password" show-password />
              </el-form-item>
              
              <el-form-item label="发件人邮箱" prop="sender_email">
                <el-input v-model="notificationsForm.sender_email" />
              </el-form-item>
              
              <el-form-item label="收件人邮箱" prop="recipient_email">
                <el-input v-model="notificationsForm.recipient_email" />
              </el-form-item>
            </template>
            
            <el-form-item label="启用Webhook通知" prop="webhook_enabled">
              <el-switch v-model="notificationsForm.webhook_enabled" />
              <div class="form-tip">是否启用Webhook通知功能</div>
            </el-form-item>
            
            <template v-if="notificationsForm.webhook_enabled">
              <el-form-item label="Webhook URL" prop="webhook_url">
                <el-input v-model="notificationsForm.webhook_url" />
              </el-form-item>
              
              <el-form-item label="Webhook密钥" prop="webhook_secret">
                <el-input v-model="notificationsForm.webhook_secret" type="password" show-password />
              </el-form-item>
            </template>
            
            <el-form-item>
              <el-button type="primary" @click="saveNotificationsSettings">保存设置</el-button>
              <el-button @click="testNotifications">测试通知</el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import axios from 'axios'

// 状态
const activeTab = ref('basic')
const basicFormRef = ref(null)
const logsFormRef = ref(null)
const notificationsFormRef = ref(null)

// 基本设置表单
const basicForm = reactive({
  max_concurrent_tasks: 5,
  default_retry_count: 3,
  default_retry_delay: 60,
  notification_enabled: true
})

// 日志设置表单
const logsForm = reactive({
  log_retention_days: 30,
  log_level: 'INFO',
  log_file_path: '/var/log/easysync'
})

// 通知设置表单
const notificationsForm = reactive({
  email_enabled: false,
  smtp_host: '',
  smtp_port: 587,
  smtp_username: '',
  smtp_password: '',
  sender_email: '',
  recipient_email: '',
  webhook_enabled: false,
  webhook_url: '',
  webhook_secret: ''
})

// 表单验证规则
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

const notificationsRules = {
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
  ],
  sender_email: [
    { required: true, message: '请输入发件人邮箱', trigger: 'blur' },
    { type: 'email', message: '请输入正确的邮箱格式', trigger: 'blur' }
  ],
  recipient_email: [
    { required: true, message: '请输入收件人邮箱', trigger: 'blur' },
    { type: 'email', message: '请输入正确的邮箱格式', trigger: 'blur' }
  ],
  webhook_url: [
    { required: true, message: '请输入Webhook URL', trigger: 'blur' },
    { type: 'url', message: '请输入正确的URL格式', trigger: 'blur' }
  ],
  webhook_secret: [
    { required: true, message: '请输入Webhook密钥', trigger: 'blur' }
  ]
}

// 获取系统设置
const fetchSettings = async () => {
  try {
    const response = await axios.get('/api/settings')
    const settings = response.data
    
    // 更新基本设置
    basicForm.max_concurrent_tasks = settings.max_concurrent_tasks
    basicForm.default_retry_count = settings.default_retry_count
    basicForm.default_retry_delay = settings.default_retry_delay
    basicForm.notification_enabled = settings.notification_enabled
    
    // 更新日志设置
    logsForm.log_retention_days = settings.log_retention_days
    logsForm.log_level = settings.log_level
    logsForm.log_file_path = settings.log_file_path
    
    // 更新通知设置
    notificationsForm.email_enabled = settings.email_enabled
    notificationsForm.smtp_host = settings.smtp_host
    notificationsForm.smtp_port = settings.smtp_port
    notificationsForm.smtp_username = settings.smtp_username
    notificationsForm.sender_email = settings.sender_email
    notificationsForm.recipient_email = settings.recipient_email
    notificationsForm.webhook_enabled = settings.webhook_enabled
    notificationsForm.webhook_url = settings.webhook_url
  } catch (error) {
    ElMessage.error('获取系统设置失败')
  }
}

// 保存基本设置
const saveBasicSettings = async () => {
  if (!basicFormRef.value) return
  
  try {
    await basicFormRef.value.validate()
    await axios.put('/api/settings/basic', basicForm)
    ElMessage.success('基本设置保存成功')
  } catch (error) {
    if (error.response?.data?.error) {
      ElMessage.error(error.response.data.error)
    } else {
      ElMessage.error('保存基本设置失败')
    }
  }
}

// 保存日志设置
const saveLogsSettings = async () => {
  if (!logsFormRef.value) return
  
  try {
    await logsFormRef.value.validate()
    await axios.put('/api/settings/logs', logsForm)
    ElMessage.success('日志设置保存成功')
  } catch (error) {
    if (error.response?.data?.error) {
      ElMessage.error(error.response.data.error)
    } else {
      ElMessage.error('保存日志设置失败')
    }
  }
}

// 清理日志
const clearLogs = async () => {
  try {
    await ElMessageBox.confirm(
      '确定要清理所有日志吗？此操作不可恢复。',
      '警告',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    await axios.post('/api/logs/clear')
    ElMessage.success('日志清理成功')
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('日志清理失败')
    }
  }
}

// 保存通知设置
const saveNotificationsSettings = async () => {
  if (!notificationsFormRef.value) return
  
  try {
    await notificationsFormRef.value.validate()
    await axios.put('/api/settings/notifications', notificationsForm)
    ElMessage.success('通知设置保存成功')
  } catch (error) {
    if (error.response?.data?.error) {
      ElMessage.error(error.response.data.error)
    } else {
      ElMessage.error('保存通知设置失败')
    }
  }
}

// 测试通知
const testNotifications = async () => {
  try {
    await axios.post('/api/notifications/test')
    ElMessage.success('测试通知发送成功')
  } catch (error) {
    ElMessage.error(error.response?.data?.error || '测试通知发送失败')
  }
}

// 生命周期钩子
onMounted(() => {
  fetchSettings()
})
</script>

<style scoped>
.settings-container {
  padding: 20px;
}

.header {
  margin-bottom: 20px;
}

.header h2 {
  margin: 0;
}

.settings-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.form-tip {
  font-size: 12px;
  color: #909399;
  margin-top: 5px;
}
</style> 