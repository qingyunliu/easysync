<template>
  <div class="alert-policies-page">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-left">
        <h1>告警策略</h1>
        <p class="page-description">管理资源告警和事件告警策略</p>
      </div>
      <div class="header-actions">
        <el-button type="primary" @click="openCreateDialog">
          <el-icon><Plus /></el-icon>
          创建告警策略
        </el-button>
        <el-button @click="openTemplateDialog">
          <el-icon><Document /></el-icon>
          模板库
        </el-button>
      </div>
    </div>

    <!-- 筛选和搜索 -->
    <el-card class="filter-card">
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
        
        <el-form-item label="关键词">
          <el-input 
            v-model="filterForm.keyword" 
            placeholder="搜索告警策略名称或描述"
            clearable
            @keyup.enter="loadPolicies"
          />
        </el-form-item>
        
        <el-form-item>
          <el-button type="primary" @click="loadPolicies">搜索</el-button>
          <el-button @click="resetFilter">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 策略列表 -->
    <el-card>
      <div v-loading="loading">
        <div v-if="policies.length === 0" class="empty-state">
          <el-empty description="暂无告警策略">
            <el-button type="primary" @click="openCreateDialog">创建第一个策略</el-button>
          </el-empty>
        </div>
        
        <div v-else class="policies-container">
          <div v-for="policy in policies" :key="policy.id" class="policy-card">
            <div class="policy-header">
              <div class="policy-title">
                <h3>{{ policy.name }}</h3>
                <div class="policy-tags">
                  <el-tag :type="getLevelTagType(policy.level)" size="small">
                    {{ getLevelLabel(policy.level) }}
                  </el-tag>
                  <el-tag :type="getPolicyTypeTagType(policy.policy_type)" size="small">
                    {{ getPolicyTypeLabel(policy.policy_type) }}
                  </el-tag>
                  <el-tag v-if="policy.enabled" type="success" size="small">启用</el-tag>
                  <el-tag v-else type="info" size="small">禁用</el-tag>
                </div>
              </div>
              <div class="policy-actions">
                <el-button type="text" size="small" @click="editPolicy(policy)">
                  <el-icon><Edit /></el-icon>
                  编辑
                </el-button>
                <el-button type="text" size="small" @click="testPolicy(policy)">
                  <el-icon><VideoPlay /></el-icon>
                  测试
                </el-button>
                <el-button type="text" size="small" @click="togglePolicy(policy)">
                  {{ policy.enabled ? '禁用' : '启用' }}
                </el-button>
                <el-button type="text" size="small" @click="deletePolicy(policy)" style="color: #f56c6c">
                  <el-icon><Delete /></el-icon>
                  删除
                </el-button>
              </div>
            </div>
            
            <div class="policy-content">
              <p class="policy-description">{{ policy.description || '暂无描述' }}</p>
              
              <!-- 资源告警详情 -->
              <div v-if="policy.policy_type === 'resource'" class="resource-details">
                <div class="detail-item">
                  <span class="label">资源类型:</span>
                  <span class="value">{{ getResourceTypeLabel(policy.resource_type) }}</span>
                </div>
                <div class="detail-item">
                  <span class="label">监控资源:</span>
                  <span class="value">{{ policy.monitored_resources?.length || 0 }}个</span>
                </div>
                <div class="detail-item">
                  <span class="label">报警条目:</span>
                  <span class="value">{{ policy.alert_items?.join(', ') || '无' }}</span>
                </div>
                <div class="detail-item">
                  <span class="label">触发规则:</span>
                  <span class="value">{{ formatTriggerRules(policy.trigger_rules) }}</span>
                </div>
              </div>
              
              <!-- 事件告警详情 -->
              <div v-if="policy.policy_type === 'event'" class="event-details">
                <div class="detail-item">
                  <span class="label">事件类型:</span>
                  <span class="value">{{ getEventTypeLabel(policy.event_type) }}</span>
                </div>
                <div class="detail-item">
                  <span class="label">事件动作:</span>
                  <span class="value">{{ policy.event_actions?.join(', ') || '无' }}</span>
                </div>
                <div class="detail-item">
                  <span class="label">事件结果:</span>
                  <span class="value">{{ policy.event_results?.join(', ') || '无' }}</span>
                </div>
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
        </div>
      </div>
    </el-card>

    <!-- 创建/编辑对话框 -->
    <el-dialog 
      v-model="dialogVisible" 
      :title="dialogMode === 'create' ? '创建告警策略' : '编辑告警策略'" 
      width="800px"
      :close-on-click-modal="false"
    >
      <el-form :model="policyForm" :rules="policyRules" ref="policyFormRef" label-width="120px">
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="策略名称" prop="name">
              <el-input v-model="policyForm.name" placeholder="请输入策略名称" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="告警级别" prop="level">
              <el-select v-model="policyForm.level" placeholder="选择告警级别">
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
            <el-form-item label="策略类型" prop="policy_type">
              <el-select v-model="policyForm.policy_type" @change="handlePolicyTypeChange" placeholder="选择策略类型">
                <el-option label="资源告警" value="resource" />
                <el-option label="事件告警" value="event" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="启用状态">
              <el-switch v-model="policyForm.enabled" />
            </el-form-item>
          </el-col>
        </el-row>
        
        <!-- 资源告警配置 -->
        <div v-if="policyForm.policy_type === 'resource'" class="resource-config">
          <el-divider content-position="left">资源告警配置</el-divider>
          
          <el-row :gutter="20">
            <el-col :span="12">
              <el-form-item label="资源类型" prop="resource_type">
                <el-select v-model="policyForm.resource_type" @change="handleResourceTypeChange" placeholder="选择资源类型">
                  <el-option label="Nodes" value="Nodes" />
                  <el-option label="Clients" value="Clients" />
                  <el-option label="系统" value="System" />
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="监控资源" prop="monitored_resources">
                <el-select v-model="policyForm.monitored_resources" multiple placeholder="选择监控资源">
                  <el-option 
                    v-for="resource in availableResources" 
                    :key="resource.id" 
                    :label="resource.name" 
                    :value="resource.id" 
                  />
                </el-select>
              </el-form-item>
            </el-col>
          </el-row>
          
          <el-form-item label="报警条目" prop="alert_items">
            <el-checkbox-group v-model="policyForm.alert_items">
              <el-checkbox label="CPU">CPU使用率</el-checkbox>
              <el-checkbox label="内存">内存使用率</el-checkbox>
              <el-checkbox label="磁盘">磁盘使用率</el-checkbox>
              <el-checkbox label="网络">网络流量</el-checkbox>
              <el-checkbox label="进程">进程数量</el-checkbox>
            </el-checkbox-group>
          </el-form-item>
          
          <el-form-item label="触发规则" prop="trigger_rules">
            <div class="trigger-rules">
              <div v-for="(rule, index) in policyForm.trigger_rules" :key="index" class="rule-item">
                <el-row :gutter="10">
                  <el-col :span="6">
                    <el-select v-model="rule.item" placeholder="监控项">
                      <el-option label="CPU使用率" value="cpu_usage" />
                      <el-option label="内存使用率" value="memory_usage" />
                      <el-option label="磁盘使用率" value="disk_usage" />
                      <el-option label="网络流量" value="network_traffic" />
                    </el-select>
                  </el-col>
                  <el-col :span="4">
                    <el-select v-model="rule.operator" placeholder="操作符">
                      <el-option label="大于" value="gt" />
                      <el-option label="大于等于" value="gte" />
                      <el-option label="小于" value="lt" />
                      <el-option label="小于等于" value="lte" />
                      <el-option label="等于" value="eq" />
                    </el-select>
                  </el-col>
                  <el-col :span="4">
                    <el-input-number v-model="rule.threshold" :min="0" :max="100" placeholder="阈值" />
                  </el-col>
                  <el-col :span="4">
                    <el-input-number v-model="rule.duration" :min="1" :max="60" placeholder="持续时间(分钟)" />
                  </el-col>
                  <el-col :span="4">
                    <el-button type="danger" size="small" @click="removeTriggerRule(index)">
                      <el-icon><Delete /></el-icon>
                    </el-button>
                  </el-col>
                </el-row>
              </div>
              <el-button type="primary" size="small" @click="addTriggerRule">
                <el-icon><Plus /></el-icon>
                添加规则
              </el-button>
            </div>
          </el-form-item>
        </div>
        
        <!-- 事件告警配置 -->
        <div v-if="policyForm.policy_type === 'event'" class="event-config">
          <el-divider content-position="left">事件告警配置</el-divider>
          
          <el-row :gutter="20">
            <el-col :span="12">
              <el-form-item label="事件类型" prop="event_type">
                <el-select v-model="policyForm.event_type" @change="handleEventTypeChange" placeholder="选择事件类型">
                  <el-option label="存储" value="storage" />
                  <el-option label="客户端" value="client" />
                  <el-option label="代理" value="agent" />
                  <el-option label="系统" value="system" />
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="事件动作" prop="event_actions">
                <el-select v-model="policyForm.event_actions" multiple placeholder="选择事件动作">
                  <el-option 
                    v-for="action in availableEventActions" 
                    :key="action" 
                    :label="action" 
                    :value="action" 
                  />
                </el-select>
              </el-form-item>
            </el-col>
          </el-row>
          
          <el-form-item label="事件结果" prop="event_results">
            <el-checkbox-group v-model="policyForm.event_results">
              <el-checkbox 
                v-for="result in availableEventResults" 
                :key="result.id" 
                :label="result.id"
              >
                {{ result.name }}
              </el-checkbox>
            </el-checkbox-group>
          </el-form-item>
        </div>
        
        <el-form-item label="通知对象" prop="notification_targets">
          <el-select v-model="policyForm.notification_targets" multiple placeholder="选择通知对象">
            <el-option 
              v-for="target in notificationTargets" 
              :key="target.id" 
              :label="target.name" 
              :value="target.id" 
            />
          </el-select>
        </el-form-item>
        
        <el-form-item label="策略描述">
          <el-input v-model="policyForm.description" type="textarea" :rows="3" placeholder="请输入策略描述" />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitPolicy" :loading="submitting">
          {{ dialogMode === 'create' ? '创建' : '保存' }}
        </el-button>
      </template>
    </el-dialog>

    <!-- 模板库对话框 -->
    <el-dialog v-model="templateDialogVisible" title="告警策略模板库" width="800px">
      <div class="template-library">
        <div v-for="template in alertTemplates" :key="template.id" class="template-item">
          <div class="template-header">
            <h4>{{ template.name }}</h4>
            <el-tag :type="getLevelTagType(template.level)" size="small">
              {{ getLevelLabel(template.level) }}
            </el-tag>
          </div>
          <p class="template-description">{{ template.description }}</p>
          <div class="template-actions">
            <el-button type="primary" size="small" @click="useTemplate(template)">
              使用模板
            </el-button>
            <el-button size="small" @click="previewTemplate(template)">
              预览
            </el-button>
          </div>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script>
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Edit, Delete, VideoPlay, Document } from '@element-plus/icons-vue'
import axios from 'axios'

