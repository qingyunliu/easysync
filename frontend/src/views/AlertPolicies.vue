<template>
  <div class="alert-policies-page">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-left">
        <h1>告警策略管理</h1>
        <p class="page-description">管理系统的告警策略，监控资源状态和事件</p>
      </div>
      <div class="header-actions">
        <el-button type="primary" @click="openCreateDialog">
          <el-icon><Plus /></el-icon>
          创建告警策略
        </el-button>
      </div>
    </div>

    <!-- 筛选栏 -->
    <div class="filter-bar">
      <el-form :model="filterForm" inline>
        <el-form-item label="策略类型">
          <el-select v-model="filterForm.policy_type" placeholder="全部类型" clearable>
            <el-option label="资源告警" value="resource" />
            <el-option label="事件告警" value="event" />
          </el-select>
        </el-form-item>
        <el-form-item label="告警级别">
          <el-select v-model="filterForm.level" placeholder="全部级别" clearable>
            <el-option label="信息" value="info" />
            <el-option label="警告" value="warning" />
            <el-option label="错误" value="error" />
            <el-option label="严重" value="critical" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="filterForm.enabled" placeholder="全部状态" clearable>
            <el-option label="启用" :value="true" />
            <el-option label="禁用" :value="false" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button @click="loadPolicies">查询</el-button>
          <el-button @click="resetFilter">重置</el-button>
        </el-form-item>
      </el-form>
    </div>

    <!-- 策略列表 -->
    <div class="policies-container">
      <el-row :gutter="20">
        <el-col 
          v-for="policy in filteredPolicies" 
          :key="policy.id" 
          :xs="24" 
          :sm="12" 
          :md="8" 
          :lg="6"
        >
          <div class="policy-card" :class="{ disabled: !policy.enabled }">
            <div class="card-header">
              <div class="policy-info">
                <h3 class="policy-name">{{ policy.name }}</h3>
                <el-tag :type="getLevelTagType(policy.level)" size="small">
                  {{ getLevelLabel(policy.level) }}
                </el-tag>
                <el-tag :type="getPolicyTypeTagType(policy.policy_type)" size="small">
                  {{ getPolicyTypeLabel(policy.policy_type) }}
                </el-tag>
              </div>
              <div class="policy-status">
                <el-switch 
                  v-model="policy.enabled" 
                  @change="togglePolicy(policy)"
                  :loading="policy.toggling"
                />
              </div>
            </div>
            
            <div class="card-content">
              <p class="policy-description">{{ policy.description || '暂无描述' }}</p>
              
              <div class="policy-details">
                <div class="detail-item">
                  <span class="label">监控资源:</span>
                  <span class="value">{{ policy.monitored_resources?.length || 0 }}个</span>
                </div>
                <div class="detail-item">
                  <span class="label">通知渠道:</span>
                  <span class="value">{{ policy.notification_channels?.length || 0 }}个</span>
                </div>
                <div class="detail-item">
                  <span class="label">通知对象:</span>
                  <span class="value">{{ policy.notification_targets?.length || 0 }}个</span>
                </div>
                <div class="detail-item">
                  <span class="label">创建时间:</span>
                  <span class="value">{{ formatDate(policy.created_at) }}</span>
                </div>
              </div>
            </div>
            
            <div class="card-actions">
              <el-button size="small" @click="editPolicy(policy)">编辑</el-button>
              <el-button size="small" type="primary" @click="testPolicy(policy)">测试</el-button>
              <el-button size="small" type="danger" @click="deletePolicy(policy)">删除</el-button>
            </div>
          </div>
        </el-col>
      </el-row>
      
      <div v-if="filteredPolicies.length === 0" class="empty-state">
        <el-empty description="暂无告警策略" />
      </div>
    </div>

    <!-- 创建/编辑对话框 -->
    <el-dialog
      v-model="showCreateDialog"
      :title="editingPolicy ? '编辑告警策略' : '创建告警策略'"
      width="800px"
      @close="resetForm"
    >
      <el-form 
        ref="policyFormRef" 
        :model="policyForm" 
        :rules="policyRules" 
        label-width="120px"
      >
        <!-- 基本信息 -->
        <el-card class="form-section">
          <template #header>
            <span class="section-title">基本信息</span>
          </template>
          
          <el-row :gutter="20">
            <el-col :span="12">
              <el-form-item label="策略名称" prop="name">
                <el-input v-model="policyForm.name" placeholder="请输入策略名称" maxlength="50" show-word-limit />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="策略类型" prop="policy_type">
                <el-radio-group v-model="policyForm.policy_type" @change="handlePolicyTypeChange">
                  <el-radio label="resource">资源告警</el-radio>
                  <el-radio label="event">事件告警</el-radio>
                </el-radio-group>
              </el-form-item>
            </el-col>
          </el-row>
          
          <el-row :gutter="20">
            <el-col :span="12">
              <el-form-item label="告警级别" prop="level">
                <el-select v-model="policyForm.level" placeholder="请选择告警级别">
                  <el-option label="信息" value="info" />
                  <el-option label="警告" value="warning" />
                  <el-option label="错误" value="error" />
                  <el-option label="严重" value="critical" />
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="启用状态">
                <el-switch v-model="policyForm.enabled" />
              </el-form-item>
            </el-col>
          </el-row>
          
          <el-form-item label="策略描述" prop="description">
            <el-input 
              v-model="policyForm.description" 
              type="textarea" 
              :rows="3"
              placeholder="请输入策略描述"
              maxlength="200"
              show-word-limit
            />
          </el-form-item>
        </el-card>

        <!-- 监控配置 -->
        <el-card class="form-section" v-if="isResourcePolicy">
          <template #header>
            <span class="section-title">监控配置</span>
          </template>
          
          <el-row :gutter="20">
            <el-col :span="12">
              <el-form-item label="资源类型" prop="resource_type">
                <el-select v-model="policyForm.resource_type" placeholder="请选择资源类型">
                  <el-option label="源端同步代理" value="source_agent" />
                  <el-option label="目标端同步代理" value="target_agent" />
                  <el-option label="存储节点" value="storage_node" />
                  <el-option label="客户端" value="client" />
                  <el-option label="系统" value="system" />
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="监控资源" prop="monitored_resources">
                <el-button @click="openResourceSelector" type="primary" plain>
                  选择资源 ({{ policyForm.monitored_resources?.length || 0 }})
                </el-button>
              </el-form-item>
            </el-col>
          </el-row>
          
          <el-form-item label="告警项目" prop="alert_items">
            <el-checkbox-group v-model="policyForm.alert_items">
              <el-checkbox label="cpu">CPU使用率</el-checkbox>
              <el-checkbox label="memory">内存使用率</el-checkbox>
              <el-checkbox label="disk">磁盘使用率</el-checkbox>
              <el-checkbox label="network">网络流量</el-checkbox>
              <el-checkbox label="connections">连接数</el-checkbox>
              <el-checkbox label="response_time">响应时间</el-checkbox>
            </el-checkbox-group>
          </el-form-item>
          
          <!-- 触发规则 -->
          <div v-if="policyForm.alert_items && policyForm.alert_items.length > 0">
            <el-divider content-position="left">触发规则</el-divider>
            <div v-for="item in policyForm.alert_items" :key="item" class="trigger-rule">
              <div class="rule-header">
                <span class="rule-title">{{ getAlertItemLabel(item) }}</span>
                <el-button size="small" @click="removeTriggerRule(item)" type="danger" plain>
                  删除规则
                </el-button>
              </div>
              <el-row :gutter="20">
                <el-col :span="8">
                  <el-form-item :label="'操作符'" :prop="`trigger_rules.${item}.operator`">
                    <el-select v-model="policyForm.trigger_rules[item].operator">
                      <el-option label="大于" value="gt" />
                      <el-option label="小于" value="lt" />
                      <el-option label="等于" value="eq" />
                      <el-option label="不等于" value="ne" />
                    </el-select>
                  </el-form-item>
                </el-col>
                <el-col :span="8">
                  <el-form-item :label="'阈值'" :prop="`trigger_rules.${item}.threshold`">
                    <el-input-number 
                      v-model="policyForm.trigger_rules[item].threshold" 
                      :min="0" 
                      :max="100"
                      :precision="2"
                    />
                  </el-form-item>
                </el-col>
                <el-col :span="8">
                  <el-form-item :label="'持续时间(秒)'" :prop="`trigger_rules.${item}.duration`">
                    <el-input-number 
                      v-model="policyForm.trigger_rules[item].duration" 
                      :min="1" 
                      :max="3600"
                    />
                  </el-form-item>
                </el-col>
              </el-row>
            </div>
          </div>
        </el-card>

        <!-- 事件配置 -->
        <el-card class="form-section" v-if="isEventPolicy">
          <template #header>
            <span class="section-title">事件配置</span>
          </template>
          
          <el-row :gutter="20">
            <el-col :span="12">
              <el-form-item label="事件类型" prop="event_type">
                <el-select v-model="policyForm.event_type" placeholder="请选择事件类型">
                  <el-option label="存储" value="storage" />
                  <el-option label="客户端" value="client" />
                  <el-option label="代理" value="agent" />
                  <el-option label="系统" value="system" />
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="事件动作" prop="event_actions">
                <el-select v-model="policyForm.event_actions" multiple placeholder="请选择事件动作">
                  <el-option label="创建" value="create" />
                  <el-option label="更新" value="update" />
                  <el-option label="删除" value="delete" />
                  <el-option label="启动" value="start" />
                  <el-option label="停止" value="stop" />
                </el-select>
              </el-form-item>
            </el-col>
          </el-row>
          
          <el-form-item label="事件结果" prop="event_results">
            <el-checkbox-group v-model="policyForm.event_results">
              <el-checkbox label="success">成功</el-checkbox>
              <el-checkbox label="failure">失败</el-checkbox>
              <el-checkbox label="timeout">超时</el-checkbox>
            </el-checkbox-group>
          </el-form-item>
        </el-card>

        <!-- 通知配置 -->
        <el-card class="form-section">
          <template #header>
            <span class="section-title">通知配置</span>
          </template>
          
          <el-row :gutter="20">
            <el-col :span="12">
              <el-form-item label="告警模板" prop="template_id">
                <el-select v-model="policyForm.template_id" placeholder="请选择告警模板" clearable>
                  <el-option 
                    v-for="template in templates" 
                    :key="template.id" 
                    :label="template.name" 
                    :value="template.id"
                  />
                </el-select>
                <div class="form-tip">选择用于发送通知的模板</div>
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="通知渠道" prop="notification_channels">
                <el-select v-model="policyForm.notification_channels" multiple placeholder="请选择通知渠道">
                  <el-option 
                    v-for="channel in notificationChannels" 
                    :key="channel.id" 
                    :label="channel.name" 
                    :value="channel.id"
                  />
                </el-select>
                <div class="form-tip">选择通知发送的渠道</div>
              </el-form-item>
            </el-col>
          </el-row>
          
          <el-row :gutter="20">
            <el-col :span="12">
              <el-form-item label="通知对象" prop="notification_targets">
                <el-button @click="openNotificationSelector" type="primary" plain>
                  选择对象 ({{ policyForm.notification_targets?.length || 0 }})
                </el-button>
                <div class="form-tip">选择接收通知的目标对象</div>
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="通知周期" prop="notification_cycle">
                <el-select v-model="policyForm.notification_cycle" placeholder="请选择通知周期">
                  <el-option label="立即通知" value="immediate" />
                  <el-option label="5分钟" value="5min" />
                  <el-option label="15分钟" value="15min" />
                  <el-option label="30分钟" value="30min" />
                  <el-option label="1小时" value="1hour" />
                </el-select>
              </el-form-item>
            </el-col>
          </el-row>
          
          <el-row :gutter="20">
            <el-col :span="8">
              <el-form-item label="重试次数" prop="retry_count">
                <el-input-number v-model="policyForm.retry_count" :min="0" :max="10" />
                <div class="form-tip">发送失败时的重试次数</div>
              </el-form-item>
            </el-col>
            <el-col :span="8">
              <el-form-item label="频率限制(秒)" prop="rate_limit">
                <el-input-number v-model="policyForm.rate_limit" :min="60" :max="3600" />
                <div class="form-tip">相同告警的发送间隔</div>
              </el-form-item>
            </el-col>
            <el-col :span="8">
              <el-form-item label="超时时间(秒)" prop="timeout">
                <el-input-number v-model="policyForm.timeout" :min="5" :max="300" />
                <div class="form-tip">发送通知的超时时间</div>
              </el-form-item>
            </el-col>
          </el-row>
        </el-card>
      </el-form>
      
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" @click="savePolicy" :loading="saving">
          {{ editingPolicy ? '更新' : '创建' }}
        </el-button>
      </template>
    </el-dialog>

    <!-- 资源选择器 -->
    <el-dialog v-model="showResourceSelector" title="选择监控资源" width="600px">
      <div class="selector-content">
        <el-input
          v-model="resourceSearchKeyword"
          placeholder="搜索资源..."
          prefix-icon="Search"
          clearable
        />
        
        <div class="resource-list">
          <el-checkbox-group v-model="selectedResources">
            <div 
              v-for="resource in filteredResources" 
              :key="resource.id" 
              class="resource-item"
            >
              <el-checkbox :label="resource.id">
                <div class="resource-info">
                  <span class="resource-name">{{ resource.name }}</span>
                  <span class="resource-type">{{ getResourceTypeLabel(resource.type) }}</span>
                </div>
              </el-checkbox>
            </div>
          </el-checkbox-group>
        </div>
      </div>
      
      <template #footer>
        <el-button @click="showResourceSelector = false">取消</el-button>
        <el-button type="primary" @click="confirmResourceSelection">确定</el-button>
      </template>
    </el-dialog>

    <!-- 通知对象选择器 -->
    <el-dialog v-model="showNotificationSelector" title="选择通知对象" width="600px">
      <div class="selector-content">
        <el-input
          v-model="notificationSearchKeyword"
          placeholder="搜索通知对象..."
          prefix-icon="Search"
          clearable
        />
        
        <div class="notification-list">
          <el-checkbox-group v-model="selectedNotifications">
            <div 
              v-for="target in filteredNotifications" 
              :key="target.id" 
              class="notification-item"
            >
              <el-checkbox :label="target.id">
                <div class="notification-info">
                  <span class="notification-name">{{ target.name }}</span>
                  <span class="notification-type">{{ target.type }}</span>
                </div>
              </el-checkbox>
            </div>
          </el-checkbox-group>
        </div>
      </div>
      
      <template #footer>
        <el-button @click="showNotificationSelector = false">取消</el-button>
        <el-button type="primary" @click="confirmNotificationSelection">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import axios from 'axios'

