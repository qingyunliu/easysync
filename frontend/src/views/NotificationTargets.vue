<template>
  <div class="notification-targets-page">
    <div class="page-header">
      <h1>通知对象</h1>
      <el-button type="primary" @click="openCreateDialog">创建通知对象</el-button>
    </div>

    <el-card>
      <div v-loading="loading">
        <div v-if="targets.length === 0" class="empty-state">
          <el-empty description="暂无通知对象">
            <el-button type="primary" @click="openCreateDialog">创建第一个通知对象</el-button>
          </el-empty>
        </div>
        
        <div v-else class="targets-grid">
          <div v-for="target in targets" :key="target.id" class="target-card">
            <div class="target-header">
              <h3>{{ target.name }}</h3>
              <div class="target-tags">
                <el-tag :type="getTargetTypeTagType(target.target_type)" size="small">
                  {{ getTargetTypeLabel(target.target_type) }}
                </el-tag>
              </div>
            </div>
            <div class="target-content">
              <p class="target-description">{{ target.description || '暂无描述' }}</p>
              <div class="target-config">
                <div class="config-item">
                  <span class="config-label">关联告警器:</span>
                  <span class="config-value">{{ target.alert_policies?.length || 0 }}个</span>
                </div>
                <div class="config-item">
                  <span class="config-label">发送通道:</span>
                  <span class="config-value">{{ target.channels?.length || 0 }}个</span>
                </div>
                <div class="config-item">
                  <span class="config-label">通知地址:</span>
                  <span class="config-value">{{ getTargetAddress(target) }}</span>
                </div>
              </div>
            </div>
            <div class="target-footer">
              <el-switch v-model="target.enabled" @change="toggleTarget(target)" />
              <div class="target-actions">
                <el-button type="text" size="small" @click="editTarget(target)">编辑</el-button>
                <el-button type="text" size="small" @click="deleteTarget(target)" style="color: #f56c6c">删除</el-button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </el-card>

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
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import axios from 'axios'

const loading = ref(false)
const targets = ref([])
const alertPolicies = ref([])
const notificationChannels = ref([])
const dialogVisible = ref(false)
const dialogMode = ref('create')
const editingTarget = ref(null)

const targetForm = reactive({
  name: '',
  target_type: 'email',
  enabled: true,
  description: '',
  alert_policies: [],
  channels: [],
  target_config: {}
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
    targets.value = response.data.targets
  } catch (error) {
    ElMessage.error('获取通知对象失败')
  } finally {
    loading.value = false
  }
}

const fetchAlertPolicies = async () => {
  try {
    const response = await axios.get('/api/alerts/policies')
    alertPolicies.value = response.data.policies
  } catch (error) {
    console.error('获取告警策略失败:', error)
  }
}

const fetchNotificationChannels = async () => {
  try {
    const response = await axios.get('/api/notifications/channels')
    notificationChannels.value = response.data.channels
  } catch (error) {
    console.error('获取通知渠道失败:', error)
  }
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
    await axios.put(`/api/notifications/targets/${target.id}`, { enabled: target.enabled })
    ElMessage.success(`通知对象已${target.enabled ? '启用' : '禁用'}`)
  } catch (error) {
    target.enabled = !target.enabled
    ElMessage.error('更新状态失败')
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
</script>

<style scoped>
.notification-targets-page {
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

.targets-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  gap: 20px;
}

.target-card {
  padding: 16px;
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  background: #fff;
}

.target-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 12px;
}

.target-header h3 {
  margin: 0;
  font-size: 16px;
}

.target-tags {
  display: flex;
  gap: 8px;
}

.target-content {
  margin-bottom: 16px;
}

.target-description {
  margin: 0 0 12px 0;
  color: #606266;
  font-size: 14px;
}

.target-config {
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

.target-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 12px;
  border-top: 1px solid #f0f0f0;
}

.target-actions {
  display: flex;
  gap: 8px;
}

.empty-state {
  padding: 40px 0;
  text-align: center;
}

.email-config,
.sms-config,
.webhook-config {
  border: 1px solid #e4e7ed;
  border-radius: 6px;
  padding: 16px;
  margin-bottom: 16px;
  background: #fafafa;
}
</style>