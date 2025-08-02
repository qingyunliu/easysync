<template>
  <div class="alert-policies-page">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-left">
        <h1>告警策略</h1>
        <p class="page-description">配置和管理系统告警规则，定义触发条件和通知方式</p>
      </div>
      <div class="header-right">
        <el-button type="primary" @click="openCreateDialog">
          <el-icon><Plus /></el-icon>
          创建策略
        </el-button>
        <el-button @click="showTemplates">
          <el-icon><Document /></el-icon>
          模板库
        </el-button>
      </div>
    </div>

    <!-- 过滤器 -->
    <el-card class="filter-card" shadow="never">
      <div class="filter-container">
        <div class="filter-left">
          <el-select v-model="filters.category" placeholder="策略分类" style="width: 140px" @change="handleFilterChange">
            <el-option label="全部分类" value="" />
            <el-option label="系统监控" value="system" />
            <el-option label="任务监控" value="task" />
            <el-option label="存储监控" value="storage" />
            <el-option label="节点监控" value="node" />
            <el-option label="客户端监控" value="client" />
          </el-select>
          
          <el-select v-model="filters.severity" placeholder="告警级别" style="width: 120px" @change="handleFilterChange">
            <el-option label="全部级别" value="" />
            <el-option label="信息" value="info" />
            <el-option label="警告" value="warning" />
            <el-option label="错误" value="error" />
            <el-option label="严重" value="critical" />
          </el-select>
          
          <el-select v-model="filters.enabled" placeholder="启用状态" style="width: 120px" @change="handleFilterChange">
            <el-option label="全部状态" value="" />
            <el-option label="已启用" value="true" />
            <el-option label="已禁用" value="false" />
          </el-select>
        </div>
        
        <div class="filter-right">
          <el-input
            v-model="filters.keyword"
            placeholder="搜索策略名称"
            style="width: 250px"
            @input="handleSearch"
            clearable
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
          <el-button @click="refreshPolicies" :loading="loading">
            <el-icon><Refresh /></el-icon>
            刷新
          </el-button>
        </div>
      </div>
    </el-card>

    <!-- 策略列表 -->
    <el-card class="policies-card">
      <div v-loading="loading" class="policies-container">
        <div v-if="policies.length === 0" class="empty-state">
          <el-empty description="暂无告警策略">
            <el-button type="primary" @click="openCreateDialog">创建第一个策略</el-button>
          </el-empty>
        </div>
        
        <div v-else class="policies-grid">
          <div 
            v-for="policy in policies" 
            :key="policy.id"
            class="policy-card"
            @click="viewPolicy(policy)"
          >
            <div class="policy-header">
              <div class="policy-title">
                <h3>{{ policy.name }}</h3>
                <el-tag 
                  :type="getSeverityTagType(policy.severity)" 
                  size="small"
                >
                  {{ getSeverityLabel(policy.severity) }}
                </el-tag>
              </div>
              <div class="policy-actions">
                <el-switch
                  v-model="policy.enabled"
                  @change="togglePolicy(policy)"
                  @click.stop
                />
                <el-dropdown @command="(cmd) => handlePolicyAction(cmd, policy)" trigger="click" @click.stop>
                  <el-button type="text" size="small">
                    <el-icon><MoreFilled /></el-icon>
                  </el-button>
                  <template #dropdown>
                    <el-dropdown-menu>
                      <el-dropdown-item command="edit">
                        <el-icon><Edit /></el-icon>
                        编辑
                      </el-dropdown-item>
                      <el-dropdown-item command="copy">
                        <el-icon><CopyDocument /></el-icon>
                        复制
                      </el-dropdown-item>
                      <el-dropdown-item command="test">
                        <el-icon><VideoPlay /></el-icon>
                        测试
                      </el-dropdown-item>
                      <el-dropdown-item command="delete" divided>
                        <el-icon><Delete /></el-icon>
                        删除
                      </el-dropdown-item>
                    </el-dropdown-menu>
                  </template>
                </el-dropdown>
              </div>
            </div>
            
            <div class="policy-content">
              <p class="policy-description">{{ policy.description || '暂无描述' }}</p>
              
              <div class="policy-info">
                <div class="info-item">
                  <span class="info-label">分类:</span>
                  <el-tag size="small" type="info">{{ getCategoryLabel(policy.category) }}</el-tag>
                </div>
                <div class="info-item">
                  <span class="info-label">规则数:</span>
                  <span class="info-value">{{ policy.rules_count || 0 }}</span>
                </div>
                <div class="info-item">
                  <span class="info-label">重复间隔:</span>
                  <span class="info-value">{{ formatInterval(policy.repeat_interval) }}</span>
                </div>
              </div>
              
              <div class="policy-conditions" v-if="policy.conditions">
                <div class="conditions-title">触发条件:</div>
                <div class="conditions-content">
                  {{ formatConditions(policy.conditions) }}
                </div>
              </div>
            </div>
            
            <div class="policy-footer">
              <div class="policy-meta">
                <span class="meta-item">
                  <el-icon><User /></el-icon>
                  {{ policy.username }}
                </span>
                <span class="meta-item">
                  <el-icon><Clock /></el-icon>
                  {{ formatTime(policy.created_at) }}
                </span>
              </div>
              <div class="policy-status">
                <el-tag 
                  :type="policy.enabled ? 'success' : 'info'" 
                  size="small"
                  effect="plain"
                >
                  {{ policy.enabled ? '已启用' : '已禁用' }}
                </el-tag>
              </div>
            </div>
          </div>
        </div>
        
        <!-- 分页 -->
        <div v-if="pagination.total > 0" class="pagination">
          <el-pagination
            v-model:current-page="pagination.current_page"
            v-model:page-size="pagination.per_page"
            :page-sizes="[12, 24, 48]"
            :total="pagination.total"
            layout="total, sizes, prev, pager, next"
            @size-change="handlePageSizeChange"
            @current-change="handleCurrentChange"
          />
        </div>
      </div>
    </el-card>

    <!-- 创建/编辑策略弹窗 -->
    <el-dialog 
      v-model="policyDialog.visible" 
      :title="policyDialog.mode === 'create' ? '创建告警策略' : '编辑告警策略'"
      width="800px"
      @close="handleDialogClose"
    >
      <el-form 
        ref="policyFormRef" 
        :model="policyForm" 
        :rules="policyRules" 
        label-width="100px"
      >
        <el-form-item label="策略名称" prop="name">
          <el-input v-model="policyForm.name" placeholder="请输入策略名称" />
        </el-form-item>
        
        <el-form-item label="策略描述" prop="description">
          <el-input 
            v-model="policyForm.description" 
            type="textarea" 
            :rows="2"
            placeholder="请输入策略描述"
          />
        </el-form-item>
        
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="策略分类" prop="category">
              <el-select v-model="policyForm.category" placeholder="选择分类">
                <el-option label="系统监控" value="system" />
                <el-option label="任务监控" value="task" />
                <el-option label="存储监控" value="storage" />
                <el-option label="节点监控" value="node" />
                <el-option label="客户端监控" value="client" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="告警级别" prop="severity">
              <el-select v-model="policyForm.severity" placeholder="选择级别">
                <el-option label="信息" value="info" />
                <el-option label="警告" value="warning" />
                <el-option label="错误" value="error" />
                <el-option label="严重" value="critical" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="重复间隔" prop="repeat_interval">
              <el-input-number 
                v-model="policyForm.repeat_interval" 
                :min="60" 
                :max="86400"
                placeholder="秒"
                style="width: 100%"
              />
              <div class="form-help">通知重复发送的间隔时间（秒）</div>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="最大告警数" prop="max_alerts">
              <el-input-number 
                v-model="policyForm.max_alerts" 
                :min="1" 
                :max="100"
                style="width: 100%"
              />
              <div class="form-help">单次触发的最大告警数量</div>
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-form-item label="启用状态">
          <el-switch v-model="policyForm.enabled" />
          <span class="switch-label">{{ policyForm.enabled ? '启用' : '禁用' }}</span>
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="policyDialog.visible = false">取消</el-button>
        <el-button type="primary" @click="submitPolicy" :loading="submitting">
          {{ policyDialog.mode === 'create' ? '创建' : '更新' }}
        </el-button>
      </template>
    </el-dialog>

    <!-- 模板库弹窗 -->
    <el-dialog v-model="templateDialog.visible" title="策略模板库" width="900px">
      <div class="templates-grid">
        <div 
          v-for="template in templates" 
          :key="template.id"
          class="template-card"
          @click="selectTemplate(template)"
        >
          <div class="template-header">
            <h4>{{ template.name }}</h4>
            <el-tag :type="getCategoryTagType(template.category)" size="small">
              {{ getCategoryLabel(template.category) }}
            </el-tag>
          </div>
          <p class="template-description">{{ template.description }}</p>
          <div class="template-config">
            <div class="config-item">
              <span class="config-label">指标:</span>
              <span class="config-value">{{ template.template.conditions.metric }}</span>
            </div>
            <div class="config-item">
              <span class="config-label">条件:</span>
              <span class="config-value">
                {{ template.template.conditions.operator }} {{ template.template.conditions.threshold }}
              </span>
            </div>
          </div>
        </div>
      </div>
      
      <template #footer>
        <el-button @click="templateDialog.visible = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Plus,
  Document,
  Search,
  Refresh,
  MoreFilled,
  Edit,
  CopyDocument,
  VideoPlay,
  Delete,
  User,
  Clock
} from '@element-plus/icons-vue'
import axios from 'axios'

