<template>
  <div class="notification-targets-page">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-left">
        <h2>{{ $t('notification.targets.title') }}</h2>
        <p class="page-description">{{ $t('notification.targets.description') }}</p>
      </div>
      <div class="header-actions">
        <el-button type="primary" @click="openCreateDialog">
          <el-icon>
            <Plus />
          </el-icon>
          {{ $t('notification.targets.createTarget') }}
        </el-button>
      </div>
    </div>

    <!-- 筛选栏 -->
    <div class="filter-bar">
      <el-form :model="filters" inline>
        <el-form-item :label="$t('notification.targets.targetType')">
          <el-select v-model="filters.target_type" :placeholder="$t('notification.targets.targetType')" clearable
            @change="loadTargets">
            <el-option :label="$t('notification.targets.targetTypes.email')" value="email" />
            <el-option :label="$t('notification.targets.targetTypes.sms')" value="sms" />
            <el-option :label="$t('notification.targets.targetTypes.webhook')" value="webhook" />
          </el-select>
        </el-form-item>
        <el-form-item :label="$t('notification.targets.targetName')">
          <el-input v-model="filters.keyword" :placeholder="$t('notification.targets.targetName')" clearable
            @keyup.enter="loadTargets">
            <template #prefix>
              <el-icon>
                <Search />
              </el-icon>
            </template>
          </el-input>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="loadTargets">
            <el-icon>
              <Search />
            </el-icon>
            {{ $t('common.search') }}
          </el-button>
          <el-button @click="resetFilter">{{ $t('common.reset') }}</el-button>
        </el-form-item>
      </el-form>
    </div>

    <!-- 对象列表 -->
    <div class="targets-container">
      <el-table :data="filteredTargets" style="width: 100%" @selection-change="handleSelectionChange"
        v-loading="loading">
        <el-table-column type="selection" width="55" />

        <el-table-column prop="name" :label="$t('notification.targets.targetName')" sortable>
          <template #default="{ row }">
            <el-link type="primary" @click="showTargetDetail(row)">
              {{ row.name }}
            </el-link>
          </template>
        </el-table-column>

        <el-table-column prop="target_type" :label="$t('notification.targets.targetType')" sortable>
          <template #default="{ row }">
            <el-tag :type="getTargetTypeTagType(row.target_type)" size="small">
              {{ getTargetTypeLabel(row.target_type) }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column :label="$t('notification.targets.targetStatus')" sortable>
          <template #default="{ row }">
            <el-tag :type="row.enabled ? 'success' : 'info'" size="small">
              {{ row.enabled ? $t('notification.targets.enabled') : $t('notification.targets.disabled') }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column :label="$t('alertPolicies.alertName')" sortable>
          <template #default="{ row }">
            <div v-if="row.alert_policies && row.alert_policies.length > 0">
              <el-tag v-for="policyId in row.alert_policies.slice(0, 2)" :key="policyId" size="small" type="warning"
                class="mr-1">
                {{ getAlertPolicyName(policyId) }}
              </el-tag>
              <el-tag v-if="row.alert_policies.length > 2" size="small" type="warning">
                +{{ row.alert_policies.length - 2 }}
              </el-tag>
            </div>
            <span v-else class="text-muted">{{ $t('common.noData') }}</span>
          </template>
        </el-table-column>

        <el-table-column :label="$t('notification.channels.title')" sortable>
          <template #default="{ row }">
            <div v-if="row.channels && row.channels.length > 0">
              <el-tag v-for="channelId in row.channels.slice(0, 2)" :key="channelId" size="small" type="success"
                class="mr-1">
                {{ getNotificationChannelName(channelId) }}
              </el-tag>
              <el-tag v-if="row.channels.length > 2" size="small" type="success">
                +{{ row.channels.length - 2 }}
              </el-tag>
            </div>
            <span v-else class="text-muted">{{ $t('common.noData') }}</span>
          </template>
        </el-table-column>

        <el-table-column :label="$t('notification.targets.targetAddress')" sortable>
          <template #default="{ row }">
            {{ getTargetAddress(row) }}
          </template>
        </el-table-column>

        <el-table-column prop="created_at" :label="$t('notification.targets.createTime')" sortable>
          <template #default="{ row }">
            <div class="time-display">
              <div>{{ formatDate(row.created_at).split(' ')[0] }}</div>
              <div class="time">{{ formatDate(row.created_at).split(' ')[1] }}</div>
            </div>
          </template>
        </el-table-column>

        <el-table-column :label="$t('notification.targets.actions')" width="200" fixed="right">
          <template #default="{ row }">
            <el-button size="small" :type="row.enabled ? 'warning' : 'success'" @click="toggleTarget(row)"
              :loading="row.toggling">
              {{ row.enabled ? $t('notification.targets.disabled') : $t('notification.targets.enabled') }}
            </el-button>
            <el-button size="small" @click="editTarget(row)">{{ $t('common.edit') }}</el-button>
            <el-button size="small" type="danger" @click="deleteTarget(row)">
              {{ $t('common.delete') }}
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <div v-if="filteredTargets.length === 0" class="empty-state">
        <el-empty :description="$t('notification.targets.noTargets')">
          <el-button type="primary" @click="openCreateDialog">{{ $t('notification.targets.createFirstTarget')
            }}</el-button>
        </el-empty>
      </div>
    </div>

    <!-- 创建/编辑弹窗 -->
    <el-dialog v-model="dialogVisible"
      :title="dialogMode === 'create' ? $t('notification.targets.createTarget') : $t('notification.targets.createTarget')"
      width="600px">
      <el-form :model="targetForm" label-width="100px">
        <el-form-item :label="$t('notification.targets.targetName')">
          <el-input v-model="targetForm.name" />
        </el-form-item>

        <el-form-item :label="$t('notification.targets.targetType')">
          <el-select v-model="targetForm.target_type" @change="handleTargetTypeChange">
            <el-option :label="$t('notification.targets.targetTypes.email')" value="email" />
            <el-option :label="$t('notification.targets.targetTypes.sms')" value="sms" />
            <el-option :label="$t('notification.targets.targetTypes.webhook')" value="webhook" />
          </el-select>
        </el-form-item>

        <!-- 邮件配置 -->
        <div v-if="targetForm.target_type === 'email'" class="email-config">
          <el-form-item :label="$t('notification.targets.targetConfig.email')">
            <el-input v-model="targetForm.target_config.email" placeholder="example@domain.com" />
          </el-form-item>
        </div>

        <!-- 短信配置 -->
        <div v-if="targetForm.target_type === 'sms'" class="sms-config">
          <el-form-item :label="$t('notification.targets.targetConfig.phone')">
            <el-input v-model="targetForm.target_config.phone" placeholder="13800138000" />
          </el-form-item>
        </div>

        <!-- WebHook配置 -->
        <div v-if="targetForm.target_type === 'webhook'" class="webhook-config">
          <el-form-item :label="$t('notification.targets.targetConfig.url')">
            <el-input v-model="targetForm.target_config.url" placeholder="https://example.com/webhook" />
          </el-form-item>
        </div>

        <el-form-item :label="$t('alertPolicies.alertName')">
          <el-select v-model="targetForm.alert_policies" multiple :placeholder="$t('alertPolicies.selectAlertPolicy')">
            <el-option v-for="policy in alertPolicies" :key="policy.id" :label="policy.name" :value="policy.id" />
          </el-select>
        </el-form-item>

        <el-form-item :label="$t('notification.channels.title')">
          <el-select v-model="targetForm.channels" multiple :placeholder="$t('notification.channels.selectChannel')">
            <el-option v-for="channel in notificationChannels" :key="channel.id" :label="channel.name"
              :value="channel.id" />
          </el-select>
        </el-form-item>

        <el-form-item :label="$t('common.description')">
          <el-input v-model="targetForm.description" type="textarea" />
        </el-form-item>

        <el-form-item :label="$t('notification.targets.targetStatus')">
          <el-switch v-model="targetForm.enabled" />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="dialogVisible = false">{{ $t('common.cancel') }}</el-button>
        <el-button type="primary" @click="submitTarget">{{ $t('common.save') }}</el-button>
      </template>
    </el-dialog>

    <!-- 对象详情侧拉抽屉 -->
    <el-drawer v-model="showTargetDetailDrawer" :title="$t('notification.targets.targetDetail')" direction="rtl"
      size="50%">
      <div v-if="selectedTarget" class="target-detail">
        <div class="detail-section">
          <h3>{{ $t('common.basicInfo') }}</h3>
          <div class="detail-item">
            <span class="label">{{ $t('notification.targets.targetName') }}:</span>
            <span class="value">{{ selectedTarget.name }}</span>
          </div>
          <div class="detail-item">
            <span class="label">{{ $t('notification.targets.targetType') }}:</span>
            <span class="value">
              <el-tag :type="getTargetTypeTagType(selectedTarget.target_type)" size="small">
                {{ getTargetTypeLabel(selectedTarget.target_type) }}
              </el-tag>
            </span>
          </div>
          <div class="detail-item">
            <span class="label">{{ $t('notification.targets.targetStatus') }}:</span>
            <span class="value">
              <el-tag :type="selectedTarget.enabled ? 'success' : 'info'" size="small">
                {{ selectedTarget.enabled ? $t('notification.targets.enabled') : $t('notification.targets.disabled') }}
              </el-tag>
            </span>
          </div>
          <div class="detail-item">
            <span class="label">{{ $t('common.description') }}:</span>
            <span class="value">{{ selectedTarget.description || $t('notification.targets.noDescription') }}</span>
          </div>
        </div>

        <div class="detail-section">
          <h3>{{ $t('common.configInfo') }}</h3>
          <div class="detail-item">
            <span class="label">{{ $t('notification.targets.targetAddress') }}:</span>
            <span class="value">{{ getTargetAddress(selectedTarget) }}</span>
          </div>
          <div class="detail-item" v-if="selectedTarget.target_config">
            <span class="label">{{ $t('common.details') }}:</span>
            <div class="value">
              <div v-for="(value, key) in selectedTarget.target_config" :key="key" class="config-item">
                <span class="config-key">{{ getConfigLabel(key) }}:</span>
                <span class="config-value">{{ value }}</span>
              </div>
            </div>
          </div>
        </div>

        <div class="detail-section">
          <h3>{{ $t('common.relatedInfo') }}</h3>
          <div class="detail-item">
            <span class="label">{{ $t('alertPolicies.alertName') }}:</span>
            <span class="value">{{ selectedTarget.alert_policies?.length || 0 }}{{ $t('common.count') }}</span>
          </div>
          <div class="detail-item" v-if="selectedTarget.alert_policies && selectedTarget.alert_policies.length > 0">
            <span class="label">{{ $t('alertPolicies.policyList') }}:</span>
            <div class="value">
              <el-tag v-for="policyId in selectedTarget.alert_policies" :key="policyId" size="small"
                style="margin-right: 8px; margin-bottom: 4px;">
                {{ getAlertPolicyName(policyId) }}
              </el-tag>
            </div>
          </div>
          <div class="detail-item">
            <span class="label">{{ $t('notification.channels.title') }}:</span>
            <span class="value">{{ selectedTarget.channels?.length || 0 }}{{ $t('common.count') }}</span>
          </div>
          <div class="detail-item" v-if="selectedTarget.channels && selectedTarget.channels.length > 0">
            <span class="label">{{ $t('notification.channels.channelList') }}:</span>
            <div class="value">
              <el-tag v-for="channelId in selectedTarget.channels" :key="channelId" size="small"
                style="margin-right: 8px; margin-bottom: 4px;">
                {{ getNotificationChannelName(channelId) }}
              </el-tag>
            </div>
          </div>
        </div>

        <div class="detail-section">
          <h3>{{ $t('common.otherInfo') }}</h3>
          <div class="detail-item">
            <span class="label">{{ $t('notification.targets.createTime') }}:</span>
            <span class="value">{{ formatDate(selectedTarget.created_at) }}</span>
          </div>
          <div class="detail-item">
            <span class="label">{{ $t('common.updateTime') }}:</span>
            <span class="value">{{ formatDate(selectedTarget.updated_at) }}</span>
          </div>
        </div>

        <div class="detail-actions">
          <el-button type="primary" @click="editTarget(selectedTarget)">{{ $t('notification.targets.editTarget')
            }}</el-button>
          <el-button :type="selectedTarget.enabled ? 'warning' : 'success'" @click="toggleTarget(selectedTarget)"
            :loading="selectedTarget.toggling">
            {{ selectedTarget.enabled ? $t('notification.targets.disable') : $t('notification.targets.enable') }}
          </el-button>
          <el-button type="danger" @click="deleteTarget(selectedTarget)">
            {{ $t('notification.targets.deleteTarget') }}
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
import { useI18n } from 'vue-i18n'
import axios from 'axios'

const { t } = useI18n()

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
    ElMessage.error(t('notification.targets.messages.getTargetsFailed'))
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
      ElMessage.success(t('notification.targets.messages.createSuccess'))
    } else {
      await axios.put(`/api/notifications/targets/${editingTarget.value.id}`, targetForm)
      ElMessage.success(t('notification.targets.messages.updateSuccess'))
    }

    dialogVisible.value = false
    fetchTargets()
  } catch (error) {
    ElMessage.error(dialogMode.value === 'create' ? t('notification.targets.messages.createFailed') : t('notification.targets.messages.updateFailed'))
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
    ElMessage.success(t('notification.targets.messages.updateSuccess'))
  } catch (error) {
    target.enabled = !target.enabled
    ElMessage.error(t('notification.targets.messages.updateFailed'))
  } finally {
    target.toggling = false
  }
}

