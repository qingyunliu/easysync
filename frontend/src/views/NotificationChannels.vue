<template>
  <div class="notification-channels-page">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-left">
        <h2>通知渠道</h2>
        <p class="page-description">管理系统通知渠道，支持邮件、短信、WebHook等多种通知方式</p>
      </div>
      <div class="header-actions">
        <el-button type="primary" @click="openCreateDialog">
          <el-icon><Plus /></el-icon>
          创建渠道
        </el-button>
      </div>
    </div>

    <!-- 筛选栏 -->
    <div class="filter-bar">
      <el-form :model="filters" inline>
        <el-form-item label="渠道类型">
          <el-select v-model="filters.channel_type" placeholder="选择渠道类型" clearable @change="loadChannels">
            <el-option label="邮件" value="email" />
            <el-option label="短信" value="sms" />
            <el-option label="WebHook" value="webhook" />
            <el-option label="钉钉" value="dingtalk" />
            <el-option label="Slack" value="slack" />
          </el-select>
        </el-form-item>
        <el-form-item label="渠道名称">
          <el-input
            v-model="filters.keyword"
            placeholder="搜索渠道名称"
            clearable
            @keyup.enter="loadChannels"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="loadChannels">
            <el-icon><Search /></el-icon>
            搜索
          </el-button>
          <el-button @click="resetFilter">重置</el-button>
        </el-form-item>
      </el-form>
    </div>

    <!-- 渠道列表 -->
    <div class="channels-container">
      <el-table 
        :data="filteredChannels" 
        style="width: 100%"
        @selection-change="handleSelectionChange"
        v-loading="loading"
      >
        <el-table-column type="selection" width="55" />
        
        <el-table-column prop="name" label="渠道名称" sortable>
          <template #default="{ row }">
            <el-link type="primary" @click="showChannelDetail(row)">
              {{ row.name }}
            </el-link>
          </template>
        </el-table-column>
        
        <el-table-column prop="channel_type" label="渠道类型" sortable>
          <template #default="{ row }">
            <el-tag :type="getChannelTypeTagType(row.channel_type)" size="small">
              {{ getChannelTypeLabel(row.channel_type) }}
            </el-tag>
          </template>
        </el-table-column>
        
        <el-table-column label="渠道状态" sortable>
          <template #default="{ row }">
            <div class="channel-status">
              <el-tag v-if="row.is_default" type="success" size="small">默认</el-tag>
              <el-tag :type="row.enabled ? 'success' : 'info'" size="small">
                {{ row.enabled ? '启用' : '禁用' }}
              </el-tag>
            </div>
          </template>
        </el-table-column>
        
        <el-table-column label="重试次数" sortable>
          <template #default="{ row }">
            {{ row.retry_count }}次
          </template>
        </el-table-column>
        
        <el-table-column label="速率限制" sortable>
          <template #default="{ row }">
            {{ row.rate_limit }}次/小时
          </template>
        </el-table-column>
        
        <el-table-column label="超时时间" sortable>
          <template #default="{ row }">
            {{ row.timeout }}秒
          </template>
        </el-table-column>
        
        <el-table-column prop="created_at" label="创建时间" sortable>
          <template #default="{ row }">
            <div class="time-display">
              <div>{{ formatDate(row.created_at).split(' ')[0] }}</div>
              <div class="time">{{ formatDate(row.created_at).split(' ')[1] }}</div>
            </div>
          </template>
        </el-table-column>
        
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button 
              size="small" 
              :type="row.enabled ? 'warning' : 'success'"
              @click="toggleChannel(row)"
              :loading="row.toggling"
            >
              {{ row.enabled ? '禁用' : '启用' }}
            </el-button>
            <el-button size="small" @click="editChannel(row)">编辑</el-button>
            <el-button size="small" type="warning" @click="testChannel(row)">测试</el-button>
            <el-button 
              size="small" 
              type="danger" 
              @click="deleteChannel(row)"
            >
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
      
      <div v-if="filteredChannels.length === 0" class="empty-state">
        <el-empty description="暂无通知渠道">
          <el-button type="primary" @click="openCreateDialog">创建第一个渠道</el-button>
        </el-empty>
      </div>
    </div>

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
          <span style="margin-left: 8px; color: var(--text-secondary);">次/小时</span>
        </el-form-item>
        
        <el-form-item label="超时时间">
          <el-input-number v-model="channelForm.timeout" :min="5" :max="300" />
          <span style="margin-left: 8px; color: var(--text-secondary);">秒</span>
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

    <!-- 渠道详情侧拉抽屉 -->
    <el-drawer
      v-model="showChannelDetailDrawer"
      title="渠道详情"
      direction="rtl"
      size="50%"
    >
      <div v-if="selectedChannel" class="channel-detail">
        <div class="detail-section">
          <h3>基本信息</h3>
          <div class="detail-item">
            <span class="label">渠道名称:</span>
            <span class="value">{{ selectedChannel.name }}</span>
          </div>
          <div class="detail-item">
            <span class="label">渠道类型:</span>
            <span class="value">
              <el-tag :type="getChannelTypeTagType(selectedChannel.channel_type)" size="small">
                {{ getChannelTypeLabel(selectedChannel.channel_type) }}
              </el-tag>
            </span>
          </div>
          <div class="detail-item">
            <span class="label">渠道状态:</span>
            <span class="value">
              <el-tag v-if="selectedChannel.is_default" type="success" size="small">默认</el-tag>
              <el-tag :type="selectedChannel.enabled ? 'success' : 'info'" size="small">
                {{ selectedChannel.enabled ? '启用' : '禁用' }}
              </el-tag>
            </span>
          </div>
        </div>

        <div class="detail-section">
          <h3>配置信息</h3>
          <div class="detail-item">
            <span class="label">重试次数:</span>
            <span class="value">{{ selectedChannel.retry_count }}次</span>
          </div>
          <div class="detail-item">
            <span class="label">速率限制:</span>
            <span class="value">{{ selectedChannel.rate_limit }}次/小时</span>
          </div>
          <div class="detail-item">
            <span class="label">超时时间:</span>
            <span class="value">{{ selectedChannel.timeout }}秒</span>
          </div>
        </div>

        <div class="detail-section" v-if="selectedChannel.config">
          <h3>渠道配置</h3>
          <div class="detail-item" v-for="(value, key) in selectedChannel.config" :key="key">
            <span class="label">{{ getConfigLabel(key) }}:</span>
            <span class="value">{{ key.includes('password') || key.includes('secret') ? '******' : value }}</span>
          </div>
        </div>

        <div class="detail-section">
          <h3>其他信息</h3>
          <div class="detail-item">
            <span class="label">创建时间:</span>
            <span class="value">{{ formatDate(selectedChannel.created_at) }}</span>
          </div>
          <div class="detail-item">
            <span class="label">更新时间:</span>
            <span class="value">{{ formatDate(selectedChannel.updated_at) }}</span>
          </div>
        </div>

        <div class="detail-actions">
          <el-button type="primary" @click="editChannel(selectedChannel)">编辑渠道</el-button>
          <el-button @click="testChannel(selectedChannel)">测试渠道</el-button>
          <el-button 
            :type="selectedChannel.enabled ? 'warning' : 'success'"
            @click="toggleChannel(selectedChannel)"
            :loading="selectedChannel.toggling"
          >
            {{ selectedChannel.enabled ? '禁用' : '启用' }}
          </el-button>
          <el-button 
            type="danger" 
            @click="deleteChannel(selectedChannel)"
          >
            删除渠道
          </el-button>
        </div>
      </div>
    </el-drawer>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Search } from '@element-plus/icons-vue'
