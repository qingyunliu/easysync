<template>
  <div class="notification-channels-page">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-left">
        <h1>通知渠道</h1>
        <p class="page-description">配置邮件、webhook、钉钉等通知方式，用于告警消息推送</p>
      </div>
      <div class="header-right">
        <el-button type="primary" @click="openCreateDialog">
          <el-icon><Plus /></el-icon>
          创建渠道
        </el-button>
        <el-button @click="refreshData">
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
      </div>
    </div>

    <!-- 过滤器 -->
    <el-card class="filter-card" shadow="never">
      <div class="filter-container">
        <div class="filter-left">
          <el-select v-model="filters.channel_type" placeholder="渠道类型" style="width: 140px" @change="handleFilterChange">
            <el-option label="全部类型" value="" />
            <el-option label="邮件" value="email" />
            <el-option label="Webhook" value="webhook" />
            <el-option label="钉钉" value="dingtalk" />
            <el-option label="短信" value="sms" />
            <el-option label="Slack" value="slack" />
          </el-select>
          
          <el-select v-model="filters.enabled" placeholder="启用状态" style="width: 120px" @change="handleFilterChange">
            <el-option label="全部状态" value="" />
            <el-option label="已启用" value="true" />
            <el-option label="已禁用" value="false" />
          </el-select>
        </div>
        
        <div class="filter-right">
          <el-input
            v-model="filters.search"
            placeholder="搜索渠道名称"
            style="width: 260px"
            @input="handleFilterChange"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
        </div>
      </div>
    </el-card>

    <!-- 数据表格 -->
    <el-card class="table-card" shadow="never">
      <el-table
        v-loading="loading"
        :data="channels"
        style="width: 100%"
        empty-text="暂无通知渠道"
      >
        <el-table-column prop="name" label="渠道名称" min-width="160">
          <template #default="{ row }">
            <div class="channel-name">
              <el-icon class="channel-icon" :color="getChannelTypeColor(row.channel_type)">
                <component :is="getChannelTypeIcon(row.channel_type)" />
              </el-icon>
              <span>{{ row.name }}</span>
              <el-tag v-if="row.is_default" type="primary" size="small" style="margin-left: 8px">默认</el-tag>
            </div>
          </template>
        </el-table-column>
        
        <el-table-column prop="channel_type" label="类型" width="100">
          <template #default="{ row }">
            <el-tag :type="getChannelTypeTagType(row.channel_type)" size="small">
              {{ getChannelTypeLabel(row.channel_type) }}
            </el-tag>
          </template>
        </el-table-column>
        
        <el-table-column prop="description" label="描述" min-width="200" show-overflow-tooltip />
        
        <el-table-column prop="rate_limit" label="速率限制" width="100">
          <template #default="{ row }">
            {{ row.rate_limit }}/小时
          </template>
        </el-table-column>
        
        <el-table-column prop="retry_attempts" label="重试次数" width="100" />
        
        <el-table-column prop="enabled" label="状态" width="80">
          <template #default="{ row }">
            <el-switch
              v-model="row.enabled"
              @change="handleStatusChange(row)"
              :loading="row.updating"
            />
          </template>
        </el-table-column>
        
        <el-table-column prop="updated_at" label="更新时间" width="160">
          <template #default="{ row }">
            {{ formatTime(row.updated_at) }}
          </template>
        </el-table-column>
        
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="testChannel(row)">
              <el-icon><Promotion /></el-icon>
              测试
            </el-button>
            <el-button link type="primary" @click="editChannel(row)">
              <el-icon><Edit /></el-icon>
              编辑
            </el-button>
            <el-button link type="danger" @click="deleteChannel(row)">
              <el-icon><Delete /></el-icon>
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 创建/编辑对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogType === 'create' ? '创建通知渠道' : '编辑通知渠道'"
      width="800px"
      @close="resetForm"
    >
      <el-form
        ref="formRef"
        :model="form"
        :rules="formRules"
        label-width="100px"
        label-position="left"
      >
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="渠道名称" prop="name">
              <el-input v-model="form.name" placeholder="请输入渠道名称" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="渠道类型" prop="channel_type">
              <el-select v-model="form.channel_type" placeholder="选择渠道类型" @change="handleChannelTypeChange">
                <el-option label="邮件" value="email" />
                <el-option label="Webhook" value="webhook" />
                <el-option label="钉钉" value="dingtalk" />
                <el-option label="短信" value="sms" />
                <el-option label="Slack" value="slack" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item label="描述">
          <el-input v-model="form.description" type="textarea" :rows="2" placeholder="请输入渠道描述" />
        </el-form-item>

        <!-- 渠道配置 -->
        <el-form-item label="渠道配置" prop="config">
          <div class="config-container">
            <!-- 邮件配置 -->
            <div v-if="form.channel_type === 'email'" class="config-form">
              <el-row :gutter="20">
                <el-col :span="12">
                  <el-form-item label="SMTP服务器" prop="config.smtp_host" label-width="100px">
                    <el-input v-model="form.config.smtp_host" placeholder="smtp.gmail.com" />
                  </el-form-item>
                </el-col>
                <el-col :span="12">
                  <el-form-item label="端口" prop="config.smtp_port" label-width="60px">
                    <el-input-number v-model="form.config.smtp_port" :min="1" :max="65535" placeholder="587" />
                  </el-form-item>
                </el-col>
              </el-row>
              <el-row :gutter="20">
                <el-col :span="12">
                  <el-form-item label="用户名" prop="config.username" label-width="100px">
                    <el-input v-model="form.config.username" placeholder="your@email.com" />
                  </el-form-item>
                </el-col>
                <el-col :span="12">
                  <el-form-item label="密码" prop="config.password" label-width="60px">
                    <el-input v-model="form.config.password" type="password" placeholder="请输入密码" show-password />
                  </el-form-item>
                </el-col>
              </el-row>
              <el-form-item label="启用TLS" label-width="100px">
                <el-switch v-model="form.config.use_tls" />
              </el-form-item>
            </div>

            <!-- Webhook配置 -->
            <div v-else-if="form.channel_type === 'webhook'" class="config-form">
              <el-form-item label="Webhook URL" prop="config.url" label-width="120px">
                <el-input v-model="form.config.url" placeholder="https://example.com/webhook" />
              </el-form-item>
              <el-row :gutter="20">
                <el-col :span="12">
                  <el-form-item label="请求方法" prop="config.method" label-width="100px">
                    <el-select v-model="form.config.method" placeholder="选择方法">
                      <el-option label="POST" value="POST" />
                      <el-option label="PUT" value="PUT" />
                    </el-select>
                  </el-form-item>
                </el-col>
                <el-col :span="12">
                  <el-form-item label="Content-Type" prop="config.content_type" label-width="120px">
                    <el-select v-model="form.config.content_type" placeholder="选择类型">
                      <el-option label="application/json" value="application/json" />
                      <el-option label="application/x-www-form-urlencoded" value="application/x-www-form-urlencoded" />
                    </el-select>
                  </el-form-item>
                </el-col>
              </el-row>
              <el-form-item label="Secret" label-width="120px">
                <el-input v-model="form.config.secret" type="password" placeholder="可选的验证密钥" show-password />
              </el-form-item>
            </div>

            <!-- 钉钉配置 -->
            <div v-else-if="form.channel_type === 'dingtalk'" class="config-form">
              <el-form-item label="Webhook URL" prop="config.webhook_url" label-width="120px">
                <el-input v-model="form.config.webhook_url" placeholder="钉钉机器人Webhook URL" />
              </el-form-item>
              <el-form-item label="密钥" label-width="120px">
                <el-input v-model="form.config.secret" type="password" placeholder="钉钉机器人密钥" show-password />
              </el-form-item>
            </div>

            <!-- SMS配置 -->
            <div v-else-if="form.channel_type === 'sms'" class="config-form">
              <el-row :gutter="20">
                <el-col :span="12">
                  <el-form-item label="API Key" prop="config.api_key" label-width="80px">
                    <el-input v-model="form.config.api_key" type="password" placeholder="短信服务API Key" show-password />
                  </el-form-item>
                </el-col>
                <el-col :span="12">
                  <el-form-item label="模板ID" prop="config.template_id" label-width="80px">
                    <el-input v-model="form.config.template_id" placeholder="短信模板ID" />
                  </el-form-item>
                </el-col>
              </el-row>
              <el-form-item label="签名" prop="config.sign_name" label-width="80px">
                <el-input v-model="form.config.sign_name" placeholder="短信签名" />
              </el-form-item>
            </div>

            <!-- Slack配置 -->
            <div v-else-if="form.channel_type === 'slack'" class="config-form">
              <el-form-item label="Webhook URL" prop="config.webhook_url" label-width="120px">
                <el-input v-model="form.config.webhook_url" placeholder="Slack Incoming Webhook URL" />
              </el-form-item>
              <el-form-item label="频道" label-width="120px">
                <el-input v-model="form.config.channel" placeholder="#general" />
              </el-form-item>
            </div>
          </div>
        </el-form-item>

        <el-row :gutter="20">
          <el-col :span="8">
            <el-form-item label="速率限制" prop="rate_limit">
              <el-input-number v-model="form.rate_limit" :min="1" :max="1000" />
              <span style="margin-left: 8px; color: var(--el-text-color-regular);">次/小时</span>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="重试次数" prop="retry_attempts">
              <el-input-number v-model="form.retry_attempts" :min="0" :max="10" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="超时时间" prop="timeout">
              <el-input-number v-model="form.timeout" :min="5" :max="300" />
              <span style="margin-left: 8px; color: var(--el-text-color-regular);">秒</span>
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="启用状态">
              <el-switch v-model="form.enabled" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="设为默认">
              <el-switch v-model="form.is_default" />
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>

      <template #footer>
        <span class="dialog-footer">
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button type="primary" @click="submitForm" :loading="submitLoading">
            {{ dialogType === 'create' ? '创建' : '更新' }}
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, nextTick } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Refresh, Search, Edit, Delete, Promotion, Message, Link, ChatDotRound, Phone, Monitor } from '@element-plus/icons-vue'
import axios from 'axios'

