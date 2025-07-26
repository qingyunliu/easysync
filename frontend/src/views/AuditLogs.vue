<template>
  <div class="audit-logs-page">
    <div class="page-header">
      <h2>审计日志</h2>
    </div>

    <div class="page-content">
      <el-tabs v-model="activeTab">
        <!-- 登录/登出审计 -->
        <el-tab-pane label="登录审计" name="login">
          <div class="tab-header">
            <div class="header-actions">
              <el-select 
                v-model="loginActionFilter" 
                placeholder="选择操作类型" 
                class="filter-select"
                @change="handleLoginFilterChange"
              >
                <el-option label="全部操作" value="all" />
                <el-option label="登录记录" value="login" />
                <el-option label="退出记录" value="logout" />
              </el-select>
            </div>
          </div>

          <div class="data-card">
            <div class="card-header">
              <div class="card-title">
                <el-icon class="title-icon"><DataAnalysis /></el-icon>
                <span>登录/登出审计日志</span>
              </div>
              <div class="card-stats">
                <span class="stats-text">共 {{ loginTotal }} 条记录</span>
              </div>
            </div>

            <div class="table-container">
              <el-table 
                :data="loginLogs" 
                class="audit-table"
                :header-cell-style="{ background: 'var(--table-header-bg)', color: 'var(--text-color)' }"
                stripe
              >
                <el-table-column prop="id" label="ID" width="330" align="center"/>
                <el-table-column prop="username" label="用户" width="160" align="center">
                  <template #default="scope">
                    <div class="user-info">
                      <el-avatar :size="28" style="margin-right: 8px">
                        {{ scope.row.username?.charAt(0)?.toUpperCase() }}
                      </el-avatar>
                      <span>{{ scope.row.username }}</span>
                    </div>
                  </template>
                </el-table-column>
                
                <el-table-column prop="action" label="操作类型" width="120" align="center">
                  <template #default="scope">
                    <el-tag 
                      :type="scope.row.action === 'login' ? 'success' : 'warning'"
                      :icon="scope.row.action === 'login' ? 'CircleCheck' : 'CircleClose'"
                      effect="light"
                    >
                      {{ scope.row.action === 'login' ? '登录' : '退出' }}
                    </el-tag>
                  </template>
                </el-table-column>
                
                <el-table-column label="操作时间" width="220" align="center">
                  <template #default="scope">
                    <div class="time-info">
                      <el-icon class="time-icon"><Clock /></el-icon>
                      <span>{{ formatTime(scope.row.details.login_time || scope.row.details.logout_time) }}</span>
                    </div>
                  </template>
                </el-table-column>

                <el-table-column prop="result" label="结果" width="100" align="center">
                  <template #default="scope">
                    <el-tag 
                      :type="scope.row.result === 'success' ? 'success' : 'danger'"
                      effect="light"
                      size="small"
                    >
                      {{ scope.row.result === 'success' ? '成功' : '失败' }}
                    </el-tag>
                  </template>
                </el-table-column>
                
                <el-table-column prop="details.ip" label="IP地址" width="180" align="center">
                  <template #default="scope">
                    <el-tag type="info" effect="plain" size="small">
                      {{ scope.row.details.ip }}
                    </el-tag>
                  </template>
                </el-table-column>
                
                <el-table-column prop="details.user_agent" label="客户端信息" min-width="200">
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
                <el-pagination
                  v-model:current-page="loginPage"
                  :page-size="loginPerPage"
                  :total="loginTotal"
                  layout="total, sizes, prev, pager, next, jumper"
                  :page-sizes="[10, 20, 50, 100]"
                  @current-change="handleLoginPageChange"
                  @size-change="handleLoginSizeChange"
                  background
                />
              </div>
            </div>
          </div>
        </el-tab-pane>

        <!-- 常规操作审计 -->
        <el-tab-pane label="操作审计" name="operation">
          <div class="tab-header">
            <div class="header-actions">
              <el-select 
                v-model="operationActionFilter" 
                placeholder="选择操作类型" 
                class="filter-select"
                @change="handleOperationFilterChange"
              >
                <el-option label="全部操作" value="all" />
                <el-option label="创建" value="create" />
                <el-option label="更新" value="update" />
                <el-option label="删除" value="delete" />
                <el-option label="查询" value="read" />
              </el-select>
              <el-select 
                v-model="resourceTypeFilter" 
                placeholder="选择资源类型" 
                class="filter-select"
                @change="handleOperationFilterChange"
              >
                <el-option label="全部资源" value="all" />
                <el-option label="用户" value="user" />
                <el-option label="节点" value="node" />
                <el-option label="存储" value="storage" />
                <el-option label="任务" value="task" />
                <el-option label="客户端" value="client" />
              </el-select>
            </div>
          </div>

          <div class="data-card">
            <div class="card-header">
              <div class="card-title">
                <el-icon class="title-icon"><Operation /></el-icon>
                <span>操作审计日志</span>
              </div>
              <div class="card-stats">
                <span class="stats-text">共 {{ operationTotal }} 条记录</span>
              </div>
            </div>

            <div class="table-container">
              <el-table 
                :data="operationLogs" 
                class="audit-table"
                :header-cell-style="{ background: 'var(--table-header-bg)', color: 'var(--text-color)' }"
                stripe
              >
                <el-table-column prop="id" label="ID" width="330" align="center"/>
                
                <el-table-column prop="username" label="用户" width="120" align="center">
                  <template #default="scope">
                    <div class="user-info">
                      <el-avatar :size="24" style="margin-right: 6px">
                        {{ scope.row.username?.charAt(0)?.toUpperCase() }}
                      </el-avatar>
                      <span>{{ scope.row.username }}</span>
                    </div>
                  </template>
                </el-table-column>
                
                <el-table-column prop="resource_name" label="资源名称" width="150" align="center">
                  <template #default="scope">
                    <span>{{ scope.row.resource_name || '-' }}</span>
                  </template>
                </el-table-column>
                
                <el-table-column prop="resource_type" label="资源类型" width="100" align="center">
                  <template #default="scope">
                    <el-tag 
                      :type="getResourceTypeColor(scope.row.resource_type)"
                      effect="light"
                      size="small"
                    >
                      {{ getResourceTypeLabel(scope.row.resource_type) }}
                    </el-tag>
                  </template>
                </el-table-column>
                
                <el-table-column prop="action" label="操作类型" width="180" align="center">
                  <template #default="scope">
                    <el-tag 
                      :type="getActionTypeColor(scope.row.action)"
                      effect="light"
                      size="small"
                    >
                      {{ getActionLabel(scope.row.action) }}
                    </el-tag>
                  </template>
                </el-table-column>
                
                <el-table-column label="操作时间" width="180" align="center">
                  <template #default="scope">
                    <div class="time-info">
                      <el-icon class="time-icon"><Clock /></el-icon>
                      <span>{{ formatTime(scope.row.created_at) }}</span>
                    </div>
                  </template>
                </el-table-column>
                
                <el-table-column prop="result" label="结果" width="100" align="center">
                  <template #default="scope">
                    <el-tag 
                      :type="scope.row.result === 'success' ? 'success' : 'danger'"
                      effect="light"
                      size="small"
                    >
                      {{ scope.row.result === 'success' ? '成功' : '失败' }}
                    </el-tag>
                  </template>
                </el-table-column>
                
                <el-table-column prop="details" label="详细信息" min-width="200">
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
                <el-pagination
                  v-model:current-page="operationPage"
                  :page-size="operationPerPage"
                  :total="operationTotal"
                  layout="total, sizes, prev, pager, next, jumper"
                  :page-sizes="[10, 20, 50, 100]"
                  @current-change="handleOperationPageChange"
                  @size-change="handleOperationSizeChange"
                  background
                />
              </div>
            </div>
          </div>
        </el-tab-pane>
      </el-tabs>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'
