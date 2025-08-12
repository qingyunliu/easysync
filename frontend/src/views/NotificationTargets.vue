<template>
  <div class="notification-targets-page">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-left">
        <h2>通知对象</h2>
        <p class="page-description">管理系统通知对象，支持邮件、短信、WebHook等多种通知方式</p>
      </div>
      <div class="header-actions">
        <el-button type="primary" @click="openCreateDialog">
          <el-icon><Plus /></el-icon>
          创建通知对象
        </el-button>
      </div>
    </div>

    <!-- 筛选栏 -->
    <div class="filter-bar">
      <el-form :model="filters" inline>
        <el-form-item label="对象类型">
          <el-select v-model="filters.target_type" placeholder="选择对象类型" clearable @change="loadTargets">
            <el-option label="邮件" value="email" />
            <el-option label="短信" value="sms" />
            <el-option label="WebHook" value="webhook" />
          </el-select>
        </el-form-item>
        <el-form-item label="对象名称">
          <el-input
            v-model="filters.keyword"
            placeholder="搜索对象名称"
            clearable
            @keyup.enter="loadTargets"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="loadTargets">
            <el-icon><Search /></el-icon>
            搜索
          </el-button>
          <el-button @click="resetFilter">重置</el-button>
        </el-form-item>
      </el-form>
    </div>

    <!-- 对象列表 -->
    <div class="targets-container">
      <el-table 
        :data="filteredTargets" 
        style="width: 100%"
        @selection-change="handleSelectionChange"
        v-loading="loading"
      >
        <el-table-column type="selection" width="55" />
        
        <el-table-column prop="name" label="对象名称" sortable>
          <template #default="{ row }">
            <el-link type="primary" @click="showTargetDetail(row)">
              {{ row.name }}
            </el-link>
          </template>
        </el-table-column>
        
        <el-table-column prop="target_type" label="对象类型" sortable>
          <template #default="{ row }">
            <el-tag :type="getTargetTypeTagType(row.target_type)" size="small">
              {{ getTargetTypeLabel(row.target_type) }}
            </el-tag>
          </template>
        </el-table-column>
        
        <el-table-column label="对象状态" sortable>
          <template #default="{ row }">
            <el-tag :type="row.enabled ? 'success' : 'info'" size="small">
              {{ row.enabled ? '启用' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        
        <el-table-column label="关联告警器" sortable>
          <template #default="{ row }">
            <div v-if="row.alert_policies && row.alert_policies.length > 0">
              <el-tag 
                v-for="policyId in row.alert_policies.slice(0, 2)" 
                :key="policyId"
                size="small"
                type="warning"
                class="mr-1"
              >
                {{ getAlertPolicyName(policyId) }}
              </el-tag>
              <el-tag v-if="row.alert_policies.length > 2" size="small" type="warning">
                +{{ row.alert_policies.length - 2 }}
              </el-tag>
            </div>
            <span v-else class="text-muted">无</span>
          </template>
        </el-table-column>
        
        <el-table-column label="发送通道" sortable>
          <template #default="{ row }">
            <div v-if="row.channels && row.channels.length > 0">
              <el-tag 
                v-for="channelId in row.channels.slice(0, 2)" 
                :key="channelId"
                size="small"
                type="success"
                class="mr-1"
              >
                {{ getNotificationChannelName(channelId) }}
              </el-tag>
              <el-tag v-if="row.channels.length > 2" size="small" type="success">
                +{{ row.channels.length - 2 }}
              </el-tag>
            </div>
            <span v-else class="text-muted">无</span>
          </template>
        </el-table-column>
        
        <el-table-column label="通知地址" sortable>
          <template #default="{ row }">
            {{ getTargetAddress(row) }}
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
              @click="toggleTarget(row)"
              :loading="row.toggling"
            >
              {{ row.enabled ? '禁用' : '启用' }}
            </el-button>
            <el-button size="small" @click="editTarget(row)">编辑</el-button>
            <el-button 
              size="small" 
              type="danger" 
              @click="deleteTarget(row)"
            >
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
      
      <div v-if="filteredTargets.length === 0" class="empty-state">
        <el-empty description="暂无通知对象">
          <el-button type="primary" @click="openCreateDialog">创建第一个通知对象</el-button>
        </el-empty>
      </div>
    </div>

    <!-- 创建/编辑弹窗 -->
    <el-dialog v-model="dialogVisible" :title="dialogMode === 'create' ? '创建通知对象' : '编辑通知对象'" width="600px">
      <el-form :model="targetForm" label-width="100px">
        <el-form-item label="对象名称">
          <el-input v-model="targetForm.name" />
        </el-form-item>
        
        <el-form-item label="对象类型">
          <el-select v-model="targetForm.target_type" @change="handleTargetTypeChange">
            <el-option label="邮件" value="email" />
            <el-option label="短信" value="sms" />
            <el-option label="WebHook" value="webhook" />
          </el-select>
        </el-form-item>
        
        <!-- 邮件配置 -->
        <div v-if="targetForm.target_type === 'email'" class="email-config">
          <el-form-item label="邮箱地址">
            <el-input v-model="targetForm.target_config.email" placeholder="example@domain.com" />
          </el-form-item>
        </div>
        
        <!-- 短信配置 -->
        <div v-if="targetForm.target_type === 'sms'" class="sms-config">
          <el-form-item label="手机号码">
            <el-input v-model="targetForm.target_config.phone" placeholder="13800138000" />
          </el-form-item>
        </div>
        
        <!-- WebHook配置 -->
        <div v-if="targetForm.target_type === 'webhook'" class="webhook-config">
          <el-form-item label="URL">
            <el-input v-model="targetForm.target_config.url" placeholder="https://example.com/webhook" />
          </el-form-item>
        </div>
        
        <el-form-item label="关联告警器">
          <el-select v-model="targetForm.alert_policies" multiple placeholder="选择关联的告警器">
            <el-option 
              v-for="policy in alertPolicies" 
              :key="policy.id" 
              :label="policy.name" 
              :value="policy.id" 
            />
          </el-select>
        </el-form-item>
        
        <el-form-item label="发送通道">
          <el-select v-model="targetForm.channels" multiple placeholder="选择发送通道">
            <el-option 
              v-for="channel in notificationChannels" 
              :key="channel.id" 
              :label="channel.name" 
              :value="channel.id" 
            />
          </el-select>
        </el-form-item>
        
        <el-form-item label="描述">
          <el-input v-model="targetForm.description" type="textarea" />
        </el-form-item>
        
        <el-form-item label="启用状态">
          <el-switch v-model="targetForm.enabled" />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitTarget">保存</el-button>
      </template>
    </el-dialog>

    <!-- 对象详情侧拉抽屉 -->
    <el-drawer
      v-model="showTargetDetailDrawer"
      title="对象详情"
      direction="rtl"
      size="50%"
    >
      <div v-if="selectedTarget" class="target-detail">
        <div class="detail-section">
          <h3>基本信息</h3>
          <div class="detail-item">
            <span class="label">对象名称:</span>
            <span class="value">{{ selectedTarget.name }}</span>
          </div>
          <div class="detail-item">
            <span class="label">对象类型:</span>
            <span class="value">
              <el-tag :type="getTargetTypeTagType(selectedTarget.target_type)" size="small">
                {{ getTargetTypeLabel(selectedTarget.target_type) }}
              </el-tag>
            </span>
          </div>
          <div class="detail-item">
            <span class="label">对象状态:</span>
            <span class="value">
              <el-tag :type="selectedTarget.enabled ? 'success' : 'info'" size="small">
                {{ selectedTarget.enabled ? '启用' : '禁用' }}
              </el-tag>
            </span>
          </div>
          <div class="detail-item">
            <span class="label">对象描述:</span>
            <span class="value">{{ selectedTarget.description || '暂无描述' }}</span>
          </div>
        </div>

        <div class="detail-section">
          <h3>配置信息</h3>
          <div class="detail-item">
            <span class="label">通知地址:</span>
            <span class="value">{{ getTargetAddress(selectedTarget) }}</span>
          </div>
          <div class="detail-item" v-if="selectedTarget.target_config">
            <span class="label">详细配置:</span>
            <div class="value">
              <div v-for="(value, key) in selectedTarget.target_config" :key="key" class="config-item">
                <span class="config-key">{{ getConfigLabel(key) }}:</span>
                <span class="config-value">{{ value }}</span>
              </div>
            </div>
          </div>
        </div>

        <div class="detail-section">
          <h3>关联信息</h3>
          <div class="detail-item">
            <span class="label">关联告警器:</span>
            <span class="value">{{ selectedTarget.alert_policies?.length || 0 }}个</span>
          </div>
          <div class="detail-item" v-if="selectedTarget.alert_policies && selectedTarget.alert_policies.length > 0">
            <span class="label">告警器列表:</span>
            <div class="value">
              <el-tag 
                v-for="policyId in selectedTarget.alert_policies" 
                :key="policyId"
                size="small"
                style="margin-right: 8px; margin-bottom: 4px;"
              >
                {{ getAlertPolicyName(policyId) }}
              </el-tag>
            </div>
          </div>
          <div class="detail-item">
            <span class="label">发送通道:</span>
            <span class="value">{{ selectedTarget.channels?.length || 0 }}个</span>
          </div>
          <div class="detail-item" v-if="selectedTarget.channels && selectedTarget.channels.length > 0">
            <span class="label">通道列表:</span>
            <div class="value">
              <el-tag 
                v-for="channelId in selectedTarget.channels" 
                :key="channelId"
                size="small"
                style="margin-right: 8px; margin-bottom: 4px;"
              >
                {{ getNotificationChannelName(channelId) }}
              </el-tag>
            </div>
          </div>
        </div>

        <div class="detail-section">
          <h3>其他信息</h3>
          <div class="detail-item">
            <span class="label">创建时间:</span>
            <span class="value">{{ formatDate(selectedTarget.created_at) }}</span>
          </div>
          <div class="detail-item">
            <span class="label">更新时间:</span>
            <span class="value">{{ formatDate(selectedTarget.updated_at) }}</span>
          </div>
        </div>

        <div class="detail-actions">
          <el-button type="primary" @click="editTarget(selectedTarget)">编辑对象</el-button>
          <el-button 
            :type="selectedTarget.enabled ? 'warning' : 'success'"
            @click="toggleTarget(selectedTarget)"
            :loading="selectedTarget.toggling"
          >
            {{ selectedTarget.enabled ? '禁用' : '启用' }}
          </el-button>
          <el-button 
            type="danger" 
            @click="deleteTarget(selectedTarget)"
          >
            删除对象
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
const targets = ref([])
const alertPolicies = ref([])
const notificationChannels = ref([])
const dialogVisible = ref(false)
const dialogMode = ref('create')
const editingTarget = ref(null)
const showTargetDetailDrawer = ref(false)
const selectedTarget = ref(null)

// 筛选表单
const filters = reactive({
  target_type: '',
  keyword: ''
})

const targetForm = reactive({
  name: '',
  target_type: 'email',
  enabled: true,
  description: '',
  alert_policies: [],
  channels: [],
  target_config: {}
})

// 计算属性
const filteredTargets = computed(() => {
  let result = targets.value
  
  if (filters.target_type) {
    result = result.filter(target => target.target_type === filters.target_type)
  }
  
  if (filters.keyword) {
    const keyword = filters.keyword.toLowerCase()
    result = result.filter(target => 
      target.name.toLowerCase().includes(keyword) ||
      target.target_type.toLowerCase().includes(keyword)
    )
  }
  
  return result
})

onMounted(() => {
  fetchTargets()
  fetchAlertPolicies()
  fetchNotificationChannels()
})

const fetchTargets = async () => {
  try {
    loading.value = true
    const response = await axios.get('/api/notifications/targets')
    targets.value = response.data.targets || []
  } catch (error) {
    ElMessage.error('获取通知对象失败')
  } finally {
    loading.value = false
  }
}

const loadTargets = () => {
  fetchTargets()
}

const resetFilter = () => {
  filters.target_type = ''
  filters.keyword = ''
  loadTargets()
}

const showTargetDetail = (target) => {
  selectedTarget.value = target
  showTargetDetailDrawer.value = true
}

const fetchAlertPolicies = async () => {
  try {
    const response = await axios.get('/api/alerts/policies')
    alertPolicies.value = response.data.policies || []
  } catch (error) {
    console.error('获取告警策略失败:', error)
  }
}

const fetchNotificationChannels = async () => {
  try {
    const response = await axios.get('/api/notifications/channels')
    notificationChannels.value = response.data.channels || []
  } catch (error) {
    console.error('获取通知渠道失败:', error)
  }
}

// 获取告警策略名称
const getAlertPolicyName = (policyId) => {
  const policy = alertPolicies.value.find(p => p.id === policyId)
  return policy ? policy.name : policyId
}

// 获取通知渠道名称
const getNotificationChannelName = (channelId) => {
  const channel = notificationChannels.value.find(c => c.id === channelId)
  return channel ? channel.name : channelId
}

const openCreateDialog = () => {
  dialogMode.value = 'create'
  editingTarget.value = null
  resetTargetForm()
  dialogVisible.value = true
}

const resetTargetForm = () => {
  Object.assign(targetForm, {
    name: '',
    target_type: 'email',
    enabled: true,
    description: '',
    alert_policies: [],
    channels: [],
    target_config: {}
  })
}

const handleTargetTypeChange = () => {
  // 根据对象类型重置配置
  targetForm.target_config = {}
  
  if (targetForm.target_type === 'email') {
    targetForm.target_config = {
      email: ''
    }
  } else if (targetForm.target_type === 'sms') {
    targetForm.target_config = {
      phone: ''
    }
  } else if (targetForm.target_type === 'webhook') {
    targetForm.target_config = {
      url: ''
    }
  }
}

const submitTarget = async () => {
  try {
    if (dialogMode.value === 'create') {
      await axios.post('/api/notifications/targets', targetForm)
      ElMessage.success('通知对象创建成功')
    } else {
      await axios.put(`/api/notifications/targets/${editingTarget.value.id}`, targetForm)
      ElMessage.success('通知对象更新成功')
    }
    
    dialogVisible.value = false
    fetchTargets()
  } catch (error) {
    ElMessage.error(dialogMode.value === 'create' ? '创建通知对象失败' : '更新通知对象失败')
  }
}

const editTarget = (target) => {
  dialogMode.value = 'edit'
  editingTarget.value = target
  
  Object.assign(targetForm, {
    name: target.name,
    target_type: target.target_type,
    enabled: target.enabled,
    description: target.description,
    alert_policies: target.alert_policies || [],
    channels: target.channels || [],
    target_config: { ...target.target_config }
  })
  
  dialogVisible.value = true
}

const toggleTarget = async (target) => {
  try {
    target.toggling = true
    await axios.put(`/api/notifications/targets/${target.id}`, { enabled: target.enabled })
    ElMessage.success(`通知对象已${target.enabled ? '启用' : '禁用'}`)
  } catch (error) {
    target.enabled = !target.enabled
    ElMessage.error('更新状态失败')
  } finally {
    target.toggling = false
  }
}

const deleteTarget = async (target) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除通知对象"${target.name}"吗？此操作不可恢复。`,
      '确认删除',
      {
        type: 'warning',
        confirmButtonText: '确定删除',
        cancelButtonText: '取消'
      }
    )
    
    await axios.delete(`/api/notifications/targets/${target.id}`)
    ElMessage.success('通知对象删除成功')
    fetchTargets()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除通知对象失败')
    }
  }
}

const getTargetTypeTagType = (targetType) => {
  const typeMap = {
    email: 'primary',
    sms: 'success',
    webhook: 'warning'
  }
  return typeMap[targetType] || 'info'
}

const getTargetTypeLabel = (targetType) => {
  const labelMap = {
    email: '邮件',
    sms: '短信',
    webhook: 'WebHook'
  }
  return labelMap[targetType] || targetType
}

const getTargetAddress = (target) => {
  if (target.target_type === 'email') {
    return target.target_config?.email || '未配置'
  } else if (target.target_type === 'sms') {
    return target.target_config?.phone || '未配置'
  } else if (target.target_type === 'webhook') {
    return target.target_config?.url || '未配置'
  }
  return '未配置'
}

const getConfigLabel = (key) => {
  const labelMap = {
    email: '邮箱地址',
    phone: '手机号码',
    url: 'URL'
  }
  return labelMap[key] || key
}

const formatDate = (date) => {
  if (!date) return '-'
  return new Date(date).toLocaleString('zh-CN')
}
</script>

<style scoped>
.mr-1 {
  margin-right: 4px;
}

.text-muted {
  color: #909399;
}
.notification-targets-page {
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

.targets-container {
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

.empty-state {
  text-align: center;
  padding: 60px 20px;
}

/* 侧拉抽屉样式 */
.target-detail {
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

.config-item {
  display: flex;
  margin-bottom: 8px;
  padding: 8px;
  background: var(--card-bg);
  border-radius: 4px;
}

.config-key {
  font-weight: 500;
  margin-right: 8px;
  color: var(--text-color);
}

.config-value {
  color: var(--text-color);
  font-family: monospace;
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
.webhook-config {
  border: 1px solid var(--border-color);
  border-radius: 6px;
  padding: 16px;
  margin-bottom: 16px;
  background: var(--card-bg);
}
</style>