// 响应式数据
const loading = ref(false)
const submitting = ref(false)
const policies = ref([])
const templates = ref([])

// 过滤器
const filters = reactive({
  category: '',
  severity: '',
  enabled: '',
  keyword: ''
})

// 分页
const pagination = reactive({
  current_page: 1,
  per_page: 12,
  total: 0
})

// 策略弹窗
const policyDialog = reactive({
  visible: false,
  mode: 'create',
  editingPolicy: null
})

const policyForm = reactive({
  name: '',
  description: '',
  category: '',
  severity: 'warning',
  repeat_interval: 3600,
  max_alerts: 10,
  enabled: true
})

const policyRules = {
  name: [
    { required: true, message: '请输入策略名称', trigger: 'blur' }
  ],
  category: [
    { required: true, message: '请选择策略分类', trigger: 'change' }
  ],
  severity: [
    { required: true, message: '请选择告警级别', trigger: 'change' }
  ]
}

// 模板弹窗
const templateDialog = reactive({
  visible: false
})

// 表单引用
const policyFormRef = ref(null)

// 生命周期
onMounted(() => {
  fetchPolicies()
  fetchTemplates()
})

// 方法
const fetchPolicies = async () => {
  try {
    loading.value = true
    const params = {
      page: pagination.current_page,
      per_page: pagination.per_page,
      ...filters
    }
    
    // 过滤空值
    Object.keys(params).forEach(key => {
      if (params[key] === '' || params[key] === null || params[key] === undefined) {
        delete params[key]
      }
    })
    
    const response = await axios.get('/api/alerts/policies', { params })
    
    policies.value = response.data.policies
    pagination.total = response.data.total
    pagination.current_page = response.data.current_page
    
  } catch (error) {
    console.error('获取告警策略失败:', error)
    ElMessage.error('获取告警策略失败')
  } finally {
    loading.value = false
  }
}

