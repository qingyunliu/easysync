<template>
  <div class="alert-templates-page">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-left">
        <h2>告警通知模板管理</h2>
        <p class="page-description">管理系统告警通知模板，支持邮件、短信、钉钉等多种通知方式</p>
      </div>
      <div class="header-actions">
        <el-button type="primary" @click="showCreateDialog = true">
          <el-icon><Plus /></el-icon>
          创建模板
        </el-button>
        <el-button @click="loadTemplates">
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
      </div>
    </div>

    <!-- 筛选栏 -->
    <div class="filter-bar">
      <el-form :model="filters" inline>
        <el-form-item label="模板分类">
          <el-select v-model="filters.category" placeholder="选择分类" clearable @change="loadTemplates">
            <el-option label="邮件" value="email" />
            <el-option label="短信" value="sms" />
            <el-option label="钉钉" value="dingtalk" />
            <el-option label="企业微信" value="wechat" />
            <el-option label="Webhook" value="webhook" />
          </el-select>
        </el-form-item>
        <el-form-item label="模板类型">
          <el-select v-model="filters.template_type" placeholder="选择类型" clearable @change="loadTemplates">
            <el-option label="邮件" value="email" />
            <el-option label="短信" value="sms" />
            <el-option label="钉钉" value="dingtalk" />
            <el-option label="企业微信" value="wechat" />
            <el-option label="Webhook" value="webhook" />
          </el-select>
        </el-form-item>
        <el-form-item label="模板名称">
          <el-input
            v-model="filters.keyword"
            placeholder="搜索模板名称"
            clearable
            @keyup.enter="loadTemplates"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="loadTemplates">
            <el-icon><Search /></el-icon>
            搜索
          </el-button>
          <el-button @click="resetFilter">重置</el-button>
        </el-form-item>
      </el-form>
    </div>

    <!-- 模板列表 -->
    <div class="templates-container">
      <el-table 
        :data="filteredTemplates" 
        style="width: 100%"
        @selection-change="handleSelectionChange"
        v-loading="loading"
      >
        <el-table-column type="selection" width="55" />
        
        <el-table-column prop="name" label="模板名称" sortable>
          <template #default="{ row }">
            <el-link type="primary" @click="showTemplateDetail(row)">
              {{ row.name }}
            </el-link>
          </template>
        </el-table-column>
        
        <el-table-column prop="category" label="模板分类" sortable>
          <template #default="{ row }">
            <el-tag size="small">{{ row.category }}</el-tag>
          </template>
        </el-table-column>
        
        <el-table-column prop="template_type" label="模板类型" sortable>
          <template #default="{ row }">
            <el-tag :type="getTemplateTypeColor(row.template_type)" size="small">
              {{ row.template_type }}
            </el-tag>
          </template>
        </el-table-column>
        
        <el-table-column label="模板状态" sortable>
          <template #default="{ row }">
            <div class="template-status">
              <el-tag v-if="row.is_system" type="success" size="small">系统</el-tag>
              <el-tag v-if="row.is_default" type="warning" size="small">默认</el-tag>
              <span v-if="!row.is_system && !row.is_default" class="custom-tag">自定义</span>
            </div>
          </template>
        </el-table-column>
        
        <el-table-column label="使用次数" sortable>
          <template #default="{ row }">
            {{ row.usage_count || 0 }}
          </template>
        </el-table-column>
        
        <el-table-column label="变量数量" sortable>
          <template #default="{ row }">
            {{ row.variables?.length || 0 }}
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
            <el-button size="small" @click="previewTemplate(row)">预览</el-button>
            <el-button size="small" @click="editTemplate(row)">编辑</el-button>
            <el-button 
              v-if="!row.is_system"
              size="small" 
              type="danger" 
              @click="deleteTemplate(row)"
            >
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
      
      <div v-if="filteredTemplates.length === 0" class="empty-state">
        <el-empty description="暂无告警模板" />
      </div>
    </div>

    <!-- 创建/编辑模板对话框 -->
    <el-dialog
      v-model="showCreateDialog"
      :title="editingTemplate ? '编辑模板' : '创建模板'"
      width="35%"
      @close="resetForm"
    >
      <el-form ref="templateFormRef" :model="templateForm" :rules="templateRules" label-width="120px">
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="模板名称" prop="name">
              <el-input v-model="templateForm.name" placeholder="请输入模板名称" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="模板分类" prop="category">
              <el-select v-model="templateForm.category" placeholder="选择分类">
                <el-option label="邮件" value="email" />
                <el-option label="短信" value="sms" />
                <el-option label="钉钉" value="dingtalk" />
                <el-option label="企业微信" value="wechat" />
                <el-option label="Webhook" value="webhook" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-form-item label="模板描述" prop="description">
          <el-input
            v-model="templateForm.description"
            type="textarea"
            :rows="3"
            placeholder="请输入模板描述"
          />
        </el-form-item>
        
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="模板类型" prop="template_type">
              <el-select v-model="templateForm.template_type" placeholder="选择模板类型">
                <el-option label="邮件" value="email" />
                <el-option label="短信" value="sms" />
                <el-option label="钉钉" value="dingtalk" />
                <el-option label="企业微信" value="wechat" />
                <el-option label="Webhook" value="webhook" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        
        <!-- 模板内容配置 -->
        <el-divider content-position="left">模板内容配置</el-divider>
        
        <el-form-item label="标题模板" prop="title_template">
          <el-input
            v-model="templateForm.title_template"
            placeholder="请输入标题模板，支持变量如 {alert_name} {severity}"
          />
        </el-form-item>
        
        <el-form-item label="内容模板" prop="content_template">
          <el-input
            v-model="templateForm.content_template"
            type="textarea"
            :rows="8"
            placeholder="请输入内容模板，支持变量如 {alert_name} {severity} {resource_name} {current_value} {threshold} {triggered_at} {description}"
          />
        </el-form-item>
        
        <!-- 变量配置 -->
        <el-divider content-position="left">变量配置</el-divider>
        
        <el-form-item label="支持变量">
          <el-select v-model="templateForm.variables" multiple placeholder="选择支持的变量">
            <el-option label="告警名称" value="alert_name" />
            <el-option label="告警级别" value="severity" />
            <el-option label="资源名称" value="resource_name" />
            <el-option label="当前值" value="current_value" />
            <el-option label="阈值" value="threshold" />
            <el-option label="触发时间" value="triggered_at" />
            <el-option label="告警描述" value="description" />
            <el-option label="节点名称" value="node_name" />
            <el-option label="客户端名称" value="client_name" />
            <el-option label="存储名称" value="storage_name" />
          </el-select>
        </el-form-item>
        
        <!-- 模板预览 -->
        <el-divider content-position="left">模板预览</el-divider>
        
        <el-form-item label="测试变量">
          <el-button @click="generateTestVariables" size="small">生成测试数据</el-button>
        </el-form-item>
        
        <div class="preview-section">
          <div class="preview-item">
            <strong>标题预览:</strong>
            <div class="preview-content">{{ previewData.title }}</div>
          </div>
          <div class="preview-item">
            <strong>内容预览:</strong>
            <div class="preview-content">{{ previewData.content }}</div>
          </div>
        </div>
      </el-form>
      
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" @click="saveTemplate" :loading="saving">
          {{ editingTemplate ? '更新' : '创建' }}
        </el-button>
      </template>
    </el-dialog>

    <!-- 预览对话框 -->
    <el-dialog v-model="showPreviewDialog" title="模板预览" width="30%">
      <div class="preview-dialog-content">
        <div class="preview-section">
          <h4>标题:</h4>
          <div class="preview-text">{{ previewData.title }}</div>
        </div>
        <div class="preview-section">
          <h4>内容:</h4>
          <div class="preview-text">{{ previewData.content }}</div>
        </div>
      </div>
    </el-dialog>

    <!-- 模板详情侧拉抽屉 -->
    <el-drawer
      v-model="showTemplateDetailDrawer"
      title="模板详情"
      direction="rtl"
      size="50%"
    >
      <div v-if="selectedTemplate" class="template-detail">
        <div class="detail-section">
          <h3>基本信息</h3>
          <div class="detail-item">
            <span class="label">模板名称:</span>
            <span class="value">{{ selectedTemplate.name }}</span>
          </div>
          <div class="detail-item">
            <span class="label">模板描述:</span>
            <span class="value">{{ selectedTemplate.description || '暂无描述' }}</span>
          </div>
          <div class="detail-item">
            <span class="label">模板分类:</span>
            <span class="value">
              <el-tag size="small">{{ selectedTemplate.category }}</el-tag>
            </span>
          </div>
          <div class="detail-item">
            <span class="label">模板类型:</span>
            <span class="value">
              <el-tag :type="getTemplateTypeColor(selectedTemplate.template_type)" size="small">
                {{ selectedTemplate.template_type }}
              </el-tag>
            </span>
          </div>
          <div class="detail-item">
            <span class="label">模板状态:</span>
            <span class="value">
              <el-tag v-if="selectedTemplate.is_system" type="success" size="small">系统</el-tag>
              <el-tag v-if="selectedTemplate.is_default" type="warning" size="small">默认</el-tag>
              <span v-if="!selectedTemplate.is_system && !selectedTemplate.is_default" class="custom-tag">自定义</span>
            </span>
          </div>
        </div>

        <div class="detail-section">
          <h3>模板内容</h3>
          <div class="detail-item">
            <span class="label">标题模板:</span>
            <div class="value template-content">{{ selectedTemplate.title_template }}</div>
          </div>
          <div class="detail-item">
            <span class="label">内容模板:</span>
            <div class="value template-content">{{ selectedTemplate.content_template }}</div>
          </div>
        </div>

        <div class="detail-section" v-if="selectedTemplate.variables && selectedTemplate.variables.length > 0">
          <h3>支持变量</h3>
          <div class="detail-item">
            <span class="label">变量列表:</span>
            <div class="value">
              <el-tag 
                v-for="variable in selectedTemplate.variables" 
                :key="variable"
                size="small"
                type="info"
                style="margin-right: 8px; margin-bottom: 4px;"
              >
                {{ '{' + variable + '}' }}
              </el-tag>
            </div>
          </div>
        </div>

        <div class="detail-section">
          <h3>使用统计</h3>
          <div class="detail-item">
            <span class="label">使用次数:</span>
            <span class="value">{{ selectedTemplate.usage_count || 0 }}次</span>
          </div>
          <div class="detail-item">
            <span class="label">创建时间:</span>
            <span class="value">{{ formatDate(selectedTemplate.created_at) }}</span>
          </div>
          <div class="detail-item">
            <span class="label">更新时间:</span>
            <span class="value">{{ formatDate(selectedTemplate.updated_at) }}</span>
          </div>
        </div>

        <div class="detail-actions">
          <el-button type="primary" @click="editTemplate(selectedTemplate)">编辑模板</el-button>
          <el-button @click="previewTemplate(selectedTemplate)">预览模板</el-button>
          <el-button 
            v-if="!selectedTemplate.is_system"
            type="danger" 
            @click="deleteTemplate(selectedTemplate)"
          >
            删除模板
          </el-button>
        </div>
      </div>
    </el-drawer>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Plus, Refresh, Search
} from '@element-plus/icons-vue'
import axios from 'axios'