// 响应式数据
const loading = ref(false)
const policies = ref([])
const availableResources = ref([])
const notificationTargets = ref([])
const notificationChannels = ref([])
const templates = ref([])
const policyFormRef = ref()

// 筛选表单
const filterForm = reactive({
  policy_type: '',
  level: '',
  enabled: null
})

// 策略表单
const policyForm = reactive({
  name: '',
  description: '',
  policy_type: 'resource',
  level: 'warning',
  enabled: true,
  resource_type: '',
  monitored_resources: [],
  alert_items: [],
  trigger_rules: {},
  event_type: '',
  event_actions: [],
  event_results: [],
  template_id: '',
  notification_channels: [],
  notification_targets: [],
  notification_cycle: 'immediate',
  retry_count: 3,
  rate_limit: 300,
  timeout: 30
})

// 表单验证规则
const policyRules = {
  name: [
    { required: true, message: '请输入策略名称', trigger: 'blur' },
    { min: 2, max: 50, message: '策略名称长度在 2 到 50 个字符', trigger: 'blur' }
  ],
  policy_type: [
    { required: true, message: '请选择策略类型', trigger: 'change' }
  ],
  level: [
    { required: true, message: '请选择告警级别', trigger: 'change' }
  ],
  description: [
    { max: 200, message: '描述长度不能超过 200 个字符', trigger: 'blur' }
  ]
}