const fetchTemplates = async () => {
  try {
    const response = await axios.get('/api/alerts/templates')
    templates.value = response.data
  } catch (error) {
    console.error('获取策略模板失败:', error)
  }
}

const refreshPolicies = () => {
  fetchPolicies()
}

const handleFilterChange = () => {
  pagination.current_page = 1
  fetchPolicies()
}

const handleSearch = () => {
  pagination.current_page = 1
  fetchPolicies()
}

const handlePageSizeChange = (size) => {
  pagination.per_page = size
  pagination.current_page = 1
  fetchPolicies()
}

const handleCurrentChange = (page) => {
  pagination.current_page = page
  fetchPolicies()
}

const openCreateDialog = () => {
  policyDialog.mode = 'create'
  policyDialog.editingPolicy = null
  resetPolicyForm()
  policyDialog.visible = true
}

const resetPolicyForm = () => {
  Object.assign(policyForm, {
    name: '',
    description: '',
    category: '',
    severity: 'warning',
    repeat_interval: 3600,
    max_alerts: 10,
    enabled: true
  })
  
  if (policyFormRef.value) {
    policyFormRef.value.clearValidate()
  }
}

const handleDialogClose = () => {
  resetPolicyForm()
}

const submitPolicy = async () => {
  try {
    await policyFormRef.value.validate()
    
    submitting.value = true
    
    if (policyDialog.mode === 'create') {
      await axios.post('/api/alerts/policies', policyForm)
      ElMessage.success('策略创建成功')
    } else {
      await axios.put(`/api/alerts/policies/${policyDialog.editingPolicy.id}`, policyForm)
      ElMessage.success('策略更新成功')
    }
    
    policyDialog.visible = false
    fetchPolicies()
    
  } catch (error) {
    console.error('保存策略失败:', error)
    ElMessage.error('保存策略失败')
  } finally {
    submitting.value = false
  }
}