// 响应式数据
const loading = ref(false)
const channels = ref([])
const dialogVisible = ref(false)
const dialogType = ref('create')
const submitLoading = ref(false)
const formRef = ref()

// 过滤器
const filters = reactive({
  channel_type: '',
  enabled: '',
  search: ''
})

// 表单数据
const form = reactive({
  name: '',
  description: '',
  channel_type: '',
  enabled: true,
  is_default: false,
  config: {},
  rate_limit: 100,
  retry_attempts: 3,
  timeout: 30
})

// 表单验证规则
const formRules = {
  name: [
    { required: true, message: '请输入渠道名称', trigger: 'blur' }
  ],
  channel_type: [
    { required: true, message: '请选择渠道类型', trigger: 'change' }
  ],
  'config.smtp_host': [
    { required: true, message: '请输入SMTP服务器', trigger: 'blur' }
  ],
  'config.smtp_port': [
    { required: true, message: '请输入端口', trigger: 'blur' }
  ],
  'config.username': [
    { required: true, message: '请输入用户名', trigger: 'blur' }
  ],
  'config.password': [
    { required: true, message: '请输入密码', trigger: 'blur' }
  ],
  'config.url': [
    { required: true, message: '请输入Webhook URL', trigger: 'blur' },
    { type: 'url', message: '请输入有效的URL', trigger: 'blur' }
  ],
  'config.webhook_url': [
    { required: true, message: '请输入Webhook URL', trigger: 'blur' },
    { type: 'url', message: '请输入有效的URL', trigger: 'blur' }
  ]
}