// 弹窗控制
const showCreateDialog = ref(false)
const showResourceSelector = ref(false)
const showNotificationSelector = ref(false)
const editingPolicy = ref(null)
const saving = ref(false)

// 选择器数据
const resourceSearchKeyword = ref('')
const selectedResources = ref([])
const filteredResources = computed(() => {
  if (!resourceSearchKeyword.value) return availableResources.value
  const keyword = resourceSearchKeyword.value.toLowerCase()
  return availableResources.value.filter(resource => 
    resource.name.toLowerCase().includes(keyword) ||
    resource.type.toLowerCase().includes(keyword)
  )
})

const notificationSearchKeyword = ref('')
const selectedNotifications = ref([])
const filteredNotifications = computed(() => {
  if (!notificationSearchKeyword.value) return notificationTargets.value
  const keyword = notificationSearchKeyword.value.toLowerCase()
  return notificationTargets.value.filter(target => 
    target.name.toLowerCase().includes(keyword) ||
    target.type.toLowerCase().includes(keyword)
  )
})

// 计算属性
const isResourcePolicy = computed(() => policyForm.policy_type === 'resource')
const isEventPolicy = computed(() => policyForm.policy_type === 'event')

const filteredPolicies = computed(() => {
  let result = policies.value
  
  if (filterForm.policy_type) {
    result = result.filter(policy => policy.policy_type === filterForm.policy_type)
  }
  
  if (filterForm.level) {
    result = result.filter(policy => policy.level === filterForm.level)
  }
  
  if (filterForm.enabled !== null) {
    result = result.filter(policy => policy.enabled === filterForm.enabled)
  }
  
  return result
})

