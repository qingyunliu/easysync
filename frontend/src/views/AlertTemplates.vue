<template>
  <div class="alert-templates">
    <div class="page-header">
      <h2>告警通知模板管理</h2>
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

    <!-- 筛选器 -->
    <div class="filter-section">
      <el-row :gutter="20">
        <el-col :span="6">
          <el-select v-model="filters.category" placeholder="选择分类" clearable @change="loadTemplates">
            <el-option label="邮件" value="email" />
            <el-option label="短信" value="sms" />
            <el-option label="钉钉" value="dingtalk" />
            <el-option label="企业微信" value="wechat" />
            <el-option label="Webhook" value="webhook" />
          </el-select>
        </el-col>
        <el-col :span="6">
          <el-select v-model="filters.template_type" placeholder="选择类型" clearable @change="loadTemplates">
            <el-option label="邮件" value="email" />
            <el-option label="短信" value="sms" />
            <el-option label="钉钉" value="dingtalk" />
            <el-option label="企业微信" value="wechat" />
            <el-option label="Webhook" value="webhook" />
          </el-select>
        </el-col>
        <el-col :span="6">
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
        </el-col>
        <el-col :span="6">
          <el-button type="primary" @click="loadTemplates">
            <el-icon><Search /></el-icon>
            搜索
          </el-button>
        </el-col>
      </el-row>
    </div>

    <!-- 模板列表 -->
    <div class="templates-grid">
      <el-row :gutter="20">
        <el-col
          v-for="template in templates"
          :key="template.id"
          :xs="24"
          :sm="12"
          :md="8"
          :lg="6"
        >
          <el-card class="template-card" :class="{ 'system-template': template.is_system }">
            <template #header>
              <div class="card-header">
                <div class="template-title">
                  <el-tag v-if="template.is_system" type="success" size="small">系统</el-tag>
                  <el-tag v-if="template.is_default" type="warning" size="small">默认</el-tag>
                  <span class="template-name">{{ template.name }}</span>
                </div>
                <div class="template-actions">
                  <el-dropdown @command="handleTemplateAction">
                    <el-button type="text" size="small">
                      <el-icon><MoreFilled /></el-icon>
                    </el-button>
                    <template #dropdown>
                      <el-dropdown-menu>
                        <el-dropdown-item :command="{ action: 'preview', template }">
                          <el-icon><View /></el-icon>
                          预览
                        </el-dropdown-item>
                        <el-dropdown-item :command="{ action: 'edit', template }">
                          <el-icon><Edit /></el-icon>
                          编辑
                        </el-dropdown-item>
                        <el-dropdown-item 
                          v-if="!template.is_system"
                          :command="{ action: 'delete', template }"
                          divided
                        >
                          <el-icon><Delete /></el-icon>
                          删除
                        </el-dropdown-item>
                      </el-dropdown-menu>
                    </template>
                  </el-dropdown>
                </div>
              </div>
            </template>
            
            <div class="template-content">
              <p class="template-description">{{ template.description }}</p>
              
              <div class="template-info">
                <div class="info-item">
                  <span class="label">分类:</span>
                  <el-tag size="small">{{ template.category }}</el-tag>
                </div>
                <div class="info-item">
                  <span class="label">类型:</span>
                  <el-tag :type="getTemplateTypeColor(template.template_type)" size="small">
                    {{ template.template_type }}
                  </el-tag>
                </div>
                <div class="info-item">
                  <span class="label">使用次数:</span>
                  <span>{{ template.usage_count || 0 }}</span>
                </div>
              </div>
              
              <div class="template-preview">
                <div class="preview-title">
                  <strong>标题预览:</strong>
                  <span class="preview-text">{{ template.title_template }}</span>
                </div>
                <div class="preview-content">
                  <strong>内容预览:</strong>
                  <div class="preview-text">{{ template.content_template }}</div>
                </div>
              </div>
              
              <div class="template-variables" v-if="template.variables && template.variables.length > 0">
                <div class="variables-title">
                  <strong>支持的变量:</strong>
                </div>
                <div class="variables-list">
                                     <el-tag 
                     v-for="variable in template.variables" 
                     :key="variable" 
                     size="small" 
                     type="info"
                     style="margin-right: 4px; margin-bottom: 4px;"
                   >
                     {{ '{' + variable + '}' }}
                   </el-tag>
                </div>
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>

    <!-- 创建/编辑模板对话框 -->
    <el-dialog
      v-model="showCreateDialog"
      :title="editingTemplate ? '编辑模板' : '创建模板'"
      width="70%"
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
    <el-dialog v-model="showPreviewDialog" title="模板预览" width="60%">
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
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Plus, Refresh, Search, MoreFilled, Edit, Delete, View
} from '@element-plus/icons-vue'
import axios from 'axios'

// 响应式数据
const templates = ref([])
const templateFormRef = ref(null)
const filters = reactive({
  category: '',
  template_type: '',
  keyword: ''
})

const showCreateDialog = ref(false)
const showPreviewDialog = ref(false)
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

// 方法
const loadTemplates = async () => {
  try {
    const params = {}
    if (filters.category) params.category = filters.category
    if (filters.template_type) params.template_type = filters.template_type
    
    const response = await axios.get('/api/alerts/templates', { params })
    templates.value = response.data.templates
  } catch (error) {
    ElMessage.error('加载模板列表失败')
  }
}

const handleTemplateAction = ({ action, template }) => {
  switch (action) {
    case 'preview':
      previewTemplate(template)
      break
    case 'edit':
      editingTemplate.value = template
      Object.assign(templateForm, template)
      showCreateDialog.value = true
      break
    case 'delete':
      deleteTemplate(template)
      break
  }
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
.alert-templates {
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.header-actions {
  display: flex;
  gap: 10px;
}

.filter-section {
  margin-bottom: 20px;
  padding: 20px;
  background: #f5f7fa;
  border-radius: 8px;
}

.templates-grid {
  margin-top: 20px;
}

.template-card {
  margin-bottom: 20px;
  transition: all 0.3s;
}

.template-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.system-template {
  border: 2px solid #67c23a;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.template-title {
  display: flex;
  align-items: center;
  gap: 8px;
}

.template-name {
  font-weight: bold;
}

.template-content {
  padding: 10px 0;
}

.template-description {
  color: #666;
  margin-bottom: 15px;
  line-height: 1.5;
}

.template-info {
  margin-bottom: 15px;
}

.info-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.label {
  font-weight: bold;
  color: #333;
}

.template-preview {
  border-top: 1px solid #eee;
  padding-top: 15px;
  margin-bottom: 15px;
}

.preview-title, .preview-content {
  margin-bottom: 10px;
}

.preview-text {
  color: #666;
  font-family: monospace;
  background: #f5f7fa;
  padding: 8px;
  border-radius: 4px;
  margin-top: 5px;
  white-space: pre-wrap;
  word-break: break-all;
}

.template-variables {
  border-top: 1px solid #eee;
  padding-top: 15px;
}

.variables-title {
  margin-bottom: 10px;
}

.variables-list {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.preview-section {
  margin-bottom: 20px;
}

.preview-item {
  margin-bottom: 15px;
}

.preview-content {
  background: #f5f7fa;
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
  background: #f5f7fa;
  padding: 15px;
  border-radius: 6px;
  margin-top: 10px;
  white-space: pre-wrap;
  word-break: break-all;
  font-family: monospace;
  line-height: 1.6;
}
</style> 