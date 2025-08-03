<template>
  <div class="notification-channels-page">
    <div class="page-header">
      <h1>通知渠道</h1>
      <el-button type="primary" @click="openCreateDialog">创建渠道</el-button>
    </div>

    <el-card>
      <div v-loading="loading">
        <div v-if="channels.length === 0" class="empty-state">
          <el-empty description="暂无通知渠道">
            <el-button type="primary" @click="openCreateDialog">创建第一个渠道</el-button>
          </el-empty>
        </div>
        
        <div v-else class="channels-grid">
          <div v-for="channel in channels" :key="channel.id" class="channel-card">
            <div class="channel-header">
              <h3>{{ channel.name }}</h3>
              <div class="channel-tags">
                <el-tag :type="getChannelTypeTagType(channel.channel_type)" size="small">
                  {{ getChannelTypeLabel(channel.channel_type) }}
                </el-tag>
                <el-tag v-if="channel.is_default" type="success" size="small">默认</el-tag>
              </div>
            </div>
            <div class="channel-content">
              <p class="channel-description">{{ channel.description || '暂无描述' }}</p>
              <div class="channel-config">
                <div class="config-item">
                  <span class="config-label">重试次数:</span>
                  <span class="config-value">{{ channel.retry_count }}次</span>
                </div>
                <div class="config-item">
                  <span class="config-label">速率限制:</span>
                  <span class="config-value">{{ channel.rate_limit }}次/小时</span>
                </div>
                <div class="config-item">
                  <span class="config-label">超时时间:</span>
                  <span class="config-value">{{ channel.timeout }}秒</span>
                </div>
              </div>
            </div>
            <div class="channel-footer">
              <el-switch v-model="channel.enabled" @change="toggleChannel(channel)" />
              <div class="channel-actions">
                <el-button type="text" size="small" @click="editChannel(channel)">编辑</el-button>
                <el-button type="text" size="small" @click="testChannel(channel)">测试</el-button>
                <el-button type="text" size="small" @click="deleteChannel(channel)" style="color: #f56c6c">删除</el-button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </el-card>

    <!-- 创建/编辑弹窗 -->
    <el-dialog v-model="dialogVisible" :title="dialogMode === 'create' ? '创建通知渠道' : '编辑通知渠道'" width="600px">
      <el-form :model="channelForm" label-width="100px">
        <el-form-item label="渠道名称">
          <el-input v-model="channelForm.name" />
        </el-form-item>
        
        <el-form-item label="渠道类型">
          <el-select v-model="channelForm.channel_type" @change="handleChannelTypeChange">
            <el-option label="邮件" value="email" />
            <el-option label="短信" value="sms" />
            <el-option label="WebHook" value="webhook" />
            <el-option label="钉钉" value="dingtalk" />
            <el-option label="Slack" value="slack" />
          </el-select>
        </el-form-item>
        
        <!-- 邮件配置 -->
        <div v-if="channelForm.channel_type === 'email'" class="email-config">
          <el-form-item label="SMTP服务器">
            <el-input v-model="channelForm.config.smtp_server" />
          </el-form-item>
          <el-form-item label="SMTP端口">
            <el-input-number v-model="channelForm.config.smtp_port" :min="1" :max="65535" />
          </el-form-item>
          <el-form-item label="用户名">
            <el-input v-model="channelForm.config.username" />
          </el-form-item>
          <el-form-item label="密码">
            <el-input v-model="channelForm.config.password" type="password" />
          </el-form-item>
        </div>
        
        <!-- 短信配置 -->
        <div v-if="channelForm.channel_type === 'sms'" class="sms-config">
          <el-form-item label="API密钥">
            <el-input v-model="channelForm.config.api_key" />
          </el-form-item>
          <el-form-item label="密钥">
            <el-input v-model="channelForm.config.secret" type="password" />
          </el-form-item>
        </div>
        
        <!-- WebHook配置 -->
        <div v-if="channelForm.channel_type === 'webhook'" class="webhook-config">
          <el-form-item label="URL">
            <el-input v-model="channelForm.config.url" />
          </el-form-item>
        </div>
        
        <!-- 钉钉配置 -->
        <div v-if="channelForm.channel_type === 'dingtalk'" class="dingtalk-config">
          <el-form-item label="WebHook URL">
            <el-input v-model="channelForm.config.webhook_url" />
          </el-form-item>
        </div>
        
        <!-- Slack配置 -->
        <div v-if="channelForm.channel_type === 'slack'" class="slack-config">
          <el-form-item label="WebHook URL">
            <el-input v-model="channelForm.config.webhook_url" />
          </el-form-item>
        </div>
        
        <el-form-item label="重试次数">
          <el-input-number v-model="channelForm.retry_count" :min="1" :max="10" />
        </el-form-item>
        
        <el-form-item label="速率限制">
          <el-input-number v-model="channelForm.rate_limit" :min="1" :max="1000" />
          <span style="margin-left: 8px; color: #909399;">次/小时</span>
        </el-form-item>
        
        <el-form-item label="超时时间">
          <el-input-number v-model="channelForm.timeout" :min="5" :max="300" />
          <span style="margin-left: 8px; color: #909399;">秒</span>
        </el-form-item>
        
        <el-form-item label="设为默认">
          <el-switch v-model="channelForm.is_default" />
        </el-form-item>
        
        <el-form-item label="启用状态">
          <el-switch v-model="channelForm.enabled" />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitChannel">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import axios from 'axios'

