<template>
  <div class="alert-templates-page">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-left">
        <h2>{{ $t('alertTemplates.title') }}</h2>
        <p class="page-description">
          {{ $t('alertTemplates.description') }}
        </p>
      </div>
      <div class="header-actions">
        <el-button type="primary" @click="showCreateDialog = true">
          <el-icon>
            <Plus />
          </el-icon>
          {{ $t('alertTemplates.createTemplate') }}
        </el-button>
        <el-button @click="loadTemplates">
          <el-icon>
            <Refresh />
          </el-icon>
          {{ $t('alertTemplates.refresh') }}
        </el-button>
      </div>
    </div>

    <!-- 筛选栏 -->
    <div class="filter-bar">
      <el-form :model="filters" inline>
        <el-form-item :label="$t('alertTemplates.templateCategory')">
          <el-select v-model="filters.category" :placeholder="$t('alertTemplates.selectCategory')" clearable
            @change="loadTemplates">
            <el-option :label="$t('alertTemplates.categories.email')" value="email" />
            <el-option :label="$t('alertTemplates.categories.sms')" value="sms" />
            <el-option :label="$t('alertTemplates.categories.dingtalk')" value="dingtalk" />
            <el-option :label="$t('alertTemplates.categories.wechat')" value="wechat" />
            <el-option :label="$t('alertTemplates.categories.webhook')" value="webhook" />
          </el-select>
        </el-form-item>
        <el-form-item :label="$t('alertTemplates.templateType')">
          <el-select v-model="filters.template_type" :placeholder="$t('alertTemplates.selectType')" clearable
            @change="loadTemplates">
            <el-option :label="$t('alertTemplates.categories.email')" value="email" />
            <el-option :label="$t('alertTemplates.categories.sms')" value="sms" />
            <el-option :label="$t('alertTemplates.categories.dingtalk')" value="dingtalk" />
            <el-option :label="$t('alertTemplates.categories.wechat')" value="wechat" />
            <el-option :label="$t('alertTemplates.categories.webhook')" value="webhook" />
          </el-select>
        </el-form-item>
        <el-form-item :label="$t('alertTemplates.templateName')">
          <el-input v-model="filters.keyword" :placeholder="$t('alertTemplates.searchTemplateName')" clearable
            @keyup.enter="loadTemplates">
            <template #prefix>
              <el-icon>
                <Search />
              </el-icon>
            </template>
          </el-input>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="loadTemplates">
            <el-icon>
              <Search />
            </el-icon>
            {{ $t('common.search') }}
          </el-button>
          <el-button @click="resetFilter">{{ $t('common.reset') }}</el-button>
        </el-form-item>
      </el-form>
    </div>

    <!-- 模板列表 -->
    <div class="templates-container">
      <el-table :data="filteredTemplates" style="width: 100%" @selection-change="handleSelectionChange"
        v-loading="loading">
        <el-table-column type="selection" width="55" />

        <el-table-column prop="name" :label="$t('alertTemplates.templateName')" sortable>
          <template #default="{ row }">
            <el-link type="primary" @click="showTemplateDetail(row)">
              {{ row.name }}
            </el-link>
          </template>
        </el-table-column>

        <el-table-column prop="category" :label="$t('alertTemplates.templateCategory')" sortable>
          <template #default="{ row }">
            <el-tag size="small">{{ row.category }}</el-tag>
          </template>
        </el-table-column>

        <el-table-column prop="template_type" :label="$t('alertTemplates.templateType')" sortable>
          <template #default="{ row }">
            <el-tag :type="getTemplateTypeColor(row.template_type)" size="small">
              {{ row.template_type }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column :label="$t('alertTemplates.templateProperty')" width="180" sortable>
          <template #default="{ row }">
            <div class="template-status">
              <el-tag v-if="row.is_system" type="success" size="small">{{ $t('alertTemplates.system') }}</el-tag>
              <el-tag v-if="row.is_default" type="warning" size="small">{{ $t('alertTemplates.default') }}</el-tag>
              <span v-if="!row.is_system && !row.is_default" class="custom-tag">{{ $t('alertTemplates.custom') }}</span>
            </div>
          </template>
        </el-table-column>

        <el-table-column :label="$t('alertTemplates.usageCount')" sortable>
          <template #default="{ row }">
            {{ row.usage_count || 0 }}
          </template>
        </el-table-column>

        <el-table-column :label="$t('alertTemplates.variableCount')" sortable>
          <template #default="{ row }">
            {{ row.variables?.length || 0 }}
          </template>
        </el-table-column>

        <el-table-column prop="created_at" :label="$t('common.createTime')" width="220" sortable>
          <template #default="{ row }">
            <div class="time-display">
              <div>{{ formatDate(row.created_at).split(" ")[0] }}</div>
              <div class="time">
                {{ formatDate(row.created_at).split(" ")[1] }}
              </div>
            </div>
          </template>
        </el-table-column>

        <el-table-column :label="$t('common.actions')" width="220" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="previewTemplate(row)">{{ $t('alertTemplates.preview') }}</el-button>
            <el-button size="small" @click="editTemplate(row)">{{ $t('common.edit') }}</el-button>
            <el-button v-if="!row.is_system" size="small" type="danger" @click="deleteTemplate(row)">
              {{ $t('common.delete') }}
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <div v-if="filteredTemplates.length === 0" class="empty-state">
        <el-empty :description="$t('alertTemplates.noTemplates')" />
      </div>
    </div>

    <!-- 创建/编辑模板对话框 -->
    <el-dialog v-model="showCreateDialog"
      :title="editingTemplate ? $t('alertTemplates.editTemplate') : $t('alertTemplates.createTemplate')" width="35%"
      @close="resetForm">
      <el-form ref="templateFormRef" :model="templateForm" :rules="templateRules" label-width="120px">
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item :label="$t('alertTemplates.templateName')" prop="name">
              <el-input v-model="templateForm.name" :placeholder="$t('alertTemplates.enterTemplateName')" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item :label="$t('alertTemplates.templateCategory')" prop="category">
              <el-select v-model="templateForm.category" :placeholder="$t('alertTemplates.selectCategory')">
                <el-option :label="$t('alertTemplates.categories.email')" value="email" />
                <el-option :label="$t('alertTemplates.categories.sms')" value="sms" />
                <el-option :label="$t('alertTemplates.categories.dingtalk')" value="dingtalk" />
                <el-option :label="$t('alertTemplates.categories.wechat')" value="wechat" />
                <el-option :label="$t('alertTemplates.categories.webhook')" value="webhook" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item :label="$t('alertTemplates.templateDescription')" prop="description">
          <el-input v-model="templateForm.description" type="textarea" :rows="3"
            :placeholder="$t('alertTemplates.enterDescription')" />
        </el-form-item>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item :label="$t('alertTemplates.templateType')" prop="template_type">
              <el-select v-model="templateForm.template_type" :placeholder="$t('alertTemplates.selectType')">
                <el-option :label="$t('alertTemplates.categories.email')" value="email" />
                <el-option :label="$t('alertTemplates.categories.sms')" value="sms" />
                <el-option :label="$t('alertTemplates.categories.dingtalk')" value="dingtalk" />
                <el-option :label="$t('alertTemplates.categories.wechat')" value="wechat" />
                <el-option :label="$t('alertTemplates.categories.webhook')" value="webhook" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>

        <!-- 模板内容配置 -->
        <el-divider content-position="left">{{ $t('alertTemplates.templateContentConfig') }}</el-divider>

        <el-form-item :label="$t('alertTemplates.titleTemplate')" prop="title_template">
          <el-input v-model="templateForm.title_template" :placeholder="$t('alertTemplates.enterTitleTemplate')" />
        </el-form-item>

        <el-form-item :label="$t('alertTemplates.contentTemplate')" prop="content_template">
          <el-input v-model="templateForm.content_template" type="textarea" :rows="8"
            :placeholder="$t('alertTemplates.enterContentTemplate')" />
        </el-form-item>

        <!-- 变量配置 -->
        <el-divider content-position="left">{{ $t('alertTemplates.variableConfig') }}</el-divider>

        <el-form-item :label="$t('alertTemplates.supportedVariables')">
          <el-select v-model="templateForm.variables" multiple :placeholder="$t('alertTemplates.selectVariables')">
            <el-option :label="$t('alertTemplates.alertName')" value="alert_name" />
            <el-option :label="$t('alertTemplates.alertLevel')" value="severity" />
            <el-option :label="$t('alertTemplates.resourceName')" value="resource_name" />
            <el-option :label="$t('alertTemplates.currentValue')" value="current_value" />
            <el-option :label="$t('alertTemplates.threshold')" value="threshold" />
            <el-option :label="$t('alertTemplates.triggeredAt')" value="triggered_at" />
            <el-option :label="$t('alertTemplates.description')" value="description" />
            <el-option :label="$t('alertTemplates.nodeName')" value="node_name" />
            <el-option :label="$t('alertTemplates.clientName')" value="client_name" />
            <el-option :label="$t('alertTemplates.storageName')" value="storage_name" />
          </el-select>
        </el-form-item>

        <!-- 模板预览 -->
        <el-divider content-position="left">{{ $t('alertTemplates.templatePreview') }}</el-divider>

        <el-form-item :label="$t('alertTemplates.testVariables')">
          <el-button @click="generateTestVariables" size="small">{{ $t('alertTemplates.generateTestData') }}</el-button>
        </el-form-item>

        <div class="preview-section">
          <div class="preview-item">
            <strong>{{ $t('alertTemplates.titlePreview') }}:</strong>
            <div class="preview-content">{{ previewData.title }}</div>
          </div>
          <div class="preview-item">
            <strong>{{ $t('alertTemplates.contentPreview') }}:</strong>
            <div class="preview-content">{{ previewData.content }}</div>
          </div>
        </div>
      </el-form>

      <template #footer>
        <el-button @click="showCreateDialog = false">{{ $t('common.cancel') }}</el-button>
        <el-button type="primary" @click="saveTemplate" :loading="saving">
          {{ editingTemplate ? $t('common.update') : $t('common.create') }}
        </el-button>
      </template>
    </el-dialog>

    <!-- 预览对话框 -->
    <el-dialog v-model="showPreviewDialog" :title="$t('alertTemplates.templatePreview')" width="30%">
      <div class="preview-dialog-content">
        <div class="preview-section">
          <h4>{{ $t('alertTemplates.title') }}:</h4>
          <div class="preview-text">{{ previewData.title }}</div>
        </div>
        <div class="preview-section">
          <h4>{{ $t('alertTemplates.content') }}:</h4>
          <div class="preview-text">{{ previewData.content }}</div>
        </div>
      </div>
    </el-dialog>

    <!-- 模板详情侧拉抽屉 -->
    <el-drawer v-model="showTemplateDetailDrawer" :title="$t('alertTemplates.templateDetails')" direction="rtl"
      size="50%">
      <div v-if="selectedTemplate" class="template-detail">
        <div class="detail-section">
          <h3>{{ $t('alertTemplates.basicInfo') }}</h3>
          <div class="detail-item">
            <span class="label">{{ $t('alertTemplates.templateName') }}:</span>
            <span class="value">{{ selectedTemplate.name }}</span>
          </div>
          <div class="detail-item">
            <span class="label">{{ $t('alertTemplates.templateDescription') }}:</span>
            <span class="value">{{
              selectedTemplate.description || $t('alertTemplates.noDescription')
            }}</span>
          </div>
          <div class="detail-item">
            <span class="label">{{ $t('alertTemplates.templateCategory') }}:</span>
            <span class="value">
              <el-tag size="small">{{ selectedTemplate.category }}</el-tag>
            </span>
          </div>
          <div class="detail-item">
            <span class="label">{{ $t('alertTemplates.templateType') }}:</span>
            <span class="value">
              <el-tag :type="getTemplateTypeColor(selectedTemplate.template_type)" size="small">
                {{ selectedTemplate.template_type }}
              </el-tag>
            </span>
          </div>
          <div class="detail-item">
            <span class="label">{{ $t('alertTemplates.templateStatus') }}:</span>
            <span class="value">
              <el-tag v-if="selectedTemplate.is_system" type="success" size="small">{{ $t('alertTemplates.system')
                }}</el-tag>
              <el-tag v-if="selectedTemplate.is_default" type="warning" size="small">{{ $t('alertTemplates.default')
                }}</el-tag>
              <span v-if="
                !selectedTemplate.is_system && !selectedTemplate.is_default
              " class="custom-tag">{{ $t('alertTemplates.custom') }}</span>
            </span>
          </div>
        </div>

        <div class="detail-section">
          <h3>{{ $t('alertTemplates.templateContent') }}</h3>
          <div class="detail-item">
            <span class="label">{{ $t('alertTemplates.titleTemplate') }}:</span>
            <div class="value template-content">
              {{ selectedTemplate.title_template }}
            </div>
          </div>
          <div class="detail-item">
            <span class="label">{{ $t('alertTemplates.contentTemplate') }}:</span>
            <div class="value template-content">
              {{ selectedTemplate.content_template }}
            </div>
          </div>
        </div>

        <div class="detail-section" v-if="
          selectedTemplate.variables && selectedTemplate.variables.length > 0
        ">
          <h3>{{ $t('alertTemplates.supportedVariables') }}</h3>
          <div class="detail-item">
            <span class="label">{{ $t('alertTemplates.variableList') }}:</span>
            <div class="value">
              <el-tag v-for="variable in selectedTemplate.variables" :key="variable" size="small" type="info"
                style="margin-right: 8px; margin-bottom: 4px">
                {{ "{" + variable + "}" }}
              </el-tag>
            </div>
          </div>
        </div>

        <div class="detail-section">
          <h3>{{ $t('alertTemplates.usageStats') }}</h3>
          <div class="detail-item">
            <span class="label">{{ $t('alertTemplates.usageCount') }}:</span>
            <span class="value">{{ selectedTemplate.usage_count || 0 }}{{ $t('alertTemplates.times') }}</span>
          </div>
          <div class="detail-item">
            <span class="label">{{ $t('common.createTime') }}:</span>
            <span class="value">{{
              formatDate(selectedTemplate.created_at)
              }}</span>
          </div>
          <div class="detail-item">
            <span class="label">{{ $t('common.updateTime') }}:</span>
            <span class="value">{{
              formatDate(selectedTemplate.updated_at)
              }}</span>
          </div>
        </div>

        <div class="detail-actions">
          <el-button type="primary" @click="editTemplate(selectedTemplate)">{{ $t('alertTemplates.editTemplate')
          }}</el-button>
          <el-button @click="previewTemplate(selectedTemplate)">{{ $t('alertTemplates.preview') }}</el-button>
          <el-button v-if="!selectedTemplate.is_system" type="danger" @click="deleteTemplate(selectedTemplate)">
            {{ $t('common.delete') }}
          </el-button>
        </div>
      </div>
    </el-drawer>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, watch } from "vue";