// 方法
const loadPolicies = async () => {
  try {
    loading.value = true
    const response = await axios.get('/api/alerts/policies')
    policies.value = response.data.data || []
  } catch (error) {
    ElMessage.error('加载告警策略失败')
  } finally {
    loading.value = false
  }
}

const loadResources = async () => {
  try {
    const response = await axios.get('/api/nodes')
    availableResources.value = response.data.data || []
  } catch (error) {
    console.error('加载资源失败:', error)
  }
}

const loadNotificationTargets = async () => {
  try {
    const response = await axios.get('/api/notifications/targets')
    notificationTargets.value = response.data.targets || []
  } catch (error) {
    console.error('加载通知对象失败:', error)
  }
}

const loadNotificationChannels = async () => {
  try {
    const response = await axios.get('/api/notifications/channels')
    notificationChannels.value = response.data.channels || []
  } catch (error) {
    console.error('加载通知渠道失败:', error)
  }
}

const loadTemplates = async () => {
  try {
    const response = await axios.get('/api/alerts/templates')
    templates.value = response.data.templates || []
  } catch (error) {
    console.error('加载模板失败:', error)
  }
}

const resetFilter = () => {
  filterForm.policy_type = ''
  filterForm.level = ''
  filterForm.enabled = null
  loadPolicies()
}