const viewPolicy = (policy) => {
  // 跳转到策略详情页面
  ElMessage.info('策略详情页面开发中...')
}

const togglePolicy = async (policy) => {
  try {
    await axios.put(`/api/alerts/policies/${policy.id}`, {
      enabled: policy.enabled
    })
    
    ElMessage.success(`策略已${policy.enabled ? '启用' : '禁用'}`)
    
  } catch (error) {
    console.error('更新策略状态失败:', error)
    ElMessage.error('更新策略状态失败')
    // 回滚状态
    policy.enabled = !policy.enabled
  }
}

const handlePolicyAction = async (command, policy) => {
  switch (command) {
    case 'edit':
      editPolicy(policy)
      break
    case 'copy':
      copyPolicy(policy)
      break
    case 'test':
      testPolicy(policy)
      break
    case 'delete':
      deletePolicy(policy)
      break
  }
}

const editPolicy = (policy) => {
  policyDialog.mode = 'edit'
  policyDialog.editingPolicy = policy
  
  Object.assign(policyForm, {
    name: policy.name,
    description: policy.description,
    category: policy.category,
    severity: policy.severity,
    repeat_interval: policy.repeat_interval,
    max_alerts: policy.max_alerts,
    enabled: policy.enabled
  })
  
  policyDialog.visible = true
}

const copyPolicy = (policy) => {
  policyDialog.mode = 'create'
  policyDialog.editingPolicy = null
  
  Object.assign(policyForm, {
    name: `${policy.name} - 副本`,
    description: policy.description,
    category: policy.category,
    severity: policy.severity,
    repeat_interval: policy.repeat_interval,
    max_alerts: policy.max_alerts,
    enabled: false
  })
  
  policyDialog.visible = true
}

const testPolicy = (policy) => {
  ElMessage.info('策略测试功能开发中...')
}