import axios from 'axios'

const loading = ref(false)
const channels = ref([])
const dialogVisible = ref(false)
const dialogMode = ref('create')
const editingChannel = ref(null)
const showChannelDetailDrawer = ref(false)
const selectedChannel = ref(null)

// 筛选表单
const filters = reactive({
  channel_type: '',
  keyword: ''
})

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

// 计算属性
const filteredChannels = computed(() => {
  let result = channels.value
  
  if (filters.channel_type) {
    result = result.filter(channel => channel.channel_type === filters.channel_type)
  }
  
  if (filters.keyword) {
    const keyword = filters.keyword.toLowerCase()
    result = result.filter(channel => 
      channel.name.toLowerCase().includes(keyword) ||
      channel.channel_type.toLowerCase().includes(keyword)
    )
  }
  
  return result
})

onMounted(() => {
  fetchChannels()
})

const fetchChannels = async () => {
  try {
    loading.value = true
    const response = await axios.get('/api/notifications/channels')
    channels.value = response.data.channels || []
  } catch (error) {
    ElMessage.error('获取通知渠道失败')
  } finally {
    loading.value = false
  }
}

const loadChannels = () => {
  fetchChannels()
}

const resetFilter = () => {
  filters.channel_type = ''
  filters.keyword = ''
  loadChannels()
}