// 响应式数据
const loading = ref(false)
const templates = ref([])
const templateFormRef = ref(null)
const filters = reactive({
  category: '',
  template_type: '',
  keyword: ''
})

const showCreateDialog = ref(false)
const showPreviewDialog = ref(false)
const showTemplateDetailDrawer = ref(false)
const editingTemplate = ref(null)
const selectedTemplate = ref(null)
const saving = ref(false)

// 表单数据
const templateForm = reactive({
  name: '',
  description: '',
  category: '',
  template_type: '',
  title_template: '',
  content_template: '',
  variables: [],
  variable_descriptions: {}
})

// 预览数据
const previewData = reactive({
  title: '',
  content: ''
})

// 表单验证规则
const templateRules = {
  name: [{ required: true, message: '请输入模板名称', trigger: 'blur' }],
  category: [{ required: true, message: '请选择模板分类', trigger: 'change' }],
  template_type: [{ required: true, message: '请选择模板类型', trigger: 'change' }],
  title_template: [{ required: true, message: '请输入标题模板', trigger: 'blur' }],
  content_template: [{ required: true, message: '请输入内容模板', trigger: 'blur' }]
}

// 计算属性
const filteredTemplates = computed(() => {
  let result = templates.value
  
  if (filters.category) {
    result = result.filter(template => template.category === filters.category)
  }
  
  if (filters.template_type) {
    result = result.filter(template => template.template_type === filters.template_type)
  }
  
  if (filters.keyword) {
    const keyword = filters.keyword.toLowerCase()
    result = result.filter(template => 
      template.name.toLowerCase().includes(keyword) ||
      template.description?.toLowerCase().includes(keyword)
    )
  }
  
  return result
})

