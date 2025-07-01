<template>
  <div class="notifications-container">
    <div class="header">
      <h2>通知设置</h2>
    </div>
    
    <el-form
      ref="settingsForm"
      :model="settings"
      :rules="rules"
      label-width="120px"
      class="settings-form"
    >
      <el-form-item label="启用通知">
        <el-switch v-model="settings.enabled" />
      </el-form-item>
      
      <el-divider>邮件通知</el-divider>
      
      <el-form-item label="启用邮件通知">
        <el-switch v-model="settings.email_enabled" />
      </el-form-item>
      
      <el-form-item
        label="邮件地址"
        prop="email"
        v-if="settings.email_enabled"
      >
        <el-input v-model="settings.email" />
      </el-form-item>
      
      <el-form-item
        label="SMTP服务器"
        prop="smtp_host"
        v-if="settings.email_enabled"
      >
        <el-input v-model="settings.smtp_host" />
      </el-form-item>
      
      <el-form-item
        label="SMTP端口"
        prop="smtp_port"
        v-if="settings.email_enabled"
      >
        <el-input-number v-model="settings.smtp_port" :min="1" :max="65535" />
      </el-form-item>
      
      <el-form-item
        label="SMTP用户名"
        prop="smtp_username"
        v-if="settings.email_enabled"
      >
        <el-input v-model="settings.smtp_username" />
      </el-form-item>
      
      <el-form-item
        label="SMTP密码"
        prop="smtp_password"
        v-if="settings.email_enabled"
      >
        <el-input
          v-model="settings.smtp_password"
          type="password"
          show-password
        />
      </el-form-item>
      
      <el-divider>Webhook通知</el-divider>
      
      <el-form-item label="启用Webhook">
        <el-switch v-model="settings.webhook_enabled" />
      </el-form-item>
      
      <el-form-item
        label="Webhook URL"
        prop="webhook_url"
        v-if="settings.webhook_enabled"
      >
        <el-input v-model="settings.webhook_url" />
      </el-form-item>
      
      <el-form-item
        label="Webhook密钥"
        prop="webhook_secret"
        v-if="settings.webhook_enabled"
      >
        <el-input
          v-model="settings.webhook_secret"
          type="password"
          show-password
        />
      </el-form-item>
      
      <el-form-item>
        <el-button type="primary" @click="handleSubmit">保存设置</el-button>
        <el-button @click="handleTest">测试通知</el-button>
      </el-form-item>
    </el-form>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import axios from 'axios'

const settingsForm = ref(null)
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
  webhook_secret: ''
})

const rules = {
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
  ],
  webhook_url: [
    { required: true, message: '请输入Webhook URL', trigger: 'blur' },
    { type: 'url', message: '请输入正确的URL地址', trigger: 'blur' }
  ],
  webhook_secret: [
    { required: true, message: '请输入Webhook密钥', trigger: 'blur' }
  ]
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
  if (!settingsForm.value) return
  
  try {
    await settingsForm.value.validate()
    await axios.put('/api/notifications/settings', settings.value)
    ElMessage.success('保存设置成功')
  } catch (error) {
    if (error.response?.data?.error) {
      ElMessage.error(error.response.data.error)
    } else {
      ElMessage.error('保存设置失败')
    }
  }
}

// 测试通知
const handleTest = async () => {
  try {
    await axios.post('/api/notifications/test')
    ElMessage.success('测试通知发送成功')
  } catch (error) {
    ElMessage.error(error.response?.data?.error || '测试通知发送失败')
  }
}

onMounted(() => {
  fetchSettings()
})
</script>

<style scoped>
.notifications-container {
  padding: 20px;
}

.header {
  margin-bottom: 20px;
}

.header h2 {
  margin: 0;
}

.settings-form {
  max-width: 600px;
  margin: 0 auto;
}
</style> 