export default {
  name: 'AlertPolicies',
  components: {
    Plus,
    Edit,
    Delete,
    VideoPlay,
    Document
  },
  setup() {
    // 响应式数据
    const loading = ref(false)
    const submitting = ref(false)
    const dialogVisible = ref(false)
    const templateDialogVisible = ref(false)
    const dialogMode = ref('create')
    const policies = ref([])
    const notificationTargets = ref([])
    const alertTemplates = ref([])
    const availableResources = ref([])
    const availableEventActions = ref([])
    const availableEventResults = ref([])
    const policyFormRef = ref()

    // 筛选表单
    const filterForm = reactive({
      policy_type: '',
      level: '',
      enabled: null,
      keyword: ''
    })

    // 策略表单
    const policyForm = reactive({
      name: '',
      description: '',
      level: 'warning',
      enabled: true,
      policy_type: 'resource',
      resource_type: '',
      monitored_resources: [],
      alert_items: [],
      trigger_rules: [],
      event_type: '',
      event_actions: [],
      notification_targets: []
    })

    // 表单验证规则
    const policyRules = {
      name: [
        { required: true, message: '请输入策略名称', trigger: 'blur' },
        { min: 2, max: 50, message: '长度在 2 到 50 个字符', trigger: 'blur' }
      ],
      level: [
        { required: true, message: '请选择告警级别', trigger: 'change' }
      ],
      policy_type: [
        { required: true, message: '请选择策略类型', trigger: 'change' }
      ],
      resource_type: [
        { required: true, message: '请选择资源类型', trigger: 'change' }
      ],
      monitored_resources: [
        { required: true, message: '请选择监控资源', trigger: 'change' }
      ],
      alert_items: [
        { required: true, message: '请选择报警条目', trigger: 'change' }
      ],
      trigger_rules: [
        { required: true, message: '请配置触发规则', trigger: 'change' }
      ],
      event_type: [
        { required: true, message: '请选择事件类型', trigger: 'change' }
      ],
      event_actions: [
        { required: true, message: '请选择事件动作', trigger: 'change' }
      ],
      event_results: [
        { required: true, message: '请选择事件结果', trigger: 'change' }
      ],
      notification_targets: [
        { required: true, message: '请选择通知对象', trigger: 'change' }
      ]
    }

    // 计算属性
    const isResourcePolicy = computed(() => policyForm.policy_type === 'resource')
    const isEventPolicy = computed(() => policyForm.policy_type === 'event')

    // 方法
    const loadPolicies = async () => {
      loading.value = true
      try {
        const params = {}
        if (filterForm.policy_type) params.policy_type = filterForm.policy_type
        if (filterForm.level) params.level = filterForm.level
        if (filterForm.enabled !== null) params.enabled = filterForm.enabled
        if (filterForm.keyword) params.keyword = filterForm.keyword

        const response = await axios.get('/api/alerts/policies', { params })
        policies.value = response.data.policies || []
      } catch (error) {
        console.error('加载告警策略失败:', error)
        ElMessage.error('加载告警策略失败')
      } finally {
        loading.value = false
      }
    }

    const loadNotificationTargets = async () => {
      try {
        const response = await axios.get('/api/alerts/targets')
        notificationTargets.value = response.data.targets || []
      } catch (error) {
        console.error('加载通知对象失败:', error)
      }
    }

    const loadTemplates = async () => {
      try {
        const response = await axios.get('/api/alerts/templates')
        alertTemplates.value = response.data.templates || []
      } catch (error) {
        console.error('加载模板失败:', error)
      }
    }

    const loadMonitorableResources = async () => {
      try {
        const response = await axios.get('/api/alerts/resources')
        availableResources.value = response.data.resources || []
      } catch (error) {
        console.error('加载可监控资源失败:', error)
      }
    }

    const loadMonitorableEvents = async () => {
      try {
        const response = await axios.get('/api/alerts/events')
        availableEventActions.value = response.data.events || []
        availableEventResults.value = response.data.results || []
      } catch (error) {
        console.error('加载可监控事件失败:', error)
      }
    }

    const resetFilter = () => {
      Object.assign(filterForm, {
        policy_type: '',
        level: '',
        enabled: null,
        keyword: ''
      })
      loadPolicies()
    }

    const openCreateDialog = () => {
      dialogMode.value = 'create'
      resetPolicyForm()
      dialogVisible.value = true
    }

    const editPolicy = (policy) => {
      dialogMode.value = 'edit'
      Object.assign(policyForm, {
        id: policy.id,
        name: policy.name,
        description: policy.description,
        level: policy.level,
        enabled: policy.enabled,
        policy_type: policy.policy_type,
        resource_type: policy.resource_type,
        monitored_resources: policy.monitored_resources || [],
        alert_items: policy.alert_items || [],
        trigger_rules: policy.trigger_rules || [],
        event_type: policy.event_type,
        event_actions: policy.event_actions || [],
        event_results: policy.event_results || [],
        notification_targets: policy.notification_targets || []
      })
      dialogVisible.value = true
    }

    const resetPolicyForm = () => {
      Object.assign(policyForm, {
        id: null,
        name: '',
        description: '',
        level: 'warning',
        enabled: true,
        policy_type: 'resource',
        resource_type: '',
        monitored_resources: [],
        alert_items: [],
        trigger_rules: [],
        event_type: '',
        event_actions: [],
        event_results: [],
        notification_targets: []
      })
    }

    const handlePolicyTypeChange = () => {
      if (policyForm.policy_type === 'resource') {
        policyForm.event_type = ''
        policyForm.event_actions = []
      } else {
        policyForm.resource_type = ''
        policyForm.monitored_resources = []
        policyForm.alert_items = []
        policyForm.trigger_rules = []
      }
    }

    const handleResourceTypeChange = () => {
      policyForm.monitored_resources = []
      loadMonitorableResources()
    }

    const handleEventTypeChange = () => {
      policyForm.event_actions = []
      loadMonitorableEvents()
    }

    const addTriggerRule = () => {
      policyForm.trigger_rules.push({
        item: '',
        operator: 'gt',
        threshold: 80,
        duration: 5
      })
    }

    const removeTriggerRule = (index) => {
      policyForm.trigger_rules.splice(index, 1)
    }

    const submitPolicy = async () => {
      try {
        await policyFormRef.value.validate()
        submitting.value = true

        const data = { ...policyForm }
        if (dialogMode.value === 'create') {
          await axios.post('/api/alerts/policies', data)
          ElMessage.success('告警策略创建成功')
        } else {
          await axios.put(`/api/alerts/policies/${data.id}`, data)
          ElMessage.success('告警策略更新成功')
        }

        dialogVisible.value = false
        loadPolicies()
      } catch (error) {
        console.error('提交告警策略失败:', error)
        ElMessage.error(error.response?.data?.message || '操作失败')
      } finally {
        submitting.value = false
      }
    }

    const togglePolicy = async (policy) => {
      try {
        await axios.put(`/api/alerts/policies/${policy.id}/toggle`)
        ElMessage.success(`策略已${policy.enabled ? '禁用' : '启用'}`)
        loadPolicies()
      } catch (error) {
        console.error('切换策略状态失败:', error)
        ElMessage.error('操作失败')
      }
    }

    const testPolicy = async (policy) => {
      try {
        await axios.post(`/api/alerts/policies/${policy.id}/test`)
        ElMessage.success('测试告警已发送')
      } catch (error) {
        console.error('测试告警失败:', error)
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
        ElMessage.success('告警策略删除成功')
        loadPolicies()
      } catch (error) {
        if (error !== 'cancel') {
          console.error('删除告警策略失败:', error)
          ElMessage.error('删除失败')
        }
      }
    }

    const openTemplateDialog = () => {
      templateDialogVisible.value = true
    }

    const useTemplate = (template) => {
      dialogMode.value = 'create'
      Object.assign(policyForm, template.config)
      templateDialogVisible.value = false
      dialogVisible.value = true
    }

    const previewTemplate = (template) => {
      ElMessage.info(`模板: ${template.name}`)
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
        Nodes: '节点',
        Clients: '客户端',
        System: '系统'
      }
      return labels[type] || type
    }

    const getEventTypeLabel = (type) => {
      const labels = {
        storage: '存储',
        client: '客户端',
        agent: '代理',
        system: '系统'
      }
      return labels[type] || type
    }

    const formatTriggerRules = (rules) => {
      if (!rules || rules.length === 0) return '无'
      return rules.map(rule => 
        `${rule.item} ${rule.operator} ${rule.threshold}% 持续${rule.duration}分钟`
      ).join(', ')
    }

    const formatDate = (date) => {
      if (!date) return '-'
      return new Date(date).toLocaleString('zh-CN')
    }

    // 生命周期
    onMounted(() => {
      loadPolicies()
      loadNotificationTargets()
      loadTemplates()
      loadMonitorableResources()
      loadMonitorableEvents()
    })

    return {
      loading,
      submitting,
      dialogVisible,
      templateDialogVisible,
      dialogMode,
      policies,
      notificationTargets,
      alertTemplates,
      availableResources,
      availableEventActions,
      availableEventResults,
      filterForm,
      policyForm,
      policyFormRef,
      policyRules,
      isResourcePolicy,
      isEventPolicy,
      loadPolicies,
      resetFilter,
      openCreateDialog,
      editPolicy,
      submitPolicy,
      togglePolicy,
      testPolicy,
      deletePolicy,
      openTemplateDialog,
      useTemplate,
      previewTemplate,
      handlePolicyTypeChange,
      handleResourceTypeChange,
      handleEventTypeChange,
      addTriggerRule,
      removeTriggerRule,
      getLevelLabel,
      getLevelTagType,
      getPolicyTypeLabel,
      getPolicyTypeTagType,
      getResourceTypeLabel,
      getEventTypeLabel,
      formatTriggerRules,
      formatDate
    }
  }
}
</script>