const openCreateDialog = () => {
  editingPolicy.value = null
  resetPolicyForm()
  showCreateDialog.value = true
}

const editPolicy = (policy) => {
  editingPolicy.value = policy
  Object.assign(policyForm, {
    name: policy.name,
    description: policy.description || '',
    policy_type: policy.policy_type,
    level: policy.level,
    enabled: policy.enabled,
    resource_type: policy.resource_type || '',
    monitored_resources: policy.monitored_resources || [],
    alert_items: policy.alert_items || [],
    trigger_rules: policy.trigger_rules || {},
    event_type: policy.event_type || '',
    event_actions: policy.event_actions || [],
    event_results: policy.event_results || [],
    template_id: policy.template_id || '',
    notification_channels: policy.notification_channels || [],
    notification_targets: policy.notification_targets || [],
    notification_cycle: policy.notification_cycle || 'immediate',
    retry_count: policy.retry_count || 3,
    rate_limit: policy.rate_limit || 300,
    timeout: policy.timeout || 30
  })
  showCreateDialog.value = true
}

const resetPolicyForm = () => {
  Object.assign(policyForm, {
    name: '',
    description: '',
    policy_type: 'resource',
    level: 'warning',
    enabled: true,
    resource_type: '',
    monitored_resources: [],
    alert_items: [],
    trigger_rules: {},
    event_type: '',
    event_actions: [],
    event_results: [],
    template_id: '',
    notification_channels: [],
    notification_targets: [],
    notification_cycle: 'immediate',
    retry_count: 3,
    rate_limit: 300,
    timeout: 30
  })
  policyFormRef.value?.resetFields()
}