// 页面加载时获取数据
onMounted(() => {
  fetchChannels()
})

// 获取通知渠道列表
const fetchChannels = async () => {
  loading.value = true
  try {
    const params = {}
    if (filters.channel_type) params.channel_type = filters.channel_type
    if (filters.enabled !== '') params.enabled = filters.enabled === 'true'
    if (filters.search) params.search = filters.search

    const response = await axios.get('/api/alerts/notification-channels', { params })
    channels.value = response.data || []
  } catch (error) {
    ElMessage.error('获取通知渠道列表失败')
  } finally {
    loading.value = false
  }
}

// 过滤条件改变
const handleFilterChange = () => {
  fetchChannels()
}

// 刷新数据
const refreshData = () => {
  fetchChannels()
}

// 打开创建对话框
const openCreateDialog = () => {
  dialogType.value = 'create'
  resetForm()
  dialogVisible.value = true
}

// 编辑渠道
const editChannel = (row) => {
  dialogType.value = 'edit'
  Object.assign(form, {
    ...row,
    config: { ...row.config }
  })
  dialogVisible.value = true
}

// 重置表单
const resetForm = () => {
  Object.assign(form, {
    name: '',
    description: '',
    channel_type: '',
    enabled: true,
    is_default: false,
    config: {},
    rate_limit: 100,
    retry_attempts: 3,
    timeout: 30
  })
  nextTick(() => {
    formRef.value?.clearValidate()
  })
}