const deletePolicy = async (policy) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除策略"${policy.name}"吗？此操作不可恢复。`,
      '确认删除',
      {
        type: 'warning',
        confirmButtonText: '确定删除',
        cancelButtonText: '取消'
      }
    )
    
    await axios.delete(`/api/alerts/policies/${policy.id}`)
    ElMessage.success('策略删除成功')
    fetchPolicies()
    
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除策略失败:', error)
      ElMessage.error('删除策略失败')
    }
  }
}

const showTemplates = () => {
  templateDialog.visible = true
}

const selectTemplate = (template) => {
  policyDialog.mode = 'create'
  policyDialog.editingPolicy = null
  
  Object.assign(policyForm, {
    name: template.name,
    description: template.description,
    category: template.category,
    severity: template.template.severity,
    repeat_interval: 3600,
    max_alerts: 10,
    enabled: true
  })
  
  templateDialog.visible = false
  policyDialog.visible = true
}

// 辅助方法
const getSeverityTagType = (severity) => {
  const typeMap = {
    info: 'info',
    warning: 'warning',
    error: 'danger',
    critical: 'danger'
  }
  return typeMap[severity] || 'info'
}

const getSeverityLabel = (severity) => {
  const labelMap = {
    info: '信息',
    warning: '警告',
    error: '错误',
    critical: '严重'
  }
  return labelMap[severity] || severity
}

const getCategoryLabel = (category) => {
  const labelMap = {
    system: '系统监控',
    task: '任务监控',
    storage: '存储监控',
    node: '节点监控',
    client: '客户端监控'
  }
  return labelMap[category] || category
}

const getCategoryTagType = (category) => {
  const typeMap = {
    system: 'primary',
    task: 'success',
    storage: 'warning',
    node: 'info',
    client: 'danger'
  }
  return typeMap[category] || 'info'
}

const formatInterval = (seconds) => {
  if (seconds < 60) return `${seconds}秒`
  if (seconds < 3600) return `${Math.floor(seconds / 60)}分钟`
  return `${Math.floor(seconds / 3600)}小时`
}

const formatConditions = (conditions) => {
  if (!conditions) return '未配置'
  return `${conditions.metric} ${conditions.operator} ${conditions.threshold}`
}

const formatTime = (timeStr) => {
  if (!timeStr) return ''
  const date = new Date(timeStr)
  return date.toLocaleDateString('zh-CN')
}
</script>

<style scoped>
.alert-policies-page {
  padding: 20px;
  background: var(--bg-color);
  min-height: 100vh;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 20px;
}

.header-left h1 {
  margin: 0 0 5px 0;
  color: var(--text-color);
  font-size: 24px;
  font-weight: 600;
}

.page-description {
  margin: 0;
  color: var(--text-secondary);
  font-size: 14px;
}

.header-right {
  display: flex;
  gap: 12px;
}

/* 过滤器 */
.filter-card {
  margin-bottom: 20px;
  border-radius: 12px;
  border: 1px solid var(--border-color);
}

.filter-container {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
}

.filter-left {
  display: flex;
  gap: 12px;
  align-items: center;
}

.filter-right {
  display: flex;
  gap: 12px;
  align-items: center;
}

/* 策略卡片 */
.policies-card {
  border-radius: 12px;
  border: 1px solid var(--border-color);
}

.policies-container {
  min-height: 400px;
}

.empty-state {
  padding: 60px 0;
  text-align: center;
}

.policies-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  gap: 20px;
  margin-bottom: 20px;
}

.policy-card {
  padding: 20px;
  border-radius: 12px;
  border: 1px solid var(--border-color);
  background: var(--card-bg);
  cursor: pointer;
  transition: all 0.3s ease;
}

.policy-card:hover {
  border-color: var(--primary-color);
  transform: translateY(-2px);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
}

.policy-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 12px;
}

.policy-title {
  flex: 1;
}

.policy-title h3 {
  margin: 0 0 8px 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--text-color);
}

.policy-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.policy-content {
  margin-bottom: 16px;
}

.policy-description {
  margin: 0 0 12px 0;
  color: var(--text-secondary);
  font-size: 14px;
  line-height: 1.5;
}

.policy-info {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-bottom: 12px;
}

.info-item {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
}

.info-label {
  color: var(--text-secondary);
}

.info-value {
  color: var(--text-color);
  font-weight: 500;
}

.policy-conditions {
  margin-top: 12px;
  padding: 8px 12px;
  background: var(--bg-color-page);
  border-radius: 6px;
  border-left: 3px solid var(--primary-color);
}

.conditions-title {
  font-size: 12px;
  color: var(--text-secondary);
  margin-bottom: 4px;
}

.conditions-content {
  font-size: 14px;
  color: var(--text-color);
  font-family: 'Courier New', monospace;
}

.policy-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 12px;
  border-top: 1px solid var(--border-color);
}

.policy-meta {
  display: flex;
  gap: 16px;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: var(--text-secondary);
}

/* 分页 */
.pagination {
  margin-top: 20px;
  display: flex;
  justify-content: center;
}

/* 表单 */
.form-help {
  font-size: 12px;
  color: var(--text-secondary);
  margin-top: 4px;
}

.switch-label {
  margin-left: 8px;
  color: var(--text-secondary);
  font-size: 14px;
}

/* 模板库 */
.templates-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 16px;
  max-height: 400px;
  overflow-y: auto;
}

.template-card {
  padding: 16px;
  border-radius: 8px;
  border: 1px solid var(--border-color);
  background: var(--card-bg);
  cursor: pointer;
  transition: all 0.2s ease;
}

.template-card:hover {
  border-color: var(--primary-color);
  transform: scale(1.02);
}

.template-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.template-header h4 {
  margin: 0;
  font-size: 14px;
  font-weight: 600;
  color: var(--text-color);
}

.template-description {
  margin: 0 0 12px 0;
  font-size: 12px;
  color: var(--text-secondary);
  line-height: 1.4;
}

.template-config {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.config-item {
  display: flex;
  font-size: 12px;
}

.config-label {
  color: var(--text-secondary);
  min-width: 40px;
}

.config-value {
  color: var(--text-color);
  font-family: 'Courier New', monospace;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .alert-policies-page {
    padding: 16px;
  }
  
  .page-header {
    flex-direction: column;
    gap: 16px;
    align-items: stretch;
  }
  
  .filter-container {
    flex-direction: column;
    gap: 12px;
    align-items: stretch;
  }
  
  .filter-left {
    flex-wrap: wrap;
  }
  
  .filter-right {
    justify-content: stretch;
  }
  
  .policies-grid {
    grid-template-columns: 1fr;
  }
  
  .policy-header {
    flex-direction: column;
    gap: 12px;
    align-items: stretch;
  }
  
  .policy-actions {
    justify-content: space-between;
  }
}
</style>