// 方法
const loadTemplates = async () => {
  try {
    loading.value = true
    const params = {}
    if (filters.category) params.category = filters.category
    if (filters.template_type) params.template_type = filters.template_type
    
    const response = await axios.get('/api/alerts/templates', { params })
    templates.value = response.data.templates || []
  } catch (error) {
    ElMessage.error('加载模板列表失败')
  } finally {
    loading.value = false
  }
}

const resetFilter = () => {
  filters.category = ''
  filters.template_type = ''
  filters.keyword = ''
  loadTemplates()
}

const showTemplateDetail = (template) => {
  selectedTemplate.value = template
  showTemplateDetailDrawer.value = true
}

const editTemplate = (template) => {
  editingTemplate.value = template
  Object.assign(templateForm, template)
  showCreateDialog.value = true
}

const previewTemplate = async (template) => {
  try {
    // 生成测试变量
    const testVariables = {
      alert_name: 'CPU使用率告警',
      severity: 'warning',
      resource_name: '服务器-01',
      current_value: '85%',
      threshold: '80%',
      triggered_at: '2024-01-15 10:30:00',
      description: 'CPU使用率超过阈值，请及时处理'
    }
    
    const response = await axios.post(`/api/alerts/templates/${template.id}/render`, {
      variables: testVariables
    })
    
    Object.assign(previewData, response.data.data)
    showPreviewDialog.value = true
  } catch (error) {
    ElMessage.error('预览模板失败')
  }
}