// 渠道类型改变
const handleChannelTypeChange = (type) => {
  form.config = {}
  // 根据类型设置默认配置
  if (type === 'email') {
    form.config = {
      smtp_host: '',
      smtp_port: 587,
      username: '',
      password: '',
      use_tls: true
    }
  } else if (type === 'webhook') {
    form.config = {
      url: '',
      method: 'POST',
      content_type: 'application/json',
      secret: ''
    }
  } else if (type === 'dingtalk') {
    form.config = {
      webhook_url: '',
      secret: ''
    }
  } else if (type === 'sms') {
    form.config = {
      api_key: '',
      template_id: '',
      sign_name: ''
    }
  } else if (type === 'slack') {
    form.config = {
      webhook_url: '',
      channel: '#general'
    }
  }
}

// 提交表单
const submitForm = async () => {
  try {
    await formRef.value.validate()
    submitLoading.value = true

    const data = { ...form }
    
    if (dialogType.value === 'create') {
      await axios.post('/api/alerts/notification-channels', data)
      ElMessage.success('通知渠道创建成功')
    } else {
      await axios.put(`/api/alerts/notification-channels/${form.id}`, data)
      ElMessage.success('通知渠道更新成功')
    }

    dialogVisible.value = false
    fetchChannels()
  } catch (error) {
    if (error.errors) {
      ElMessage.error('表单验证失败，请检查输入')
    } else {
      ElMessage.error(dialogType.value === 'create' ? '创建失败' : '更新失败')
    }
  } finally {
    submitLoading.value = false
  }
}

// 状态切换
const handleStatusChange = async (row) => {
  row.updating = true
  try {
    await axios.put(`/api/alerts/notification-channels/${row.id}`, {
      enabled: row.enabled
    })
    ElMessage.success('状态更新成功')
  } catch (error) {
    row.enabled = !row.enabled // 恢复原状态
    ElMessage.error('状态更新失败')
  } finally {
    row.updating = false
  }
}

// 测试渠道
const testChannel = async (row) => {
  try {
    await axios.post(`/api/alerts/notification-channels/${row.id}/test`)
    ElMessage.success('测试通知已发送，请检查接收情况')
  } catch (error) {
    ElMessage.error('测试发送失败: ' + (error.message || '未知错误'))
  }
}

// 删除渠道
const deleteChannel = async (row) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除通知渠道「${row.name}」吗？此操作不可恢复。`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    await axios.delete(`/api/alerts/notification-channels/${row.id}`)
    ElMessage.success('删除成功')
    fetchChannels()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

// 辅助函数
const getChannelTypeLabel = (type) => {
  const labels = {
    email: '邮件',
    webhook: 'Webhook',
    dingtalk: '钉钉',
    sms: '短信',
    slack: 'Slack'
  }
  return labels[type] || type
}

const getChannelTypeTagType = (type) => {
  const types = {
    email: '',
    webhook: 'success',
    dingtalk: 'warning',
    sms: 'info',
    slack: 'danger'
  }
  return types[type] || ''
}

const getChannelTypeIcon = (type) => {
  const icons = {
    email: Message,
    webhook: Link,
    dingtalk: ChatDotRound,
    sms: Phone,
    slack: Monitor
  }
  return icons[type] || Message
}

const getChannelTypeColor = (type) => {
  const colors = {
    email: '#409EFF',
    webhook: '#67C23A',
    dingtalk: '#E6A23C',
    sms: '#909399',
    slack: '#F56C6C'
  }
  return colors[type] || '#409EFF'
}

const formatTime = (timeStr) => {
  if (!timeStr) return '-'
  return new Date(timeStr).toLocaleString('zh-CN')
}
</script>

<style scoped>
.notification-channels-page {
  padding: 0;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 20px;
  padding: 0 4px;
}

.header-left h1 {
  margin: 0 0 8px 0;
  font-size: 24px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.page-description {
  margin: 0;
  color: var(--el-text-color-regular);
  font-size: 14px;
}

.header-right {
  display: flex;
  gap: 12px;
}

.filter-card {
  margin-bottom: 20px;
}

.filter-container {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.filter-left {
  display: flex;
  gap: 16px;
}

.table-card {
  margin-bottom: 20px;
}

.channel-name {
  display: flex;
  align-items: center;
  gap: 8px;
}

.channel-icon {
  font-size: 16px;
}

.config-container {
  width: 100%;
  border: 1px solid var(--el-border-color-light);
  border-radius: 4px;
  padding: 16px;
  background-color: var(--el-bg-color-page);
}

.config-form {
  width: 100%;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

:deep(.el-form-item) {
  margin-bottom: 18px;
}

:deep(.el-form-item__label) {
  font-weight: 500;
}

:deep(.el-table) {
  font-size: 14px;
}

:deep(.el-table .cell) {
  padding: 8px 12px;
}
</style>