const handlePolicyTypeChange = () => {
  if (policyForm.policy_type === 'resource') {
    policyForm.event_type = ''
    policyForm.event_actions = []
    policyForm.event_results = []
    policyForm.trigger_rules = {}
  } else {
    policyForm.resource_type = ''
    policyForm.monitored_resources = []
    policyForm.alert_items = []
    policyForm.trigger_rules = {}
  }
}

const openResourceSelector = () => {
  showResourceSelector.value = true
  selectedResources.value = policyForm.monitored_resources.map(r => r.id)
}

const confirmResourceSelection = () => {
  policyForm.monitored_resources = availableResources.value.filter(r => selectedResources.value.includes(r.id))
  showResourceSelector.value = false
}

const openNotificationSelector = () => {
  showNotificationSelector.value = true
  selectedNotifications.value = policyForm.notification_targets.map(t => t.id)
}

const confirmNotificationSelection = () => {
  policyForm.notification_targets = notificationTargets.value.filter(target => selectedNotifications.value.includes(target.id))
  showNotificationSelector.value = false
}

const removeTriggerRule = (item) => {
  delete policyForm.trigger_rules[item]
  policyForm.alert_items = policyForm.alert_items.filter(i => i !== item)
}

const togglePolicy = async (policy) => {
  try {
    policy.toggling = true
    const response = await axios.put(`/api/alerts/policies/${policy.id}`, {
      enabled: policy.enabled
    })
    ElMessage.success(policy.enabled ? '策略已启用' : '策略已禁用')
  } catch (error) {
    policy.enabled = !policy.enabled // 恢复状态
    ElMessage.error('操作失败')
  } finally {
    policy.toggling = false
  }
}

const testPolicy = async (policy) => {
  try {
    await axios.post(`/api/alerts/policies/${policy.id}/test`)
    ElMessage.success('测试告警已发送')
  } catch (error) {
    ElMessage.error('测试失败')
  }
}