import { ElMessage, ElMessageBox } from "element-plus";
import { Plus, Refresh, Search } from "@element-plus/icons-vue";
import { useI18n } from "vue-i18n";
import axios from "axios";

const { t } = useI18n();

// 响应式数据
const loading = ref(false);
const templates = ref([]);
const templateFormRef = ref(null);
const filters = reactive({
  category: "",
  template_type: "",
  keyword: "",
});

const showCreateDialog = ref(false);
const showPreviewDialog = ref(false);
const showTemplateDetailDrawer = ref(false);
const editingTemplate = ref(null);
const selectedTemplate = ref(null);
const saving = ref(false);

// 表单数据
const templateForm = reactive({
  name: "",
  description: "",
  category: "",
  template_type: "",
  title_template: "",
  content_template: "",
  variables: [],
  variable_descriptions: {},
});

// 预览数据
const previewData = reactive({
  title: "",
  content: "",
});

// 表单验证规则
const templateRules = {
  name: [{ required: true, message: t('alertTemplates.enterTemplateName'), trigger: "blur" }],
  category: [{ required: true, message: t('alertTemplates.selectCategory'), trigger: "change" }],
  template_type: [
    { required: true, message: t('alertTemplates.selectType'), trigger: "change" },
  ],
  title_template: [
    { required: true, message: t('alertTemplates.enterTitleTemplate'), trigger: "blur" },
  ],
  content_template: [
    { required: true, message: t('alertTemplates.enterContentTemplate'), trigger: "blur" },
  ],
};