const showChannelDetail = (channel) => {
  selectedChannel.value = channel
  showChannelDetailDrawer.value = true
}

const handleSelectionChange = (selection) => {
  console.log('选中的渠道:', selection)
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
    channel.toggling = true
    await axios.put(`/api/notifications/channels/${channel.id}`, { enabled: channel.enabled })
    ElMessage.success(`通知渠道已${channel.enabled ? '启用' : '禁用'}`)
  } catch (error) {
    channel.enabled = !channel.enabled
    ElMessage.error('更新状态失败')
  } finally {
    channel.toggling = false
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

const getConfigLabel = (key) => {
  const labelMap = {
    smtp_server: 'SMTP服务器',
    smtp_port: 'SMTP端口',
    username: '用户名',
    password: '密码',
    api_key: 'API密钥',
    secret: '密钥',
    url: 'URL',
    webhook_url: 'WebHook URL'
  }
  return labelMap[key] || key
}

const formatDate = (date) => {
  if (!date) return '-'
  return new Date(date).toLocaleString('zh-CN')
}
</script>

<style scoped>
.notification-channels-page {
  padding: 20px;
  min-height: 100vh;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 30px;
  padding: 20px;
  background: var(--card-bg);
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.header-left h2 {
  margin: 0 0 5px 0;
  color: var(--text-color);
  font-size: 24px;
}

.page-description {
  margin: 0;
  color: var(--text-secondary);
  font-size: 14px;
}

.header-actions {
  display: flex;
  gap: 10px;
}

.filter-bar {
  background: var(--card-bg);
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  margin-bottom: 20px;
}

.channels-container {
  margin-top: 20px;
}

/* 表格样式 */
.el-table {
  border-radius: 8px;
  overflow: hidden;
}

.time-display {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
}

.time-display .time {
  font-size: 12px;
  color: var(--text-secondary);
  margin-top: 2px;
}

.channel-status {
  display: flex;
  gap: 4px;
}

.empty-state {
  text-align: center;
  padding: 60px 20px;
}

/* 侧拉抽屉样式 */
.channel-detail {
  padding: 20px;
}

.detail-section {
  margin-bottom: 30px;
}

.detail-section h3 {
  margin: 0 0 15px 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--text-color);
  border-bottom: 1px solid #ebeef5;
  padding-bottom: 8px;
}

.detail-item {
  display: flex;
  margin-bottom: 12px;
  align-items: flex-start;
}

.detail-item .label {
  width: 100px;
  font-weight: 500;
  color: var(--text-color);
  flex-shrink: 0;
}

.detail-item .value {
  flex: 1;
  color: var(--text-color);
}

.detail-actions {
  margin-top: 30px;
  padding-top: 20px;
  border-top: 1px solid #ebeef5;
  display: flex;
  gap: 10px;
}

.email-config,
.sms-config,
.webhook-config,
.dingtalk-config,
.slack-config {
  border: 1px solid var(--border-color);
  border-radius: 6px;
  padding: 16px;
  margin-bottom: 16px;
  background: var(--card-bg);
}
</style>