const deletePolicy = async (policy) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除告警策略 "${policy.name}" 吗？`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    await axios.delete(`/api/alerts/policies/${policy.id}`)
    ElMessage.success('删除成功')
    loadPolicies()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

const savePolicy = async () => {
  try {
    await policyFormRef.value.validate()
    saving.value = true
    
    const data = { ...policyForm }
    
    if (editingPolicy.value) {
      await axios.put(`/api/alerts/policies/${editingPolicy.value.id}`, data)
      ElMessage.success('更新成功')
    } else {
      await axios.post('/api/alerts/policies', data)
      ElMessage.success('创建成功')
    }
    
    showCreateDialog.value = false
    loadPolicies()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(editingPolicy.value ? '更新失败' : '创建失败')
    }
  } finally {
    saving.value = false
  }
}

const resetForm = () => {
  resetPolicyForm()
}

// 工具方法
const getLevelLabel = (level) => {
  const labels = {
    info: '信息',
    warning: '警告',
    error: '错误',
    critical: '严重'
  }
  return labels[level] || level
}

const getLevelTagType = (level) => {
  const types = {
    info: 'info',
    warning: 'warning',
    error: 'danger',
    critical: 'danger'
  }
  return types[level] || 'info'
}

const getPolicyTypeLabel = (type) => {
  const labels = {
    resource: '资源告警',
    event: '事件告警'
  }
  return labels[type] || type
}

const getPolicyTypeTagType = (type) => {
  const types = {
    resource: 'primary',
    event: 'success'
  }
  return types[type] || 'info'
}

const getResourceTypeLabel = (type) => {
  const labels = {
    source_agent: '源端同步代理',
    target_agent: '目标端同步代理',
    storage_node: '存储节点',
    client: '客户端',
    system: '系统'
  }
  return labels[type] || type
}

const getAlertItemLabel = (item) => {
  const labels = {
    cpu: 'CPU使用率',
    memory: '内存使用率',
    disk: '磁盘使用率',
    network: '网络流量',
    connections: '连接数',
    response_time: '响应时间'
  }
  return labels[item] || item
}

const formatDate = (date) => {
  if (!date) return '-'
  return new Date(date).toLocaleString('zh-CN')
}

// 生命周期
onMounted(() => {
  loadPolicies()
  loadResources()
  loadNotificationTargets()
  loadNotificationChannels()
  loadTemplates()
})
</script>

<style scoped>
.alert-policies-page {
  padding: 20px;
  background: #f5f7fa;
  min-height: 100vh;
}

.page-header {
  background: white;
  padding: 24px;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  margin-bottom: 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-left h1 {
  margin: 0 0 8px 0;
  font-size: 24px;
  font-weight: 600;
  color: #303133;
}

.page-description {
  margin: 0;
  color: #606266;
  font-size: 14px;
}

.filter-bar {
  background: white;
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  margin-bottom: 20px;
}

.policies-container {
  margin-top: 20px;
}

.policy-card {
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  margin-bottom: 20px;
  transition: all 0.3s ease;
  border: 1px solid #e4e7ed;
}

.policy-card:hover {
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
  transform: translateY(-2px);
}

.policy-card.disabled {
  opacity: 0.6;
}

.card-header {
  padding: 20px 20px 0;
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}

.policy-info {
  flex: 1;
}

.policy-name {
  margin: 0 0 12px 0;
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.policy-info .el-tag {
  margin-right: 8px;
}

.policy-status {
  margin-left: 16px;
}

.card-content {
  padding: 16px 20px;
}

.policy-description {
  margin: 0 0 16px 0;
  color: #606266;
  font-size: 14px;
  line-height: 1.5;
}

.policy-details {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.detail-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 13px;
}

.detail-item .label {
  color: #909399;
}

.detail-item .value {
  color: #303133;
  font-weight: 500;
}

.card-actions {
  padding: 16px 20px 20px;
  display: flex;
  gap: 8px;
  border-top: 1px solid #f0f0f0;
}

.empty-state {
  text-align: center;
  padding: 60px 20px;
}

.form-section {
  margin-bottom: 20px;
}

.section-title {
  font-weight: 600;
  color: #303133;
}

.trigger-rule {
  background: #f8f9fa;
  padding: 16px;
  border-radius: 6px;
  margin-bottom: 16px;
}

.rule-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.rule-title {
  font-weight: 600;
  color: #303133;
}

.selector-content {
  max-height: 400px;
  overflow-y: auto;
}

.resource-list,
.notification-list {
  margin-top: 16px;
}

.resource-item,
.notification-item {
  padding: 12px;
  border-bottom: 1px solid #f0f0f0;
}

.resource-item:last-child,
.notification-item:last-child {
  border-bottom: none;
}

.resource-info,
.notification-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-left: 8px;
}

.resource-name,
.notification-name {
  font-weight: 500;
  color: #303133;
}

.resource-type,
.notification-type {
  color: #909399;
  font-size: 12px;
}

:deep(.el-card__header) {
  padding: 16px 20px;
  border-bottom: 1px solid #f0f0f0;
  background: #fafafa;
}

:deep(.el-form-item__label) {
  font-weight: 500;
  color: #303133;
}

:deep(.el-checkbox-group) {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

:deep(.el-radio-group) {
  display: flex;
  gap: 16px;
}

.form-tip {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
  line-height: 1.4;
}
</style>