<style scoped>
.alert-policies-page {
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 20px;
}

.header-left h1 {
  margin: 0 0 8px 0;
  font-size: 24px;
  font-weight: 600;
}

.page-description {
  margin: 0;
  color: #666;
  font-size: 14px;
}

.header-actions {
  display: flex;
  gap: 12px;
}

.filter-card {
  margin-bottom: 20px;
}

.policies-container {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(400px, 1fr));
  gap: 20px;
}

.policy-card {
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  padding: 16px;
  background: #fff;
  transition: all 0.3s;
}

.policy-card:hover {
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

.policy-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 12px;
}

.policy-title h3 {
  margin: 0 0 8px 0;
  font-size: 16px;
  font-weight: 600;
}

.policy-tags {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

.policy-actions {
  display: flex;
  gap: 8px;
}

.policy-content {
  font-size: 14px;
}

.policy-description {
  margin: 0 0 12px 0;
  color: #666;
  line-height: 1.5;
}

.detail-item {
  display: flex;
  margin-bottom: 6px;
  font-size: 13px;
}

.detail-item .label {
  color: #666;
  min-width: 80px;
  margin-right: 8px;
}

.detail-item .value {
  color: #333;
  flex: 1;
}

.resource-details,
.event-details {
  margin-bottom: 12px;
  padding: 12px;
  background: #f8f9fa;
  border-radius: 4px;
}

.trigger-rules {
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  padding: 12px;
  background: #fafafa;
}

.rule-item {
  margin-bottom: 12px;
  padding: 8px;
  background: #fff;
  border-radius: 4px;
  border: 1px solid #e4e7ed;
}

.rule-item:last-child {
  margin-bottom: 8px;
}

.template-library {
  max-height: 400px;
  overflow-y: auto;
}

.template-item {
  border: 1px solid #e4e7ed;
  border-radius: 6px;
  padding: 16px;
  margin-bottom: 12px;
  background: #fff;
}

.template-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.template-header h4 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
}

.template-description {
  margin: 0 0 12px 0;
  color: #666;
  font-size: 14px;
  line-height: 1.5;
}

.template-actions {
  display: flex;
  gap: 8px;
}

.empty-state {
  text-align: center;
  padding: 40px 0;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .page-header {
    flex-direction: column;
    gap: 16px;
  }
  
  .header-actions {
    width: 100%;
    justify-content: flex-end;
  }
  
  .policies-container {
    grid-template-columns: 1fr;
  }
  
  .policy-header {
    flex-direction: column;
    gap: 12px;
  }
  
  .policy-actions {
    justify-content: flex-end;
  }
}
</style>