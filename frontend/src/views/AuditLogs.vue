<template>
  <div class="audit-logs-page">
    <div class="page-header">
      <h2>{{ $t('audit.title') }}</h2>
    </div>

    <div class="page-content">
      <el-tabs v-model="activeTab">
        <!-- 登录/登出审计 -->
        <el-tab-pane :label="$t('audit.loginAudit')" name="login">
          <div class="tab-header">
            <div class="header-actions">
              <el-select v-model="loginActionFilter" :placeholder="$t('audit.selectActionType')" class="filter-select"
                @change="handleLoginFilterChange">
                <el-option :label="$t('audit.allOperations')" value="all" />
                <el-option :label="$t('audit.loginRecord')" value="login" />
                <el-option :label="$t('audit.logoutRecord')" value="logout" />
              </el-select>
            </div>
          </div>

          <div class="data-card">
            <div class="card-header">
              <div class="card-title">
                <el-icon class="title-icon">
                  <DataAnalysis />
                </el-icon>
                <span>{{ $t('audit.loginLogoutAudit') }}</span>
              </div>
              <div class="card-stats">
                <span class="stats-text">{{ $t('audit.totalRecords', { count: loginTotal }) }}</span>
              </div>
            </div>

            <div class="table-container">
              <el-table :data="loginLogs" class="audit-table"
                :header-cell-style="{ background: 'var(--table-header-bg)', color: 'var(--text-color)' }" stripe
                @row-click="handleLoginRowClick">
                <el-table-column prop="id" :label="$t('audit.id')" width="330" align="center" />
                <el-table-column prop="username" :label="$t('audit.username')" width="160" align="center">
                  <template #default="scope">
                    <div class="user-info">
                      <el-avatar :size="28" style="margin-right: 8px">
                        {{ scope.row.username?.charAt(0)?.toUpperCase() }}
                      </el-avatar>
                      <span>{{ scope.row.username }}</span>
                    </div>
                  </template>
                </el-table-column>

                <el-table-column prop="action" :label="$t('audit.actionType')" width="120" align="center">
                  <template #default="scope">
                    <el-tag :type="scope.row.action === 'login' ? 'success' : 'warning'"
                      :icon="scope.row.action === 'login' ? 'CircleCheck' : 'CircleClose'" effect="light">
                      {{ scope.row.action === 'login' ? $t('audit.loginRecord') : $t('audit.logoutRecord') }}
                    </el-tag>
                  </template>
                </el-table-column>

                <el-table-column :label="$t('audit.operationTime')" width="220" align="center">
                  <template #default="scope">
                    <div class="time-info">
                      <el-icon class="time-icon">
                        <Clock />
                      </el-icon>
                      <span>{{ formatTime(scope.row.details.login_time || scope.row.details.logout_time) }}</span>
                    </div>
                  </template>
                </el-table-column>

                <el-table-column prop="result" :label="$t('audit.result')" width="100" align="center">
                  <template #default="scope">
                    <el-tag :type="scope.row.result === 'success' ? 'success' : 'danger'" effect="light" size="small">
                      {{ scope.row.result === 'success' ? $t('logs.success') : $t('logs.failed') }}
                    </el-tag>
                  </template>
                </el-table-column>

                <el-table-column prop="details.ip" :label="$t('audit.ipAddress')" width="180" align="center">
                  <template #default="scope">
                    <el-tag type="info" effect="plain" size="small">
                      {{ scope.row.details.ip }}
                    </el-tag>
                  </template>
                </el-table-column>

                <el-table-column prop="details.user_agent" :label="$t('audit.clientInfo')" min-width="200">
                  <template #default="scope">
                    <div class="user-agent-info">
                      <el-tooltip :content="scope.row.details.user_agent" placement="top">
                        <span class="user-agent-text">{{ formatUserAgent(scope.row.details.user_agent) }}</span>
                      </el-tooltip>
                    </div>
                  </template>
                </el-table-column>
              </el-table>

              <div class="pagination-wrapper">
                <el-pagination v-model:current-page="loginPage" :page-size="loginPerPage" :total="loginTotal"
                  layout="total, sizes, prev, pager, next, jumper" :page-sizes="[10, 20, 50, 100]"
                  @current-change="handleLoginPageChange" @size-change="handleLoginSizeChange" background />
              </div>
            </div>
          </div>
        </el-tab-pane>

        <!-- 常规操作审计 -->
        <el-tab-pane :label="$t('audit.operationAudit')" name="operation">
          <div class="tab-header">
            <div class="header-actions">
              <el-select v-model="operationActionFilter" :placeholder="$t('audit.selectActionType')"
                class="filter-select" @change="handleOperationFilterChange">
                <el-option :label="$t('audit.allOperations')" value="all" />
                <el-option :label="$t('audit.create')" value="create" />
                <el-option :label="$t('audit.update')" value="update" />
                <el-option :label="$t('audit.delete')" value="delete" />
                <el-option :label="$t('audit.read')" value="read" />
              </el-select>
              <el-select v-model="resourceTypeFilter" :placeholder="$t('audit.selectResourceType')"
                class="filter-select" @change="handleOperationFilterChange">
                <el-option :label="$t('audit.allResources')" value="all" />
                <el-option :label="$t('audit.user')" value="user" />
                <el-option :label="$t('audit.node')" value="node" />
                <el-option :label="$t('audit.storage')" value="storage" />
                <el-option :label="$t('audit.task')" value="task" />
                <el-option :label="$t('audit.client')" value="client" />
              </el-select>
            </div>
          </div>

          <div class="data-card">
            <div class="card-header">
              <div class="card-title">
                <el-icon class="title-icon">
                  <Operation />
                </el-icon>
                <span>{{ $t('audit.operationAuditLog') }}</span>
              </div>
              <div class="card-stats">
                <span class="stats-text">{{ $t('audit.totalRecords', { count: operationTotal }) }}</span>
              </div>
            </div>

            <div class="table-container">
              <el-table :data="operationLogs" class="audit-table"
                :header-cell-style="{ background: 'var(--table-header-bg)', color: 'var(--text-color)' }" stripe
                @row-click="handleOperationRowClick">
                <el-table-column prop="id" :label="$t('audit.id')" width="330" align="center" />

                <el-table-column prop="username" :label="$t('audit.username')" width="120" align="center">
                  <template #default="scope">
                    <div class="user-info">
                      <el-avatar :size="24" style="margin-right: 6px">
                        {{ scope.row.username?.charAt(0)?.toUpperCase() }}
                      </el-avatar>
                      <span>{{ scope.row.username }}</span>
                    </div>
                  </template>
                </el-table-column>

                <el-table-column prop="resource_name" :label="$t('audit.resourceName')" width="150" align="center">
                  <template #default="scope">
                    <span>{{ scope.row.resource_name || '-' }}</span>
                  </template>
                </el-table-column>

                <el-table-column prop="resource_type" :label="$t('audit.resourceType')" width="100" align="center">
                  <template #default="scope">
                    <el-tag :type="getResourceTypeColor(scope.row.resource_type)" effect="light" size="small">
                      {{ getResourceTypeLabel(scope.row.resource_type) }}
                    </el-tag>
                  </template>
                </el-table-column>

                <el-table-column prop="action" :label="$t('audit.actionType')" width="180" align="center">
                  <template #default="scope">
                    <el-tag :type="getActionTypeColor(scope.row.action)" effect="light" size="small">
                      {{ getActionLabel(scope.row.action) }}
                    </el-tag>
                  </template>
                </el-table-column>

                <el-table-column :label="$t('audit.operationTime')" width="180" align="center">
                  <template #default="scope">
                    <div class="time-info">
                      <el-icon class="time-icon">
                        <Clock />
                      </el-icon>
                      <span>{{ formatTime(scope.row.created_at) }}</span>
                    </div>
                  </template>
                </el-table-column>

                <el-table-column prop="result" :label="$t('audit.result')" width="100" align="center">
                  <template #default="scope">
                    <el-tag :type="scope.row.result === 'success' ? 'success' : 'danger'" effect="light" size="small">
                      {{ scope.row.result === 'success' ? $t('logs.success') : $t('logs.failed') }}
                    </el-tag>
                  </template>
                </el-table-column>

                <el-table-column prop="details" :label="$t('audit.details')" min-width="200">
                  <template #default="scope">
                    <div class="details-info">
                      <el-tooltip :content="JSON.stringify(scope.row.details, null, 2)" placement="top">
                        <span class="details-text">{{ formatDetails(scope.row.details) }}</span>
                      </el-tooltip>
                    </div>
                  </template>
                </el-table-column>
              </el-table>

              <div class="pagination-wrapper">
                <el-pagination v-model:current-page="operationPage" :page-size="operationPerPage"
                  :total="operationTotal" layout="total, sizes, prev, pager, next, jumper"
                  :page-sizes="[10, 20, 50, 100]" @current-change="handleOperationPageChange"
                  @size-change="handleOperationSizeChange" background />
              </div>
            </div>
          </div>
        </el-tab-pane>
      </el-tabs>
    </div>

    <!-- 审计日志详情抽屉 -->
    <el-drawer v-model="drawerVisible" :title="$t('audit.auditLogDetail')" direction="rtl" size="60%"
      :before-close="handleDrawerClose" class="audit-drawer">
      <div class="detail-content">

        <!-- 基本信息卡片 -->
        <el-card class="info-card">
          <template #header>
            <div class="card-header">
              <span>{{ $t('audit.basicInfo') }}</span>
            </div>
          </template>
          <el-descriptions :column="2" border>
            <el-descriptions-item :label="$t('audit.logId')">
              <el-tag type="info">{{ currentLog.id }}</el-tag>
            </el-descriptions-item>
            <el-descriptions-item :label="$t('audit.username')">
              <div class="user-info">
                <el-avatar :size="24" style="margin-right: 8px">
                  {{ currentLog.username?.charAt(0)?.toUpperCase() }}
                </el-avatar>
                <span>{{ currentLog.username }}</span>
              </div>
            </el-descriptions-item>
            <el-descriptions-item :label="$t('audit.actionType')">
              <el-tag :type="currentLog.action === 'login' ? 'success' :
                currentLog.action === 'logout' ? 'warning' :
                  getActionTypeColor(currentLog.action)" effect="light">
                {{ currentLog.action === 'login' ? $t('audit.loginRecord') :
                  currentLog.action === 'logout' ? $t('audit.logoutRecord') :
                    getActionLabel(currentLog.action) }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item :label="$t('audit.operationResult')">
              <el-tag :type="currentLog.result === 'success' ? 'success' : 'danger'" effect="light">
                {{ currentLog.result === 'success' ? $t('logs.success') : $t('logs.failed') }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item :label="$t('audit.operationTime')">
              {{ formatTime(currentLog.created_at || currentLog.details?.login_time || currentLog.details?.logout_time)
              }}
            </el-descriptions-item>
            <el-descriptions-item v-if="currentLog.resource_type" :label="$t('audit.resourceType')">
              <el-tag :type="getResourceTypeColor(currentLog.resource_type)" effect="light">
                {{ getResourceTypeLabel(currentLog.resource_type) }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item v-if="currentLog.resource_name" :label="$t('audit.resourceName')">
              {{ currentLog.resource_name }}
            </el-descriptions-item>
            <el-descriptions-item v-if="currentLog.resource_id" :label="$t('audit.resourceId')">
              <el-tag type="info" size="small">{{ currentLog.resource_id }}</el-tag>
            </el-descriptions-item>
          </el-descriptions>
        </el-card>

        <!-- 详细信息卡片 -->
        <el-card class="info-card" v-if="currentLog.details && hasDetailsContent(currentLog.details)">
          <template #header>
            <div class="card-header">
              <span>{{ $t('audit.details') }}</span>
            </div>
          </template>
          <el-descriptions :column="1" border>
            <el-descriptions-item v-if="currentLog.details.ip" :label="$t('audit.ipAddress')">
              <el-tag type="info" effect="plain">{{ currentLog.details.ip }}</el-tag>
            </el-descriptions-item>
            <el-descriptions-item v-if="currentLog.details.user_agent" :label="$t('audit.userAgent')">
              <div class="user-agent-detail">
                <span>{{ currentLog.details.user_agent }}</span>
              </div>
            </el-descriptions-item>
            <el-descriptions-item v-if="currentLog.details.path" :label="$t('audit.requestPath')">
              <el-tag type="info" effect="plain">{{ currentLog.details.path }}</el-tag>
            </el-descriptions-item>
            <el-descriptions-item v-if="currentLog.details.method" :label="$t('audit.requestMethod')">
              <el-tag type="info" effect="plain">{{ currentLog.details.method }}</el-tag>
            </el-descriptions-item>
            <el-descriptions-item v-if="currentLog.details.status_code" :label="$t('audit.statusCode')">
              <el-tag
                :type="currentLog.details.status_code >= 200 && currentLog.details.status_code < 300 ? 'success' : 'danger'"
                effect="light">
                {{ currentLog.details.status_code }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item v-if="currentLog.details.response_time" :label="$t('audit.responseTime')">
              <span>{{ currentLog.details.response_time }}ms</span>
            </el-descriptions-item>
            <el-descriptions-item v-if="currentLog.details.msg" :label="$t('audit.operationMessage')">
              <span>{{ currentLog.details.msg }}</span>
            </el-descriptions-item>
            <el-descriptions-item v-if="currentLog.details.username" :label="$t('audit.operationUsername')">
              <span>{{ currentLog.details.username }}</span>
            </el-descriptions-item>
            <el-descriptions-item v-if="currentLog.details.name" :label="$t('audit.resourceNameDetail')">
              <span>{{ currentLog.details.name }}</span>
            </el-descriptions-item>
            <el-descriptions-item v-if="currentLog.details.ip_address" :label="$t('audit.ipAddress')">
              <span>{{ currentLog.details.ip_address }}</span>
            </el-descriptions-item>
            <el-descriptions-item v-if="currentLog.details.status" :label="$t('audit.status')">
              <el-tag :type="currentLog.details.status === 'success' ? 'success' : 'danger'" effect="light">
                {{ currentLog.details.status }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item v-if="currentLog.details.error" :label="$t('audit.errorInfo')">
              <div class="error-detail">
                <el-tag type="danger" effect="light">{{ currentLog.details.error }}</el-tag>
              </div>
            </el-descriptions-item>
          </el-descriptions>
        </el-card>

        <!-- 操作审计详细信息卡片 -->
        <el-card class="info-card" v-if="currentLog.resource_type && currentLog.details">
          <template #header>
            <div class="card-header">
              <span>{{ $t('audit.operationDetails') }}</span>
              <el-button type="primary" link @click="toggleDetailsExpanded" size="small">
                {{ detailsExpanded ? $t('audit.collapse') : $t('audit.expand') }}
                <el-icon style="margin-left: 4px;">
                  <ArrowDown v-if="!detailsExpanded" />
                  <ArrowUp v-else />
                </el-icon>
              </el-button>
            </div>
          </template>

          <!-- 简化的详细信息 -->
          <div v-if="!detailsExpanded" class="details-summary">
            <div class="summary-item" v-if="currentLog.details.params">
              <span class="summary-label">{{ $t('audit.requestParams') }}:</span>
              <span class="summary-value">{{ getSummaryText(currentLog.details.params) }}</span>
            </div>
            <div class="summary-item" v-if="currentLog.details.headers">
              <span class="summary-label">{{ $t('audit.requestHeaders') }}:</span>
              <span class="summary-value">{{ getSummaryText(currentLog.details.headers) }}</span>
            </div>
            <div class="summary-item" v-if="currentLog.details.response">
              <span class="summary-label">{{ $t('audit.responseData') }}:</span>
              <span class="summary-value">{{ getSummaryText(currentLog.details.response) }}</span>
            </div>
            <div class="summary-item" v-if="currentLog.details.error">
              <span class="summary-label">{{ $t('audit.errorInfo') }}:</span>
              <span class="summary-value error-text">{{ currentLog.details.error }}</span>
            </div>
            <div
              v-if="!currentLog.details.params && !currentLog.details.headers && !currentLog.details.response && !currentLog.details.error"
              class="summary-item">
              <span class="summary-label">{{ $t('audit.details') }}:</span>
              <span class="summary-value">{{ getSummaryText(currentLog.details) }}</span>
            </div>
          </div>

          <!-- 展开的详细信息 -->
          <div v-else class="details-expanded">
            <el-collapse v-model="activeDetailsCollapse">
              <el-collapse-item v-if="currentLog.details.params" :title="$t('audit.requestParams')" name="params">
                <div class="json-detail">
                  <pre>{{ formatJSON(currentLog.details.params) }}</pre>
                </div>
              </el-collapse-item>

              <el-collapse-item v-if="currentLog.details.headers" :title="$t('audit.requestHeaders')" name="headers">
                <div class="json-detail">
                  <pre>{{ formatJSON(currentLog.details.headers) }}</pre>
                </div>
              </el-collapse-item>

              <el-collapse-item v-if="currentLog.details.response" :title="$t('audit.responseData')" name="response">
                <div class="json-detail">
                  <pre>{{ formatJSON(currentLog.details.response) }}</pre>
                </div>
              </el-collapse-item>

              <el-collapse-item v-if="currentLog.details.error" :title="$t('audit.errorInfo')" name="error">
                <div class="error-detail">
                  <el-tag type="danger" effect="light">{{ currentLog.details.error }}</el-tag>
                </div>
              </el-collapse-item>

              <el-collapse-item
                v-if="!currentLog.details.params && !currentLog.details.headers && !currentLog.details.response && !currentLog.details.error"
                :title="$t('audit.fullDetails')" name="full">
                <div class="json-detail">
                  <pre>{{ formatJSON(currentLog.details) }}</pre>
                </div>
              </el-collapse-item>
            </el-collapse>
          </div>
        </el-card>

        <!-- 环境信息卡片 -->
        <el-card class="info-card"
          v-if="currentLog.details && (currentLog.details.user_agent || currentLog.details.ip)">
          <template #header>
            <div class="card-header">
              <span>{{ $t('audit.environmentInfo') }}</span>
            </div>
          </template>
          <el-descriptions :column="2" border>
            <el-descriptions-item v-if="currentLog.details.session_id" :label="$t('audit.sessionId')">
              <el-tag type="info" size="small">{{ currentLog.details.session_id }}</el-tag>
            </el-descriptions-item>
            <el-descriptions-item v-if="currentLog.details.user_id" :label="$t('audit.userId')">
              <el-tag type="info" size="small">{{ currentLog.details.user_id }}</el-tag>
            </el-descriptions-item>
            <el-descriptions-item v-if="currentLog.details.user_agent" :label="$t('audit.clientType')">
              <el-tag type="info" effect="plain">{{ getClientType(currentLog.details.user_agent) }}</el-tag>
            </el-descriptions-item>
            <el-descriptions-item v-if="currentLog.details.user_agent" :label="$t('audit.operatingSystem')">
              <el-tag type="info" effect="plain">{{ getOSInfo(currentLog.details.user_agent) }}</el-tag>
            </el-descriptions-item>
            <el-descriptions-item v-if="currentLog.details.location" :label="$t('audit.location')">
              <span>{{ currentLog.details.location }}</span>
            </el-descriptions-item>
            <el-descriptions-item v-if="currentLog.details.timezone" :label="$t('audit.timezone')">
              <span>{{ currentLog.details.timezone }}</span>
            </el-descriptions-item>
          </el-descriptions>
        </el-card>

        <el-card class="info-card original-card" v-if="currentLog.id">
          <template #header>
            <div class="card-header">
              <span>{{ $t('audit.originalInfo') }}</span>
            </div>
          </template>
          <div class="original-content">
            <p><strong>{{ $t('audit.logData') }}:</strong></p>
            <pre>{{ JSON.stringify(currentLog, null, 2) }}</pre>
          </div>
        </el-card>
      </div>
    </el-drawer>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import axios from '@/utils/axios.mjs'
import { DataAnalysis, Clock, Operation, ArrowDown, ArrowUp } from '@element-plus/icons-vue'

const { t } = useI18n()

// 登录审计相关
const loginLogs = ref([])
const loginPage = ref(1)
const loginPerPage = ref(10)
const loginTotal = ref(0)
const loginActionFilter = ref('all')

// 操作审计相关
const operationLogs = ref([])
const operationPage = ref(1)
const operationPerPage = ref(10)
const operationTotal = ref(0)
const operationActionFilter = ref('all')
const resourceTypeFilter = ref('all')

// 当前激活的标签页
const activeTab = ref('login')

// 审计日志详情抽屉
const drawerVisible = ref(false)
const currentLog = ref({})

// 控制操作审计详细信息展开/收起
const detailsExpanded = ref(false)
const activeDetailsCollapse = ref(['params']) // 默认展开第一个

// 获取登录审计日志
const fetchLoginLogs = async () => {
  try {
    const res = await axios.get('/auth/audit-logs', {
      params: {
        page: loginPage.value,
        per_page: loginPerPage.value,
        action: loginActionFilter.value
      }
    })
    loginLogs.value = res.data.logs
    loginTotal.value = res.data.total
  } catch (error) {
    console.error(t('audit.getLoginLogsFailed'), error)
  }
}

// 获取操作审计日志
const fetchOperationLogs = async () => {
  try {
    const res = await axios.get('/auth/operation-logs', {
      params: {
        page: operationPage.value,
        per_page: operationPerPage.value,
        action: operationActionFilter.value,
        resource_type: resourceTypeFilter.value
      }
    })
    operationLogs.value = res.data.logs
    operationTotal.value = res.data.total
  } catch (error) {
    console.error(t('audit.getOperationLogsFailed'), error)
  }
}

// 登录审计分页处理
const handleLoginPageChange = (newPage) => {
  loginPage.value = newPage
  fetchLoginLogs()
}

const handleLoginSizeChange = (newSize) => {
  loginPerPage.value = newSize
  loginPage.value = 1
  fetchLoginLogs()
}

const handleLoginFilterChange = () => {
  loginPage.value = 1
  fetchLoginLogs()
}

// 操作审计分页处理
const handleOperationPageChange = (newPage) => {
  operationPage.value = newPage
  fetchOperationLogs()
}

const handleOperationSizeChange = (newSize) => {
  operationPerPage.value = newSize
  operationPage.value = 1
  fetchOperationLogs()
}

const handleOperationFilterChange = () => {
  operationPage.value = 1
  fetchOperationLogs()
}

// 处理登录日志行点击
const handleLoginRowClick = (row) => {
  currentLog.value = row
  drawerVisible.value = true
  // 重置展开状态
  detailsExpanded.value = false
  activeDetailsCollapse.value = ['params']
}

// 处理操作日志行点击
const handleOperationRowClick = (row) => {
  currentLog.value = row
  drawerVisible.value = true
  // 重置展开状态
  detailsExpanded.value = false
  activeDetailsCollapse.value = ['params']
}

// 关闭抽屉
const handleDrawerClose = () => {
  drawerVisible.value = false
  currentLog.value = {}
  // 重置展开状态
  detailsExpanded.value = false
  activeDetailsCollapse.value = ['params']
}

// 格式化时间
const formatTime = (t) => {
  if (!t) return '-'
  const date = new Date(t)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
}

// 格式化用户代理
const formatUserAgent = (userAgent) => {
  if (!userAgent) return '-'
  if (userAgent.includes('Chrome')) return 'Chrome'
  if (userAgent.includes('Firefox')) return 'Firefox'
  if (userAgent.includes('Safari')) return 'Safari'
  if (userAgent.includes('Edge')) return 'Edge'
  return t('audit.otherBrowser')
}

// 格式化详细信息
const formatDetails = (details) => {
  if (!details) return '-'
  if (typeof details === 'string') {
    return details.length > 50 ? details.substring(0, 50) + '...' : details
  }
  const detailsStr = JSON.stringify(details)
  return detailsStr.length > 50 ? detailsStr.substring(0, 50) + '...' : detailsStr
}

// 格式化JSON
const formatJSON = (json) => {
  if (!json) return 'null'
  try {
    return JSON.stringify(json, null, 2)
  } catch (e) {
    return JSON.stringify(json)
  }
}

// 获取资源类型标签
const getResourceTypeLabel = (type) => {
  const labels = {
    'user': t('audit.user'),
    'node': t('audit.node'),
    'storage': t('audit.storage'),
    'task': t('audit.task'),
    'client': t('audit.client')
  }
  return labels[type] || type
}

// 获取资源类型颜色
const getResourceTypeColor = (type) => {
  const colors = {
    'user': 'primary',
    'node': 'success',
    'storage': 'warning',
    'task': 'info',
    'client': 'danger'
  }
  return colors[type] || 'info'
}

// 获取动作标签
const getActionLabel = (action) => {
  const labels = {
    'create': t('audit.create'),
    'update': t('audit.update'),
    'delete': t('audit.delete'),
    'read': t('audit.read')
  }
  return labels[action] || action
}

// 获取动作颜色
const getActionTypeColor = (action) => {
  const colors = {
    'create': 'success',
    'update': 'warning',
    'delete': 'danger',
    'read': 'info'
  }
  return colors[action] || 'info'
}

// 获取客户端类型
const getClientType = (userAgent) => {
  if (!userAgent) return t('audit.unknown')
  if (userAgent.includes('Chrome')) return 'Chrome'
  if (userAgent.includes('Firefox')) return 'Firefox'
  if (userAgent.includes('Safari')) return 'Safari'
  if (userAgent.includes('Edge')) return 'Edge'
  return t('audit.otherBrowser')
}

// 获取操作系统信息
const getOSInfo = (userAgent) => {
  if (!userAgent) return t('audit.unknown')
  if (userAgent.includes('Windows')) return 'Windows'
  if (userAgent.includes('Macintosh')) return 'Mac OS'
  if (userAgent.includes('Linux')) return 'Linux'
  if (userAgent.includes('Android')) return 'Android'
  if (userAgent.includes('iOS')) return 'iOS'
  return t('audit.otherOS')
}

// 切换操作审计详细信息展开/收起
const toggleDetailsExpanded = () => {
  detailsExpanded.value = !detailsExpanded.value
  if (detailsExpanded.value) {
    activeDetailsCollapse.value = ['params'] // 默认展开第一个
  } else {
    activeDetailsCollapse.value = [] // 收起所有
  }
}

// 获取操作审计详细信息摘要文本
const getSummaryText = (json) => {
  if (!json) return t('audit.noContent')
  if (typeof json === 'string') {
    return json.length > 50 ? json.substring(0, 50) + '...' : json
  }
  const keys = Object.keys(json)
  if (keys.length === 0) return t('audit.noContent')
  return `${keys.length} ${t('audit.items')}`
}

// 判断详细信息是否有实际内容
const hasDetailsContent = (details) => {
  if (!details) return false

  // 检查是否有我们关心的字段
  const relevantFields = [
    'ip', 'user_agent', 'path', 'method', 'status_code', 'response_time',
    'msg', 'username', 'name', 'ip_address', 'status', 'error'
  ]

  return relevantFields.some(field => details[field] !== undefined && details[field] !== null && details[field] !== '')
}

// 判断操作审计详细信息是否有实际内容
const hasOperationDetailsContent = (details) => {
  if (!details) return false

  // 检查是否有我们关心的字段
  const relevantFields = [
    'params', 'headers', 'response', 'error'
  ]

  return relevantFields.some(field => details[field] !== undefined && details[field] !== null && details[field] !== '')
}

onMounted(() => {
  fetchLoginLogs()
  fetchOperationLogs()
})
</script>

<style scoped>
.audit-logs-page {
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.page-header h2 {
  margin: 0;
}

.tab-header {
  margin-bottom: 20px;
}

.header-actions {
  display: flex;
  gap: 16px;
  align-items: center;
}

.filter-select {
  width: 150px;
}

.page-content {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.data-card {
  background: var(--card-bg);
  border-radius: 12px;
  box-shadow: var(--card-shadow);
  border: 1px solid var(--border-color);
  overflow: hidden;
  height: 100%;
  display: flex;
  flex-direction: column;
  padding: 20px;
}

.card-header {
  padding-bottom: 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 600;
  color: var(--text-color);
}

.title-icon {
  color: var(--primary-color);
  font-size: 18px;
}

.card-stats {
  color: var(--text-secondary);
  font-size: 14px;
}

.table-container {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.audit-table {
  flex: 1;
}

.user-info {
  display: flex;
  justify-content: center;
  align-items: center;
}

.time-info {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 6px;
}

.time-icon {
  color: var(--text-secondary);
  font-size: 14px;
}

.user-agent-info {
  padding: 0 8px;
}

.user-agent-text {
  color: var(--text-color);
  font-size: 13px;
}

.details-info {
  padding: 0 8px;
}

.details-text {
  color: var(--text-color);
  font-size: 13px;
}

.pagination-wrapper {
  padding: 20px 24px;
  border-top: 1px solid var(--border-color);
  background: var(--card-header-bg);
  display: flex;
  justify-content: flex-end;
}

:deep(.el-table) {
  background: transparent;
  color: var(--text-color);
}

:deep(.el-table tr) {
  background: transparent;
}

:deep(.el-table--striped .el-table__body tr.el-table__row--striped td) {
  background: var(--table-stripe-bg);
}

:deep(.el-table td.el-table__cell) {
  border-bottom: 1px solid var(--border-lighter);
  padding: 12px 0;
}

:deep(.el-table th.el-table__cell) {
  background: var(--table-header-bg) !important;
  color: var(--text-color) !important;
  border-bottom: 1px solid var(--border-color);
  font-weight: 600;
}

:deep(.el-pagination) {
  color: var(--text-color);
}

:deep(.el-pagination .el-pager li) {
  background: var(--card-bg);
  color: var(--text-color);
  border: 1px solid var(--border-color);
}

:deep(.el-pagination .el-pager li:hover) {
  color: var(--primary-color);
}

:deep(.el-pagination .el-pager li.is-active) {
  background: var(--primary-color);
  color: #fff;
}

:deep(.el-select .el-input .el-input__wrapper) {
  background: var(--input-bg);
  border-color: var(--border-color);
}

:deep(.el-tag) {
  border-radius: 6px;
}

/* 抽屉样式 */
.audit-drawer {
  height: 100vh;
}

.audit-drawer :deep(.el-drawer__body) {
  padding: 0;
  height: calc(100vh - 60px);
  overflow: hidden;
}

.detail-content {
  display: flex;
  flex-direction: column;
  gap: 20px;
  padding: 20px;
  overflow-y: auto;
  overflow-x: hidden;
}

.info-card {
  background: var(--card-bg);
  border-radius: 12px;
  box-shadow: var(--card-shadow);
  border: 1px solid var(--border-color);
  margin-bottom: 0;
}

.info-card .el-card__header {
  background: var(--card-header-bg);
  border-bottom: 1px solid var(--border-color);
  padding: 15px 20px;
}

.info-card .el-card__body {
  padding: 20px;
}

.info-card .el-card__header .el-card__title {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-color);
}

.json-detail pre {
  background: var(--code-bg, #f5f5f5);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  padding: 10px;
  overflow-x: auto;
  font-size: 13px;
  color: var(--text-color);
  white-space: pre-wrap;
  word-break: break-all;
  max-height: 200px;
  overflow-y: auto;
}

.error-detail .el-tag {
  background: var(--danger-bg, #fef0f0);
  color: var(--danger-color, #f56c6c);
}

.user-agent-detail {
  display: flex;
  align-items: center;
  gap: 8px;
}

.user-agent-detail span {
  word-break: break-all;
  line-height: 1.4;
}

.user-agent-detail .el-tag {
  background: var(--info-bg, #f0f9ff);
  color: var(--info-color, #409eff);
}

/* 表格行点击样式 */
:deep(.el-table__row) {
  cursor: pointer;
  transition: all 0.3s ease;
}

:deep(.el-table__row:hover) {
  background-color: var(--el-color-primary-light-9);
}

/* 卡片头部样式 */
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-header span {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-color);
}

/* 抽屉滚动条样式 */
.detail-content::-webkit-scrollbar {
  width: 6px;
}

.detail-content::-webkit-scrollbar-track {
  background: var(--border-lighter);
  border-radius: 3px;
}

.detail-content::-webkit-scrollbar-thumb {
  background: var(--border-color);
  border-radius: 3px;
}

.detail-content::-webkit-scrollbar-thumb:hover {
  background: var(--text-tertiary);
}

/* JSON详情滚动条样式 */
.json-detail pre::-webkit-scrollbar {
  width: 4px;
  height: 4px;
}

.json-detail pre::-webkit-scrollbar-track {
  background: var(--border-lighter);
  border-radius: 2px;
}

.json-detail pre::-webkit-scrollbar-thumb {
  background: var(--border-color);
  border-radius: 2px;
}

.json-detail pre::-webkit-scrollbar-thumb:hover {
  background: var(--text-tertiary);
}

/* 操作审计详细信息样式 */
.details-summary {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.summary-item {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 8px 12px;
  background: var(--bg-secondary);
  border-radius: 6px;
  border: 1px solid var(--border-lighter);
}

.summary-label {
  font-weight: 500;
  color: var(--text-secondary);
  min-width: 80px;
  flex-shrink: 0;
}

.summary-value {
  color: var(--text-color);
  flex: 1;
  word-break: break-all;
  line-height: 1.4;
}

.summary-value.error-text {
  color: var(--danger-color);
}

.details-expanded {
  margin-top: 16px;
}

.details-expanded :deep(.el-collapse) {
  border: none;
}

.details-expanded :deep(.el-collapse-item__header) {
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  padding: 10px;
  border-radius: 6px;
  margin-bottom: 8px;
  font-weight: 500;
  color: var(--text-color);
}

.details-expanded :deep(.el-collapse-item__content) {
  padding: 0;
}

.details-expanded :deep(.el-collapse-item__wrap) {
  border: none;
  background: transparent;
}

/* 卡片头部按钮样式 */
.card-header .el-button {
  font-size: 14px;
  padding: 4px 8px;
}

.card-header .el-icon {
  font-size: 12px;
}

.original-card {
  border: 2px dashed var(--el-color-warning);
  background: var(--el-color-warning-light-9);
}

.original-content {
  font-size: 12px;
  line-height: 1.4;
}

.original-content pre {
  background: var(--code-bg);
  border: 1px solid var(--border-color);
  border-radius: 4px;
  padding: 8px;
  overflow-x: auto;
  font-size: 11px;
  max-height: 200px;
  overflow-y: auto;
}
</style>