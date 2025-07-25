<template>
  <div class="audit-logs-page">
    <div class="page-header">
      <h2>登录审计</h2>
      <div class="header-actions">
        <el-select 
          v-model="actionFilter" 
          placeholder="选择操作类型" 
          class="filter-select"
          @change="handleFilterChange"
        >
          <el-option label="全部操作" value="all" />
          <el-option label="登录记录" value="login" />
          <el-option label="退出记录" value="logout" />
        </el-select>
      </div>
    </div>

    <div class="page-content">
      <div class="data-card">
        <div class="card-header">
          <div class="card-title">
            <el-icon class="title-icon"><DataAnalysis /></el-icon>
            <span>审计日志</span>
          </div>
          <div class="card-stats">
            <span class="stats-text">共 {{ total }} 条记录</span>
          </div>
        </div>

        <div class="table-container">
          <el-table 
            :data="logs" 
            class="audit-table"
            :header-cell-style="{ background: 'var(--table-header-bg)', color: 'var(--text-color)' }"
            stripe
          >
            <el-table-column prop="username" label="用户" width="120" align="center">
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
            
            <el-table-column label="操作时间" width="180" align="center">
              <template #default="scope">
                <div class="time-info">
                  <el-icon class="time-icon"><Clock /></el-icon>
                  <span>{{ formatTime(scope.row.details.login_time || scope.row.details.logout_time) }}</span>
                </div>
              </template>
            </el-table-column>
            
            <el-table-column prop="details.ip" label="IP地址" width="140" align="center">
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
              v-model:current-page="page"
              :page-size="perPage"
              :total="total"
              layout="total, sizes, prev, pager, next, jumper"
              :page-sizes="[10, 20, 50, 100]"
              @current-change="handlePageChange"
              @size-change="handleSizeChange"
              background
            />
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'
import { DataAnalysis, Clock } from '@element-plus/icons-vue'

const logs = ref([])
const page = ref(1)
const perPage = ref(20)
const total = ref(0)
const actionFilter = ref('all')

const fetchLogs = async () => {
  try {
    const res = await axios.get('/api/auth/audit-logs', {
      params: { 
        page: page.value, 
        per_page: perPage.value,
        action: actionFilter.value
      }
    })
    logs.value = res.data.logs
    total.value = res.data.total
  } catch (error) {
    console.error('获取审计日志失败:', error)
  }
}

const handlePageChange = (newPage) => {
  page.value = newPage
  fetchLogs()
}

const handleSizeChange = (newSize) => {
  perPage.value = newSize
  page.value = 1
  fetchLogs()
}

const handleFilterChange = () => {
  page.value = 1
  fetchLogs()
}

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

const formatUserAgent = (userAgent) => {
  if (!userAgent) return '-'
  // 简化显示，提取浏览器和操作系统信息
  if (userAgent.includes('Chrome')) return 'Chrome'
  if (userAgent.includes('Firefox')) return 'Firefox'
  if (userAgent.includes('Safari')) return 'Safari'
  if (userAgent.includes('Edge')) return 'Edge'
  return '其他浏览器'
}

onMounted(fetchLogs)
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
  align-items: center;
}

.time-info {
  display: flex;
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