const loading = ref(false)
const channels = ref([])
const dialogVisible = ref(false)
const dialogMode = ref('create')
const editingChannel = ref(null)

const channelForm = reactive({
  name: '',
  channel_type: 'email',
  enabled: true,
  retry_count: 3,
  rate_limit: 100,
  timeout: 30,
  is_default: false,
  config: {}
})

onMounted(() => {
  fetchChannels()
})

const fetchChannels = async () => {
  try {
    loading.value = true
    const response = await axios.get('/api/notifications/channels')
    channels.value = response.data.channels
  } catch (error) {
    ElMessage.error('获取通知渠道失败')
  } finally {
    loading.value = false
  }
}

const openCreateDialog = () => {
  dialogMode.value = 'create'
  editingChannel.value = null
  resetChannelForm()
  dialogVisible.value = true
}

const resetChannelForm = () => {
  Object.assign(channelForm, {
    name: '',
    channel_type: 'email',
    enabled: true,
    retry_count: 3,
    rate_limit: 100,
    timeout: 30,
    is_default: false,
    config: {}
  })
}

const handleChannelTypeChange = () => {
  // 根据渠道类型重置配置
  channelForm.config = {}
  
  if (channelForm.channel_type === 'email') {
    channelForm.config = {
      smtp_server: '',
      smtp_port: 587,
      username: '',
      password: ''
    }
  } else if (channelForm.channel_type === 'sms') {
    channelForm.config = {
      api_key: '',
      secret: ''
    }
  } else if (channelForm.channel_type === 'webhook') {
    channelForm.config = {
      url: ''
    }
  } else if (channelForm.channel_type === 'dingtalk' || channelForm.channel_type === 'slack') {
    channelForm.config = {
      webhook_url: ''
    }
  }
}

const submitChannel = async () => {
  try {
    if (dialogMode.value === 'create') {
      await axios.post('/api/notifications/channels', channelForm)
      ElMessage.success('通知渠道创建成功')
    } else {
      await axios.put(`/api/notifications/channels/${editingChannel.value.id}`, channelForm)
      ElMessage.success('通知渠道更新成功')
    }
    
    dialogVisible.value = false
    fetchChannels()
  } catch (error) {
    ElMessage.error(dialogMode.value === 'create' ? '创建通知渠道失败' : '更新通知渠道失败')
  }
}

const editChannel = (channel) => {
  dialogMode.value = 'edit'
  editingChannel.value = channel
  
  Object.assign(channelForm, {
    name: channel.name,
    channel_type: channel.channel_type,
    enabled: channel.enabled,
    retry_count: channel.retry_count,
    rate_limit: channel.rate_limit,
    timeout: channel.timeout,
    is_default: channel.is_default,
    config: { ...channel.config }
  })
  
  dialogVisible.value = true
}

const toggleChannel = async (channel) => {
  try {
    await axios.put(`/api/notifications/channels/${channel.id}`, { enabled: channel.enabled })
    ElMessage.success(`通知渠道已${channel.enabled ? '启用' : '禁用'}`)
  } catch (error) {
    channel.enabled = !channel.enabled
    ElMessage.error('更新状态失败')
  }
}

const testChannel = async (channel) => {
  try {
    await axios.post(`/api/notifications/channels/${channel.id}/test`)
    ElMessage.success('测试通知发送成功')
  } catch (error) {
    ElMessage.error('测试通知发送失败')
  }
}

const deleteChannel = async (channel) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除通知渠道"${channel.name}"吗？此操作不可恢复。`,
      '确认删除',
      {
        type: 'warning',
        confirmButtonText: '确定删除',
        cancelButtonText: '取消'
      }
    )
    
    await axios.delete(`/api/notifications/channels/${channel.id}`)
    ElMessage.success('通知渠道删除成功')
    fetchChannels()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除通知渠道失败')
    }
  }
}

const getChannelTypeTagType = (channelType) => {
  const typeMap = {
    email: 'primary',
    sms: 'success',
    webhook: 'warning',
    dingtalk: 'info',
    slack: 'danger'
  }
  return typeMap[channelType] || 'info'
}

const getChannelTypeLabel = (channelType) => {
  const labelMap = {
    email: '邮件',
    sms: '短信',
    webhook: 'WebHook',
    dingtalk: '钉钉',
    slack: 'Slack'
  }
  return labelMap[channelType] || channelType
}
</script>

<style scoped>
.notification-channels-page {
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.page-header h1 {
  margin: 0;
}

.channels-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  gap: 20px;
}

.channel-card {
  padding: 16px;
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  background: #fff;
}

.channel-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 12px;
}

.channel-header h3 {
  margin: 0;
  font-size: 16px;
}

.channel-tags {
  display: flex;
  gap: 8px;
}

.channel-content {
  margin-bottom: 16px;
}

.channel-description {
  margin: 0 0 12px 0;
  color: #606266;
  font-size: 14px;
}

.channel-config {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.config-item {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
}

.config-label {
  color: #909399;
}

.config-value {
  color: #606266;
  font-weight: 500;
}

.channel-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 12px;
  border-top: 1px solid #f0f0f0;
}

.channel-actions {
  display: flex;
  gap: 8px;
}

.empty-state {
  padding: 40px 0;
  text-align: center;
}

.email-config,
.sms-config,
.webhook-config,
.dingtalk-config,
.slack-config {
  border: 1px solid #e4e7ed;
  border-radius: 6px;
  padding: 16px;
  margin-bottom: 16px;
  background: #fafafa;
}
</style>