// 计算属性
const filteredTemplates = computed(() => {
  let result = templates.value;

  if (filters.category) {
    result = result.filter(
      (template) => template.category === filters.category
    );
  }

  if (filters.template_type) {
    result = result.filter(
      (template) => template.template_type === filters.template_type
    );
  }

  if (filters.keyword) {
    const keyword = filters.keyword.toLowerCase();
    result = result.filter(
      (template) =>
        template.name.toLowerCase().includes(keyword) ||
        template.description?.toLowerCase().includes(keyword)
    );
  }

  return result;
});

// 方法
const loadTemplates = async () => {
  try {
    loading.value = true;
    const params = {};
    if (filters.category) params.category = filters.category;
    if (filters.template_type) params.template_type = filters.template_type;

    const response = await axios.get("/api/alerts/templates", { params });
    templates.value = response.data.templates || [];
  } catch (error) {
    ElMessage.error(t('alertTemplates.loadTemplatesFailed'));
  } finally {
    loading.value = false;
  }
};

const resetFilter = () => {
  filters.category = "";
  filters.template_type = "";
  filters.keyword = "";
  loadTemplates();
};

const showTemplateDetail = (template) => {
  selectedTemplate.value = template;
  showTemplateDetailDrawer.value = true;
};

const editTemplate = (template) => {
  editingTemplate.value = template;
  Object.assign(templateForm, template);
  showCreateDialog.value = true;
};