import { DataAnalysis, Clock, Operation } from '@element-plus/icons-vue'

// 登录审计相关
const loginLogs = ref([])
const loginPage = ref(1)
const loginPerPage = ref(20)
const loginTotal = ref(0)
const loginActionFilter = ref('all')

// 操作审计相关
const operationLogs = ref([])
const operationPage = ref(1)
const operationPerPage = ref(20)
const operationTotal = ref(0)
const operationActionFilter = ref('all')
const resourceTypeFilter = ref('all')

// 当前激活的标签页
const activeTab = ref('login')

// 获取登录审计日志
const fetchLoginLogs = async () => {
  try {
    const res = await axios.get('/api/auth/audit-logs', {
      params: { 
        page: loginPage.value, 
        per_page: loginPerPage.value,
        action: loginActionFilter.value
      }
    })
    loginLogs.value = res.data.logs
    loginTotal.value = res.data.total
  } catch (error) {
    console.error('获取登录审计日志失败:', error)
  }
}

// 获取操作审计日志
const fetchOperationLogs = async () => {
  try {
    const res = await axios.get('/api/auth/operation-logs', {
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
    console.error('获取操作审计日志失败:', error)
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
  return '其他浏览器'
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

// 获取资源类型标签
const getResourceTypeLabel = (type) => {
  const labels = {
    'user': '用户',
    'node': '节点',
    'storage': '存储',
    'task': '任务',
    'client': '客户端'
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
    'create': '创建',
    'update': '更新',
    'delete': '删除',
    'read': '查询'
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
</style> 