const deleteTarget = async (target) => {
  try {
    await ElMessageBox.confirm(
      t('notification.targets.messages.confirmDelete', { name: target.name }),
      t('common.confirmDelete'),
      {
        type: 'warning',
        confirmButtonText: t('common.confirmDelete'),
        cancelButtonText: t('common.cancel')
      }
    )

    await axios.delete(`/api/notifications/targets/${target.id}`)
    ElMessage.success(t('notification.targets.messages.deleteSuccess'))
    fetchTargets()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(t('notification.targets.messages.deleteFailed'))
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
    email: t('notification.targets.targetTypes.email'),
    sms: t('notification.targets.targetTypes.sms'),
    webhook: t('notification.targets.targetTypes.webhook')
  }
  return labelMap[targetType] || targetType
}

const getTargetAddress = (target) => {
  if (target.target_type === 'email') {
    return target.target_config?.email || t('common.notConfigured')
  } else if (target.target_type === 'sms') {
    return target.target_config?.phone || t('common.notConfigured')
  } else if (target.target_type === 'webhook') {
    return target.target_config?.url || t('common.notConfigured')
  }
  return t('common.notConfigured')
}

const getConfigLabel = (key) => {
  const labelMap = {
    email: t('notification.targets.targetConfig.email'),
    phone: t('notification.targets.targetConfig.phone'),
    url: t('notification.targets.targetConfig.url')
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