const previewTemplate = async (template) => {
  try {
    // 生成测试变量
    const testVariables = {
      alert_name: t('alertTemplates.testData.alertName'),
      severity: "warning",
      resource_name: t('alertTemplates.testData.resourceName'),
      current_value: "85%",
      threshold: "80%",
      triggered_at: "2024-01-15 10:30:00",
      description: t('alertTemplates.testData.description'),
    };

    const response = await axios.post(
      `/api/alerts/templates/${template.id}/render`,
      {
        variables: testVariables,
      }
    );

    Object.assign(previewData, response.data.data);
    showPreviewDialog.value = true;
  } catch (error) {
    ElMessage.error(t('alertTemplates.previewFailed'));
  }
};

const saveTemplate = async () => {
  try {
    // 表单验证
    if (!templateFormRef.value) return;

    const valid = await templateFormRef.value.validate();
    if (!valid) {
      ElMessage.error(t('alertTemplates.checkFormError'));
      return;
    }

    saving.value = true;

    const data = { ...templateForm };
    if (editingTemplate.value) {
      await axios.put(
        `/api/alerts/templates/${editingTemplate.value.id}`,
        data
      );
      ElMessage.success(t('alertTemplates.updateSuccess'));
    } else {
      await axios.post("/api/alerts/templates", data);
      ElMessage.success(t('alertTemplates.createSuccess'));
    }

    showCreateDialog.value = false;
    loadTemplates();
  } catch (error) {
    ElMessage.error(t('alertTemplates.saveFailed'));
  } finally {
    saving.value = false;
  }
};