const saveTemplate = async () => {
  try {
    // 表单验证
    if (!templateFormRef.value) return
    
    const valid = await templateFormRef.value.validate()
    if (!valid) {
      ElMessage.error('请检查表单填写是否正确')
      return
    }
    
    saving.value = true
    
    const data = { ...templateForm }
    if (editingTemplate.value) {
      await axios.put(`/api/alerts/templates/${editingTemplate.value.id}`, data)
      ElMessage.success('模板更新成功')
    } else {
      await axios.post('/api/alerts/templates', data)
      ElMessage.success('模板创建成功')
    }
    
    showCreateDialog.value = false
    loadTemplates()
  } catch (error) {
    ElMessage.error('保存模板失败')
  } finally {
    saving.value = false
  }
}

const deleteTemplate = async (template) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除模板 "${template.name}" 吗？`,
      '确认删除',
      { type: 'warning' }
    )
    
    await axios.delete(`/api/alerts/templates/${template.id}`)
    ElMessage.success('模板删除成功')
    loadTemplates()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除模板失败')
    }
  }
}

const resetForm = () => {
  editingTemplate.value = null
  Object.assign(templateForm, {
    name: '',
    description: '',
    category: '',
    template_type: '',
    title_template: '',
    content_template: '',
    variables: [],
    variable_descriptions: {}
  })
  
  // 重置表单验证
  if (templateFormRef.value) {
    templateFormRef.value.clearValidate()
  }
}

const getTemplateTypeColor = (type) => {
  const colors = {
    email: 'primary',
    sms: 'success',
    dingtalk: 'warning',
    wechat: 'info',
    webhook: 'danger'
  }
  return colors[type] || ''
}

const generateTestVariables = () => {
  // 生成测试变量数据
  const testVariables = {
    alert_name: 'CPU使用率告警',
    severity: 'warning',
    resource_name: '服务器-01',
    current_value: '85%',
    threshold: '80%',
    triggered_at: '2024-01-15 10:30:00',
    description: 'CPU使用率超过阈值，请及时处理',
    node_name: '节点-01',
    client_name: '客户端-01',
    storage_name: '存储-01'
  }
  
  // 更新预览
  updatePreview(testVariables)
}

const updatePreview = (variables) => {
  let title = templateForm.title_template
  let content = templateForm.content_template
  
  // 替换变量
  for (const [key, value] of Object.entries(variables)) {
    const placeholder = `{${key}}`
    title = title.replace(new RegExp(placeholder, 'g'), value)
    content = content.replace(new RegExp(placeholder, 'g'), value)
  }
  
  previewData.title = title
  previewData.content = content
}

const formatDate = (date) => {
  if (!date) return '-'
  return new Date(date).toLocaleString('zh-CN')
}

// 监听器
watch([() => templateForm.title_template, () => templateForm.content_template], () => {
  if (templateForm.title_template || templateForm.content_template) {
    generateTestVariables()
  }
}, { deep: true })

// 生命周期
onMounted(() => {
  loadTemplates()
})
</script>

<style scoped>
.alert-templates-page {
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

.templates-container {
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

.template-status {
  display: flex;
  gap: 4px;
}

.custom-tag {
  font-size: 12px;
  color: var(--text-secondary);
}

/* 侧拉抽屉样式 */
.template-detail {
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

.template-content {
  background: var(--card-bg);
  padding: 8px;
  border-radius: 4px;
  font-family: monospace;
  white-space: pre-wrap;
  word-break: break-all;
  margin-top: 4px;
}

.detail-actions {
  margin-top: 30px;
  padding-top: 20px;
  border-top: 1px solid #ebeef5;
  display: flex;
  gap: 10px;
}

.empty-state {
  text-align: center;
  padding: 60px 20px;
}

.preview-section {
  margin-bottom: 20px;
}

.preview-item {
  margin-bottom: 15px;
}

.preview-content {
  background: var(--card-bg);
  padding: 10px;
  border-radius: 4px;
  margin-top: 5px;
  white-space: pre-wrap;
  word-break: break-all;
  font-family: monospace;
}

.preview-dialog-content {
  padding: 20px 0;
}

.preview-dialog-content .preview-section {
  margin-bottom: 20px;
}

.preview-dialog-content .preview-text {
  background: var(--card-bg);
  padding: 15px;
  border-radius: 6px;
  margin-top: 10px;
  white-space: pre-wrap;
  word-break: break-all;
  font-family: monospace;
  line-height: 1.6;
}
</style> 