const deleteTemplate = async (template) => {
  try {
    await ElMessageBox.confirm(
      t('alertTemplates.confirmDelete', { name: template.name }),
      t('common.confirmDelete'),
      { type: "warning" }
    );

    await axios.delete(`/api/alerts/templates/${template.id}`);
    ElMessage.success(t('alertTemplates.deleteSuccess'));
    loadTemplates();
  } catch (error) {
    if (error !== "cancel") {
      ElMessage.error(t('alertTemplates.deleteFailed'));
    }
  }
};

const resetForm = () => {
  editingTemplate.value = null;
  Object.assign(templateForm, {
    name: "",
    description: "",
    category: "",
    template_type: "",
    title_template: "",
    content_template: "",
    variables: [],
    variable_descriptions: {},
  });

  // 重置表单验证
  if (templateFormRef.value) {
    templateFormRef.value.clearValidate();
  }
};

const getTemplateTypeColor = (type) => {
  const colors = {
    email: "primary",
    sms: "success",
    dingtalk: "warning",
    wechat: "info",
    webhook: "danger",
  };
  return colors[type] || "";
};

const generateTestVariables = () => {
  // 生成测试变量数据
  const testVariables = {
    alert_name: t('alertTemplates.testData.alertName'),
    severity: "warning",
    resource_name: t('alertTemplates.testData.resourceName'),
    current_value: "85%",
    threshold: "80%",
    triggered_at: "2024-01-15 10:30:00",
    description: t('alertTemplates.testData.description'),
    node_name: t('alertTemplates.testData.nodeName'),
    client_name: t('alertTemplates.testData.clientName'),
    storage_name: t('alertTemplates.testData.storageName'),
  };

  // 更新预览
  updatePreview(testVariables);
};

const updatePreview = (variables) => {
  let title = templateForm.title_template;
  let content = templateForm.content_template;

  // 替换变量
  for (const [key, value] of Object.entries(variables)) {
    const placeholder = `{${key}}`;
    title = title.replace(new RegExp(placeholder, "g"), value);
    content = content.replace(new RegExp(placeholder, "g"), value);
  }

  previewData.title = title;
  previewData.content = content;
};

const formatDate = (date) => {
  if (!date) return "-";
  return new Date(date).toLocaleString("zh-CN");
};

// 监听器
watch(
  [() => templateForm.title_template, () => templateForm.content_template],
  () => {
    if (templateForm.title_template || templateForm.content_template) {
      generateTestVariables();
    }
  },
  { deep: true }
);

// 生命周期
onMounted(() => {
  loadTemplates();
});
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

:deep(.el-table__header) {
  width: 100% !important;
}

:deep(.el-table__header th) {
  background: var(--bg-secondary);
  color: var(--text-secondary);
  font-weight: 600;
  border-bottom: 1px solid var(--border-color);
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
